"""Enable least-privilege login roles without putting passwords in Git.

Required environment variables:
  MIGRATION_DATABASE_URL   authorized direct database connection
  TRIVIAVERSE_APP_PASSWORD
  TRIVIAVERSE_MIGRATOR_PASSWORD
"""
import os

import psycopg2
from psycopg2 import sql


def required(name):
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f'{name} is required')
    return value


def main():
    connection = psycopg2.connect(required('MIGRATION_DATABASE_URL'))
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            for role, variable in (
                ('triviaverse_app', 'TRIVIAVERSE_APP_PASSWORD'),
                ('triviaverse_migrator', 'TRIVIAVERSE_MIGRATOR_PASSWORD'),
            ):
                cursor.execute(
                    sql.SQL('ALTER ROLE {} LOGIN PASSWORD %s').format(
                        sql.Identifier(role)),
                    (required(variable),),
                )
    finally:
        connection.close()
    print('TriviaVerse database roles provisioned successfully.')


if __name__ == '__main__':
    main()
