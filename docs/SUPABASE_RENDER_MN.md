# TriviaVerse: Supabase + Render production runbook

Энэ заавар нь `website` Supabase project (`rqohugxyvdomjmcvknde`, Singapore)
болон Render Singapore Docker Web Service-д зориулагдсан. Хуучин Supabase
project, эх SQLite, backup-ийг устгах алхам энд байхгүй.

## Архитектур

- Бүх ORM table `app` private schema-д байна. `anon`, `authenticated` болон
  Data API эдгээр table-д эрхгүй.
- `users.id` болон одоогийн integer foreign key хэвээр; `auth_user_id UUID`
  нь Supabase Auth account-тай холбоно.
- Runtime нь хамгийн бага эрхтэй `triviaverse_app`, migration/import нь
  `triviaverse_migrator` role ашиглана.
- Avatar/banner нь Supabase Storage, chat/notification/presence нь Realtime,
  authoritative game event нь Socket.IO хэвээр. Game state бүр PostgreSQL-д
  snapshot хийгдэнэ.
- Render filesystem-д durable өгөгдөл хадгалахгүй.

## 1. Secret ба connection

Secret бүрийг password manager эсвэл deployment secret store-д хадгална.
Git, issue, log, chat-д тавихгүй.

- `DATABASE_URL`: Supavisor **session pooler**, port `5432`,
  `triviaverse_app` role, TLS.
- `MIGRATION_DATABASE_URL`: direct/authorized migration connection,
  `triviaverse_migrator` role, TLS.
- `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`: browser-д өгч болох public
  config.
- `SUPABASE_SECRET_KEY`, `SECRET_KEY`, `JWT_SECRET_KEY`, database password:
  server-only secret.

Role migration-аар эхлээд `NOLOGIN` үүснэ. Random password-ийг environment-оор
өгч нэг удаа login role болгоно:

```bash
python scripts/provision_roles.py
```

Үүнд `MIGRATION_DATABASE_URL`, `TRIVIAVERSE_APP_PASSWORD`,
`TRIVIAVERSE_MIGRATOR_PASSWORD` шаардлагатай.

## 2. Baseline migration

Runtime дээр `db.create_all()` ажиллахгүй. Schema өөрчлөх цорын ганц зам нь
versioned Alembic migration:

```bash
set FLASK_ENV=production
set DATABASE_URL=<runtime-session-pooler-url>
set MIGRATION_DATABASE_URL=<authorized-direct-url>
flask db upgrade
flask db current
```

Эхний revision нь бүх model/constraint/index-ийн baseline; дараагийн revision
нь Auth bridge, timezone-aware timestamp, FK index, roles, Storage policy,
private Realtime authorization үүсгэнэ.

## 3. SQLite backup ба алдагдалгүй import

Эх файлыг ажиллаж байх үед өөрчилж болохгүй. SQLite backup API ашиглан
consistent copy ба SHA-256 manifest үүсгэнэ:

```bash
python scripts/backup_sqlite.py triviaverse.db backups/triviaverse-before-supabase.db
```

Import target schema хоосон үед:

```bash
python scripts/import_sqlite_to_postgres.py backups/triviaverse-before-supabase.db --report backups/import-report.json
```

Importer нь transaction дотор dependency order-оор insert хийж, ID/FK/UTC
timestamp хадгална; integer sequence-ийг `max(id)`-тай тааруулна. Commit-ийн
дараа table бүрийн row count, primary-key checksum, canonical row checksum,
foreign key validation-ыг дахин шалгана. Нэг шалгалт зөрвөл command fail болно.

Одоогийн source backup:

- SHA-256: `57d7177fcf62a5783d6eb09f674c070a7d8f1ef65269082c518060953aed4089`
- Imported seed/business rows: achievements 8, categories 10, chat channels 6,
  daily quests 3, forum categories 7, pet species 5, regions 7,
  transactions 2, user achievements 8, users 1.
- Нэг upload файл database owner/reference-гүй orphan байсан; backup-д
  хадгалагдсан, Storage object болгон импортлоогүй.

## 4. Supabase Auth, Storage, Realtime

Auth dashboard-д production Site URL болон дараах redirect-үүдийг allowlist-д
нэмнэ:

- `https://<render-service>.onrender.com/auth/discord/callback`
- `https://<render-service>.onrender.com/auth/callback`
- local development-д `http://localhost:5000/...`

Discord provider-ийн client ID/secret-ийг Supabase secret UI-д тохируулна.
Email/password ба MFA-г enable хийнэ. Legacy хэрэглэгч зөв password-аар анх
нэвтрэх үед Auth account автоматаар үүсэж `auth_user_id` холбоно; амжилттай
cutover-ийн дараа legacy password hash арилна.

Migration нь `avatars`, `banners` public-read bucket (WebP, 6 MiB) болон
owner-only insert/update/delete policy үүсгэнэ. Object path нь
`{auth_user_id}/...` байна. Realtime private topic membership-ийг
`app.can_access_realtime_topic` шалгана; service/secret key frontend-д очихгүй.

## 5. Render Blueprint deploy

Render Dashboard → New → Blueprint → GitHub repository сонгоход
`render.yaml` автоматаар уншигдана. Plan нь `free`, region нь `singapore`,
branch нь `main`, auto-deploy нь `checksPass`, health check нь
`/health/ready`.

Blueprint deploy-оос өмнө `sync:false` утгуудыг Render secret болгон оруулна:

- `DATABASE_URL`
- `MIGRATION_DATABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY`
- `SOCKETIO_CORS_ALLOWED_ORIGINS=https://<render-service>.onrender.com`

`SECRET_KEY`, `JWT_SECRET_KEY`-г Render санамсаргүй үүсгэнэ. Build дууссаны
дараа `/health/live` 200, `/health/ready` 200 байх ёстой. Free service 15 минут
idle үед унтаж, дараагийн request ойролцоогоор нэг минут cold start хийж болно;
always-on SLA биш.

## 6. Шалгалт

```bash
pytest tests --cov=app --cov-fail-under=60
ruff check . --select E9,F63,F7,F82
bandit -r app discord_bot -q -lll -ii
pip-audit -r requirements.lock
npm ci
npm run build
npm run check
npm audit --audit-level=high
docker compose config --quiet
docker build -t triviaverse .
```

Supabase Security Advisor critical/error 0 байх ёстой. Performance Advisor-ийн
unused-index info нь шинэ/бага өгөгдөлтэй project дээр informational байж болно.

## 7. Rollback

1. Render Dashboard-аас өмнөх healthy deploy-г сонгон rollback хийнэ.
2. Database schema rollback шаардлагатай бол эхлээд шинэ backup авна, тухайн
   release-д тохирох Alembic revision руу `flask db downgrade <revision>`
   ажиллуулна.
3. Import-ийг буцаах шаардлагатай бол production schema-г шууд устгахгүй;
   тусдаа recovery database/project дээр SQLite backup-аас restore хийж row
   count/checksum тулгасны дараа traffic шилжүүлнэ.
4. Хуучин Supabase project болон local SQLite backup-ийг баталгаатай хугацаа
   дуустал хадгална.

`main`-ийн шинэ deploy unhealthy бол Render traffic өмнөх deploy дээр үлдэх
ёстой. Migration болон application rollback-ийг нэг revision pair гэж үзнэ.
