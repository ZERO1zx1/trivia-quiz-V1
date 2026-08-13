"""Create a transactionally consistent, non-destructive SQLite backup."""
import argparse
import hashlib
import sqlite3
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    destination = args.destination.resolve()
    if source == destination:
        raise SystemExit('Backup destination must differ from source')
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise SystemExit(f'Refusing to overwrite existing backup: {destination}')

    with sqlite3.connect(f'file:{source.as_posix()}?mode=ro', uri=True) as src:
        with sqlite3.connect(destination) as dst:
            src.backup(dst)
            issues = dst.execute('PRAGMA integrity_check').fetchall()
            if issues != [('ok',)]:
                raise SystemExit(f'Backup integrity check failed: {issues}')
    print(f'Backup: {destination}')
    print(f'SHA256: {sha256(destination)}')


if __name__ == '__main__':
    main()
