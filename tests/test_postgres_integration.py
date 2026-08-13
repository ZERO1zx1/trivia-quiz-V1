"""Runs as a dedicated CI step against PostgreSQL 17."""
from sqlalchemy import text

from app.extensions import db
from app.models.user import User


def test_postgres_schema_timezone_and_constraints(app):
    if db.engine.dialect.name != 'postgresql':
        return
    assert db.session.execute(text(
        "select to_regclass('app.alembic_version') is not null"
    )).scalar() is True
    assert db.session.execute(text(
        "select count(*) = 0 from information_schema.columns "
        "where table_schema='app' "
        "and data_type='timestamp without time zone'"
    )).scalar() is True
    assert db.session.execute(text(
        "select current_schema() = 'app'"
    )).scalar() is True

    user = User(username='pg-smoke', email='pg-smoke@example.com', coins=0)
    db.session.add(user)
    db.session.commit()
    assert user.created_at is not None
