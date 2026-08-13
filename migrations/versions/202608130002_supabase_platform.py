"""Supabase platform hardening: private schema, roles, Storage, Realtime.

Revision ID: 202608130002
Revises: 15686c108f32
Create Date: 2026-08-13
"""
from alembic import op


revision = '202608130002'
down_revision = '15686c108f32'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('SET search_path = app, public')

    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'users_auth_user_id_fkey'
          AND conrelid = 'app.users'::regclass
      ) THEN
        ALTER TABLE app.users
          ADD CONSTRAINT users_auth_user_id_fkey
          FOREIGN KEY (auth_user_id) REFERENCES auth.users(id)
          ON DELETE SET NULL;
      END IF;
    END $$;
    """)

    # Existing SQLite datetimes are UTC by contract. PostgreSQL stores every
    # application timestamp as an instant, preserving the original wall time.
    op.execute("""
    DO $$
    DECLARE column_record record;
    BEGIN
      FOR column_record IN
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'app'
          AND data_type = 'timestamp without time zone'
      LOOP
        EXECUTE format(
          'ALTER TABLE app.%I ALTER COLUMN %I TYPE timestamptz '
          'USING %I AT TIME ZONE ''UTC''',
          column_record.table_name,
          column_record.column_name,
          column_record.column_name
        );
      END LOOP;
    END $$;
    """)

    # Index every FK whose leading columns are not already covered by an
    # index. This keeps joins/deletes predictable on the imported 98-table
    # schema and makes Realtime membership checks cheap.
    op.execute("""
    DO $$
    DECLARE fk record;
    DECLARE index_name text;
    BEGIN
      FOR fk IN
        SELECT
          c.conrelid,
          n.nspname AS schema_name,
          t.relname AS table_name,
          c.conname,
          c.conkey
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE c.contype = 'f' AND n.nspname = 'app'
          AND NOT EXISTS (
            SELECT 1 FROM pg_index i
            WHERE i.indrelid = c.conrelid
              AND i.indisvalid
              AND i.indkey[0] = c.conkey[1]
          )
      LOOP
        index_name := left('ix_' || fk.table_name || '_' || fk.conname, 63);
        EXECUTE format(
          'CREATE INDEX IF NOT EXISTS %I ON %I.%I (%s)',
          index_name, fk.schema_name, fk.table_name,
          (SELECT string_agg(quote_ident(a.attname), ', ' ORDER BY u.ordinality)
           FROM unnest(fk.conkey) WITH ORDINALITY AS u(attnum, ordinality)
           JOIN pg_attribute a
             ON a.attrelid = fk.conrelid AND a.attnum = u.attnum)
        );
      END LOOP;
    END $$;
    """)

    op.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS
      uq_category_analytics_user_category
      ON app.category_analytics(user_id, category);
    """)

    # Roles are created without passwords. scripts/provision_roles.py enables
    # LOGIN using secrets supplied outside Git, then the session-pooler URL is
    # stored directly in Render.
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='triviaverse_app') THEN
        CREATE ROLE triviaverse_app NOLOGIN NOINHERIT NOSUPERUSER
          NOCREATEDB NOCREATEROLE NOREPLICATION;
      END IF;
      IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname='triviaverse_migrator'
      ) THEN
        CREATE ROLE triviaverse_migrator NOLOGIN NOINHERIT NOSUPERUSER
          NOCREATEDB NOCREATEROLE NOREPLICATION;
      END IF;
    END $$;

    REVOKE ALL ON SCHEMA app FROM PUBLIC, anon, authenticated;
    GRANT USAGE ON SCHEMA app TO triviaverse_app;
    GRANT SELECT, INSERT, UPDATE, DELETE
      ON ALL TABLES IN SCHEMA app TO triviaverse_app;
    GRANT USAGE, SELECT, UPDATE
      ON ALL SEQUENCES IN SCHEMA app TO triviaverse_app;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO triviaverse_app;

    GRANT USAGE, CREATE ON SCHEMA app TO triviaverse_migrator;
    GRANT ALL PRIVILEGES
      ON ALL TABLES IN SCHEMA app TO triviaverse_migrator;
    GRANT ALL PRIVILEGES
      ON ALL SEQUENCES IN SCHEMA app TO triviaverse_migrator;
    GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA app TO triviaverse_migrator;

    ALTER DEFAULT PRIVILEGES IN SCHEMA app
      GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO triviaverse_app;
    ALTER DEFAULT PRIVILEGES IN SCHEMA app
      GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO triviaverse_app;
    """)

    # Storage buckets are public-read image CDN buckets. Authenticated clients
    # may only create/update/delete objects below their own Auth UUID prefix.
    op.execute("""
    INSERT INTO storage.buckets
      (id, name, public, file_size_limit, allowed_mime_types)
    VALUES
      ('avatars', 'avatars', true, 6291456, ARRAY['image/webp']),
      ('banners', 'banners', true, 6291456, ARRAY['image/webp'])
    ON CONFLICT (id) DO UPDATE SET
      public = EXCLUDED.public,
      file_size_limit = EXCLUDED.file_size_limit,
      allowed_mime_types = EXCLUDED.allowed_mime_types;

    DROP POLICY IF EXISTS triviaverse_images_read ON storage.objects;
    CREATE POLICY triviaverse_images_read
      ON storage.objects FOR SELECT TO anon, authenticated
      USING (bucket_id IN ('avatars', 'banners'));

    DROP POLICY IF EXISTS triviaverse_images_insert ON storage.objects;
    CREATE POLICY triviaverse_images_insert
      ON storage.objects FOR INSERT TO authenticated
      WITH CHECK (
        bucket_id IN ('avatars', 'banners')
        AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
      );

    DROP POLICY IF EXISTS triviaverse_images_update ON storage.objects;
    CREATE POLICY triviaverse_images_update
      ON storage.objects FOR UPDATE TO authenticated
      USING (
        bucket_id IN ('avatars', 'banners')
        AND owner_id = (SELECT auth.uid()::text)
      )
      WITH CHECK (
        bucket_id IN ('avatars', 'banners')
        AND (storage.foldername(name))[1] = (SELECT auth.uid()::text)
      );

    DROP POLICY IF EXISTS triviaverse_images_delete ON storage.objects;
    CREATE POLICY triviaverse_images_delete
      ON storage.objects FOR DELETE TO authenticated
      USING (
        bucket_id IN ('avatars', 'banners')
        AND owner_id = (SELECT auth.uid()::text)
      );
    """)

    # Topic authorization is centralized in a SECURITY DEFINER function whose
    # search_path is empty. app tables remain invisible to the Data API roles.
    op.execute("""
    CREATE OR REPLACE FUNCTION app.can_access_realtime_topic(topic text)
    RETURNS boolean
    LANGUAGE plpgsql
    STABLE
    SECURITY DEFINER
    SET search_path = ''
    AS $$
    DECLARE
      auth_id uuid := auth.uid();
      channel_id integer;
    BEGIN
      IF auth_id IS NULL THEN
        RETURN false;
      END IF;

      IF topic = 'user:' || auth_id::text || ':notifications' THEN
        RETURN true;
      END IF;

      IF topic ~ '^chat:[0-9]+:messages$' THEN
        channel_id := split_part(topic, ':', 2)::integer;
        RETURN EXISTS (
          SELECT 1
          FROM app.chat_channels c
          WHERE c.id = channel_id
            AND (
              c.channel_type IN ('global', 'public')
              OR EXISTS (
                SELECT 1
                FROM app.chat_members cm
                JOIN app.users u ON u.id = cm.user_id
                WHERE cm.channel_id = c.id
                  AND u.auth_user_id = auth_id
              )
            )
        );
      END IF;

      RETURN false;
    EXCEPTION WHEN invalid_text_representation THEN
      RETURN false;
    END;
    $$;

    REVOKE ALL ON FUNCTION app.can_access_realtime_topic(text) FROM PUBLIC;
    GRANT EXECUTE ON FUNCTION app.can_access_realtime_topic(text)
      TO authenticated;

    DROP POLICY IF EXISTS triviaverse_realtime_receive
      ON realtime.messages;
    CREATE POLICY triviaverse_realtime_receive
      ON realtime.messages FOR SELECT TO authenticated
      USING (app.can_access_realtime_topic((SELECT realtime.topic())));

    DROP POLICY IF EXISTS triviaverse_realtime_send
      ON realtime.messages;
    CREATE POLICY triviaverse_realtime_send
      ON realtime.messages FOR INSERT TO authenticated
      WITH CHECK (app.can_access_realtime_topic((SELECT realtime.topic())));
    """)


def downgrade():
    op.execute("""
    DROP POLICY IF EXISTS triviaverse_realtime_send ON realtime.messages;
    DROP POLICY IF EXISTS triviaverse_realtime_receive ON realtime.messages;
    DROP FUNCTION IF EXISTS app.can_access_realtime_topic(text);
    DROP POLICY IF EXISTS triviaverse_images_delete ON storage.objects;
    DROP POLICY IF EXISTS triviaverse_images_update ON storage.objects;
    DROP POLICY IF EXISTS triviaverse_images_insert ON storage.objects;
    DROP POLICY IF EXISTS triviaverse_images_read ON storage.objects;
    DELETE FROM storage.buckets WHERE id IN ('avatars', 'banners');
    ALTER TABLE app.users DROP CONSTRAINT IF EXISTS users_auth_user_id_fkey;
    """)
