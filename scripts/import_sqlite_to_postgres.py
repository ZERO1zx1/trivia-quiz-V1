"""Lossless SQLite -> private-schema PostgreSQL import and verification."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import MetaData, create_engine, inspect, select, text


def canonical(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec='microseconds')
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray, memoryview)):
        return base64.b64encode(bytes(value)).decode('ascii')
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    return value


def row_digest(rows, columns):
    digest = hashlib.sha256()
    normalized = []
    for row in rows:
        normalized.append(json.dumps(
            [canonical(row[column]) for column in columns],
            ensure_ascii=False, separators=(',', ':'), sort_keys=False,
        ))
    for value in sorted(normalized):
        digest.update(value.encode('utf-8'))
        digest.update(b'\n')
    return digest.hexdigest()


def read_rows(connection, table, pk_names):
    columns = [column.name for column in table.columns]
    ordering = [table.c[name] for name in pk_names if name in table.c]
    statement = select(table)
    if ordering:
        statement = statement.order_by(*ordering)
    return [dict(row._mapping) for row in connection.execute(statement)], columns


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--database-url', default=os.getenv('MIGRATION_DATABASE_URL'))
    parser.add_argument('--schema', default='app')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit('MIGRATION_DATABASE_URL or --database-url is required')
    if args.schema != 'app':
        raise SystemExit('Only the private app schema is supported')

    source_path = args.source.resolve(strict=True)
    source_engine = create_engine(
        f'sqlite:///{source_path.as_posix()}',
        connect_args={'check_same_thread': False},
    )
    target_engine = create_engine(
        args.database_url, pool_pre_ping=True,
        connect_args={'sslmode': 'require', 'options': '-c timezone=UTC'},
    )
    source_meta = MetaData()
    target_meta = MetaData(schema=args.schema)

    report = {'source': str(source_path), 'schema': args.schema, 'tables': {}}
    with source_engine.connect() as source, target_engine.begin() as target:
        source_issues = source.exec_driver_sql('PRAGMA foreign_key_check').all()
        if source_issues:
            raise SystemExit(f'Source has foreign key errors: {source_issues}')
        source_meta.reflect(bind=source)
        target_meta.reflect(bind=target, schema=args.schema)

        source_names = set(source_meta.tables)
        target_by_name = {
            table.name: table for table in target_meta.tables.values()
        }
        missing = sorted(name for name in source_names
                         if name not in target_by_name)
        if missing:
            raise SystemExit(f'Target schema is missing source tables: {missing}')

        # Reflected target metadata supplies FK dependency order.
        for target_table in target_meta.sorted_tables:
            name = target_table.name
            if name not in source_meta.tables:
                continue
            source_table = source_meta.tables[name]
            target_count = target.execute(
                select(text('count(*)')).select_from(target_table)).scalar_one()
            if target_count:
                raise SystemExit(
                    f'Target table {name} is not empty ({target_count} rows)')
            pk_names = [column.name for column
                        in inspect(source_engine).get_pk_constraint(name)
                        .get('constrained_columns', [])]
            rows, source_columns = read_rows(source, source_table, pk_names)
            common = [column for column in source_columns
                      if column in target_table.c]
            payload = [{column: row[column] for column in common}
                       for row in rows]
            if payload:
                target.execute(target_table.insert(), payload)

        # Align every integer identity/serial sequence after preserving IDs.
        target.execute(text("""
        DO $$
        DECLARE seq record;
        DECLARE maximum bigint;
        BEGIN
          FOR seq IN
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'app'
              AND column_default LIKE 'nextval(%'
          LOOP
            EXECUTE format('SELECT max(%I) FROM %I.%I',
              seq.column_name, 'app', seq.table_name) INTO maximum;
            EXECUTE format(
              'SELECT setval(pg_get_serial_sequence(%L, %L), %s, %L)',
              'app.' || seq.table_name,
              seq.column_name,
              greatest(coalesce(maximum, 1), 1),
              maximum IS NOT NULL
            );
          END LOOP;
        END $$;
        """))
        target.execute(text('SET CONSTRAINTS ALL IMMEDIATE'))

    # Verify in a fresh transaction after the import commit.
    with source_engine.connect() as source, target_engine.connect() as target:
        target_meta = MetaData(schema=args.schema)
        target_meta.reflect(bind=target, schema=args.schema)
        for name, source_table in source_meta.tables.items():
            target_table = next(
                table for table in target_meta.tables.values()
                if table.name == name)
            pk_names = [column.name for column
                        in inspect(source_engine).get_pk_constraint(name)
                        .get('constrained_columns', [])]
            source_rows, columns = read_rows(source, source_table, pk_names)
            target_rows, _ = read_rows(target, target_table, pk_names)
            common = [column for column in columns if column in target_table.c]
            source_checksum = row_digest(source_rows, common)
            target_checksum = row_digest(target_rows, common)
            source_pk = row_digest(source_rows, pk_names) if pk_names else None
            target_pk = row_digest(target_rows, pk_names) if pk_names else None
            verified = (len(source_rows) == len(target_rows)
                        and source_checksum == target_checksum
                        and source_pk == target_pk)
            report['tables'][name] = {
                'source_rows': len(source_rows),
                'target_rows': len(target_rows),
                'primary_key_checksum': source_pk,
                'row_checksum': source_checksum,
                'verified': verified,
            }
            if not verified:
                raise SystemExit(f'Verification failed for table {name}')

        invalid_fk = target.execute(text("""
          SELECT conrelid::regclass::text, conname
          FROM pg_constraint
          WHERE contype = 'f'
            AND connamespace = (SELECT oid FROM pg_namespace
                                WHERE nspname = :schema)
            AND NOT convalidated
        """), {'schema': args.schema}).all()
        if invalid_fk:
            raise SystemExit(f'Unvalidated target foreign keys: {invalid_fk}')
        report['verified'] = all(
            table['verified'] for table in report['tables'].values())

    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        if args.report.exists():
            raise SystemExit(f'Refusing to overwrite report: {args.report}')
        args.report.write_text(rendered + '\n', encoding='utf-8')
    print(rendered)


if __name__ == '__main__':
    main()
