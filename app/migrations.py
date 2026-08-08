"""Idempotent SQL migrations runner (FIX-022).

Runs plain-SQL migration files from the project `migrations/` directory
against PostgreSQL deployments that predate the updated schema. Every
statement inside a migration file is wrapped in an idempotent `DO $$ ...
END $$;` block, so the file can be applied repeatedly without side effects.

SQLite (development/testing) does not need this: `db.create_all()` already
produces the current schema.

Enabled by setting ``RUN_DB_MIGRATIONS=1`` at application startup.
"""
import glob
import os

from app.extensions import db


MIGRATIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'migrations',
)


def run_sql_migrations(app):
    """Apply every ``*.sql`` migration file once per deployment.

    Applies files in filename order. A marker row is kept in
    ``_schema_migrations`` so each file is only applied once. Failures abort
    further migrations and are logged loudly (never silently swallowed).
    """
    marker_table = '_schema_migrations'
    marker_exists = db.engine.dialect.has_table(db.engine, marker_table)
    if not marker_exists:
        db.session.execute(db.text(
            f'CREATE TABLE IF NOT EXISTS {marker_table} '
            '(filename VARCHAR(255) PRIMARY KEY, applied_at TIMESTAMP)'
        ))
        db.session.commit()

    files = sorted(glob.glob(os.path.join(MIGRATIONS_DIR, '*.sql')))
    applied = {
        row[0] for row in
        db.session.execute(
            db.text(f'SELECT filename FROM {marker_table}')).fetchall()
    }

    for path in files:
        filename = os.path.basename(path)
        if filename in applied:
            continue
        with open(path, 'r', encoding='utf-8') as handle:
            sql = handle.read()
        app.logger.info('Applying SQL migration: %s', filename)
        try:
            for statement in _split_statements(sql):
                db.session.execute(db.text(statement))
            db.session.commit()
        except Exception as exc:  # pragma: no cover - logged, then raised
            db.session.rollback()
            app.logger.error('Migration %s failed: %s', filename, exc)
            raise
        db.session.execute(
            db.text(
                f'INSERT INTO {marker_table} (filename, applied_at) '
                'VALUES (:fn, now())'
            ), {'fn': filename})
        db.session.commit()


def _split_statements(sql):
    """Split a migration file into non-empty statement blocks.

    Idempotent PostgreSQL ``DO $$ ... END $$;`` blocks contain internal
    semicolons, so we split on the token ``;\\n`` followed by a non-space
    character start — a simple conservative approach: split on lines that
    are exactly a semicolon.
    """
    buffer = []
    for line in sql.splitlines():
        buffer.append(line)
        if line.strip() == ';':
            yield '\n'.join(buffer).strip()
            buffer = []
    remainder = '\n'.join(buffer).strip()
    if remainder:
        yield remainder
