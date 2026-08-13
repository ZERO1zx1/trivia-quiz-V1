"""Render a deterministic, self-verifying SQL data import from SQLite."""
import argparse
import hashlib
import json
import sqlite3
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy import MetaData, create_engine, inspect


def sql_literal(value, declared_type):
    if value is None:
        return 'NULL'
    kind = (declared_type or '').upper()
    if 'BOOL' in kind:
        return 'TRUE' if bool(value) else 'FALSE'
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, bytes):
        return "decode('%s', 'hex')" % value.hex()
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def canonical(value, declared_type):
    if value is None:
        return None
    kind = (declared_type or '').upper()
    if 'BOOL' in kind:
        return bool(value)
    if isinstance(value, datetime) or 'DATETIME' in kind or 'TIMESTAMP' in kind:
        parsed = value if isinstance(value, datetime) else datetime.fromisoformat(
            str(value).replace('Z', '+00:00'))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        rendered = parsed.astimezone(timezone.utc).isoformat()
        # PostgreSQL's JSON encoder trims insignificant fractional-second
        # zeros (e.g. .767700 -> .7677).
        if '.' in rendered:
            prefix, remainder = rendered.split('.', 1)
            fraction, offset = remainder.split('+', 1)
            fraction = fraction.rstrip('0')
            rendered = prefix + (f'.{fraction}' if fraction else '') \
                + '+' + offset
        return rendered
    if isinstance(value, date) or kind == 'DATE':
        return value.isoformat() if isinstance(value, date) else str(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, bytes):
        return '\\x' + value.hex()
    return value


def pg_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(', ', ': '))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    engine = create_engine(f'sqlite:///{source.as_posix()}')
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)

    output = ['SET search_path = app, public;']
    manifest = []
    with engine.connect() as connection:
        for table in metadata.sorted_tables:
            columns_info = inspector.get_columns(table.name)
            declared = {
                column['name']: str(column['type'])
                for column in columns_info
            }
            columns = [column.name for column in table.columns]
            pk = inspector.get_pk_constraint(table.name).get(
                'constrained_columns', [])
            statement = table.select()
            if pk:
                statement = statement.order_by(
                    *(table.c[column] for column in pk))
            rows = [dict(row._mapping)
                    for row in connection.execute(statement)]
            if not rows:
                continue

            quoted_columns = ', '.join(f'"{column}"' for column in columns)
            values = []
            canonical_rows = []
            for row in rows:
                values.append('(' + ', '.join(
                    sql_literal(row[column], declared[column])
                    for column in columns) + ')')
                canonical_rows.append([
                    canonical(row[column], declared[column])
                    for column in columns
                ])
            output.append(
                f'INSERT INTO app."{table.name}" ({quoted_columns}) VALUES\n'
                + ',\n'.join(values) + ';')

            expected = hashlib.md5(''.join(
                pg_json(row) for row in canonical_rows
            ).encode('utf-8')).hexdigest()
            order = ', '.join(f'"{column}"' for column in pk) or '1'
            expression = ', '.join(f'"{column}"' for column in columns)
            manifest.append((table.name, len(rows), expected,
                             expression, order))

    output.append("""
DO $$
DECLARE seq record;
DECLARE maximum bigint;
BEGIN
  FOR seq IN
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'app' AND column_default LIKE 'nextval(%'
  LOOP
    EXECUTE format('SELECT max(%I) FROM app.%I',
      seq.column_name, seq.table_name) INTO maximum;
    EXECUTE format(
      'SELECT setval(pg_get_serial_sequence(%L, %L), %s, %L)',
      'app.' || seq.table_name, seq.column_name,
      greatest(coalesce(maximum, 1), 1), maximum IS NOT NULL);
  END LOOP;
END $$;
""".strip())

    for table, count, expected, expression, order in manifest:
        output.append(f"""
DO $$
DECLARE actual_count bigint;
DECLARE actual_checksum text;
BEGIN
  SELECT count(*), md5(coalesce(string_agg(
    jsonb_build_array({expression})::text, '' ORDER BY {order}), ''))
  INTO actual_count, actual_checksum
  FROM app."{table}";
  IF actual_count <> {count} OR actual_checksum <> '{expected}' THEN
    RAISE EXCEPTION 'Import verification failed for {table}: count %, checksum %',
      actual_count, actual_checksum;
  END IF;
END $$;
""".strip())

    print('\n\n'.join(output))


if __name__ == '__main__':
    main()
