# 🎮 TriviaVerse — Enterprise Multiplayer Trivia Engine

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.1-lightgrey.svg)
![Discord.py](https://img.shields.io/badge/Discord.py-2.6+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**TriviaVerse** нь бодит цагийн (Real-time) олон тоглогчийн trivia тоглоомын платформ бөгөөд Discord боттой бүрэн холбогдсон, Flask + Socket.IO дээр суурилсан веб экосистем юм. Энэхүү систем нь зөвхөн асуулт хариулт төдийгүй, RPG элемент, виртуал эдийн засаг, амжилтын системүүдийг өөртөө багтаасан **AAA түвшний MMO** архитектуртай.

---

## ✨ Үндсэн боломжууд (Core Features)

### 🔗 Веб & Discord Hybrid Систем
* **Нэгдсэн Бааз:** Вебсайт болон Discord сервер дээрх зоос (Coins), инвентарь, XP зэрэг нь хоорондоо бодит цагт синхрончлогдоно.
* **OAuth2 Нэвтрэлт:** Discord хаягаараа нэг товшилтоор бүртгэл үүсгэж, нэвтрэх боломж.
* **Premium Sync:** Вэбээс Premium авахад Discord дээр автоматаар Role олгогдоно.

### 🕹️ Тоглоомын Горимууд (Game Modes)
* **Classic & Time Attack:** Бодит цагийн өрсөлдөөн, цагтай уралдах систем.
* **Survival Mode:** Буруу хариулвал амь хасагдах (Elimination) хатуу горим.
* **Quiz Duel (PvP):** 1v1 бооцоотой тулаан болон Elo Rating эрэмбэ.
* **World Boss:** Сервер даяарх тоглогчид нэгдэн хүчирхэг Boss-ыг ялах горим.

### 💰 Эдийн Засаг & RPG (Economy & RPG)
* **Marketplace:** Тоглогчид хоорондоо айтем зарах, солилцох (ACID transactions).
* **Crafting & Pets:** Илүүдэл зүйлсийг нэгтгэж шинийг урлах, туслах амьтан дагуулах.
* **Fortune Wheel:** Өдөр тутмын азын хүрд болон Daily Quest систем.

---

## 🛠️ Технологийн Стек (Tech Stack)

| Төрөл | Технологи |
| --- | --- |
| **Backend** | Python 3.12+, Flask, Flask-SocketIO |
| **Database** | Supabase PostgreSQL 17 (`app` private schema) |
| **Auth / Files / Events** | Supabase Auth, Storage, Realtime |
| **Frontend** | Jinja2, Vanilla JS, pinned npm bundles |
| **Bot System** | discord.py 2.6+ |
| **AI Integration**| OpenAI API (GPT-4), Gemini, Claude |
| **DevOps** | Docker, Render Blueprint, GitHub Actions |

---

## 🚀 Хөгжүүлэлтийн Замнал (Roadmap)

### ✅ Phase 0-2: Суурь ба Сошиал (Completed)
- [x] OTP & Discord OAuth бүртгэл
- [x] Socket.IO бодит цагийн холболт
- [x] Guild System & Tournament System
- [x] Advanced Chat & Forum

### ✅ Phase 3-4: Эдийн засаг ба Дэд бүтэц (Completed)
- [x] Marketplace & Crafting
- [x] Security 2.0 (2FA, Audit Logs)
- [x] Spectator & Replay System
- [x] Anti-Cheat System

---

## 📂 Төслийн бүтэц (Project Structure)

Төслийн дэлгэрэнгүй бүтэц болон техникийн баримт бичгийг
[DOCUMENTATION.md](./docs/DOCUMENTATION.md), production ажиллуулах зааврыг
[SUPABASE_RENDER_MN.md](./docs/SUPABASE_RENDER_MN.md)-ээс харна уу.

---

## ⚙️ Суулгах Заавар (Installation)

### 1. Репозиторийг хуулах
```bash
git clone https://github.com/ZERO1zx1/trivia-quiz-V1.git
cd trivia-quiz-V1
```

### 2. Environment бэлтгэх

```bash
cp .env.example .env
```

`.env` доторх secret болон Supabase connection-уудыг бөглөнө. Secret-ийг Git-д
commit хийж болохгүй.

### 3. Docker ашиглан ажиллуулах (Санал болгож буй)

```bash
docker compose up --build
```

### 4. Гараар ажиллуулах

1. Python 3.12, Node 22 суулгана.
2. `pip install -r requirements.lock`
3. `npm ci && npm run build`
4. `flask db upgrade`
5. `python run.py` (веб сервер)
6. `python discord_bot/bot.py` (Discord бот, optional)

## ✅ Шалгалт

```bash
pytest tests --cov=app --cov-fail-under=60
npm run check
docker compose config --quiet
docker build -t triviaverse .
```

CI нь PostgreSQL 17 migration forward/rollback, Python/JS security audit,
coverage, Compose болон production Docker build-ийг шалгана. Runtime дээр
`/health/live` процесс, `/health/ready` database ба Alembic schema-г шалгана.

## ☁️ Production

`render.yaml` нь Singapore region дахь Render Docker Web Service-ийг `main`
branch-аас checks pass болсны дараа deploy хийнэ. Durable өгөгдөл, session,
зураг, game snapshot бүгд Supabase-д хадгалагдана. Render-ийн free service 15
минут trafficгүй үед sleep хийж, дараагийн хүсэлт cold start авч болно.

Migration, SQLite import verification, Auth/Storage/Realtime, secret, deploy,
rollback-ийн алхмууд: [Монгол production runbook](./docs/SUPABASE_RENDER_MN.md).

---

## 🤖 Discord Bot Командууд

| Команд | Тайлбар |
| --- | --- |
| `/profile` | Өөрийн статистик харах |
| `/quiz-duel` | 1v1 тулаанд дуудах |
| `/shop` | Дэлгүүр нээх |
| `/attack` | World Boss руу дайрах |

---

## 📄 Лиценз (License)

Энэхүү төсөл нь **MIT License**-ийн дагуу түгээгддэг.

---
*© 2026 TriviaVerse. Бүх эрх хуулиар хамгаалагдсан.*
