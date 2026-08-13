"""Render Alembic SQL into connector-safe, statement-aligned chunks."""
import argparse
import hashlib
import os
import subprocess
import sys


def statements(sql):
    items = []
    buffer = []
    index = 0
    quote = None
    dollar = None
    line_comment = False
    block_comment = False
    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ''
        if line_comment:
            buffer.append(char)
            if char == '\n':
                line_comment = False
            index += 1
            continue
        if block_comment:
            buffer.append(char)
            if char == '*' and next_char == '/':
                buffer.append(next_char)
                block_comment = False
                index += 2
            else:
                index += 1
            continue
        if dollar:
            if sql.startswith(dollar, index):
                buffer.append(dollar)
                index += len(dollar)
                dollar = None
            else:
                buffer.append(char)
                index += 1
            continue
        if quote:
            buffer.append(char)
            if char == quote:
                if next_char == quote:
                    buffer.append(next_char)
                    index += 2
                    continue
                quote = None
            index += 1
            continue
        if char == '-' and next_char == '-':
            buffer.extend((char, next_char))
            line_comment = True
            index += 2
            continue
        if char == '/' and next_char == '*':
            buffer.extend((char, next_char))
            block_comment = True
            index += 2
            continue
        if char in ("'", '"'):
            quote = char
            buffer.append(char)
            index += 1
            continue
        if char == '$':
            end = sql.find('$', index + 1)
            if end >= 0:
                tag = sql[index:end + 1]
                if tag[1:-1].replace('_', 'a').isalnum() or tag == '$$':
                    dollar = tag
                    buffer.append(tag)
                    index = end + 1
                    continue
        buffer.append(char)
        if char == ';':
            statement = ''.join(buffer).strip()
            if statement and statement.upper() not in ('BEGIN;', 'COMMIT;'):
                items.append(statement)
            buffer = []
        index += 1
    tail = ''.join(buffer).strip()
    if tail:
        items.append(tail)
    return items


def chunks(items, maximum):
    result = []
    current = []
    size = 0
    for statement in items:
        length = len(statement) + 2
        if length > maximum:
            raise SystemExit(
                f'One SQL statement exceeds chunk limit ({length} > {maximum})')
        if current and size + length > maximum:
            result.append('\n\n'.join(current))
            current = []
            size = 0
        current.append(statement)
        size += length
    if current:
        result.append('\n\n'.join(current))
    return result


def render():
    env = dict(os.environ)
    env.update({
        'FLASK_APP': 'run.py',
        'AUTO_INIT_DATABASE': '0',
        'DATABASE_URL': 'postgresql://user:pass@localhost/triviaverse',
    })
    result = subprocess.run(
        [sys.executable, '-m', 'flask', 'db', 'upgrade', '--sql'],
        check=True, capture_output=True, text=True, env=env,
    )
    if 'truncated' in result.stdout:
        raise SystemExit('Alembic output was unexpectedly truncated')
    # Alembic escapes percent signs for ConfigParser while generating offline
    # SQL. The connector executes SQL directly, so restore PostgreSQL format
    # placeholders such as %I and %L.
    return result.stdout.replace('%%', '%')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--chunk', type=int)
    parser.add_argument('--max-chars', type=int, default=24000)
    args = parser.parse_args()
    rendered = chunks(statements(render()), args.max_chars)
    if args.chunk is None:
        for index, value in enumerate(rendered, start=1):
            digest = hashlib.sha256(value.encode()).hexdigest()[:12]
            print(f'{index}\t{len(value)}\t{digest}')
        return
    if args.chunk < 1 or args.chunk > len(rendered):
        raise SystemExit(f'Chunk must be between 1 and {len(rendered)}')
    print(rendered[args.chunk - 1])


if __name__ == '__main__':
    main()
