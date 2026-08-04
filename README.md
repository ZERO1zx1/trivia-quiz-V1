# 🎮 TriviaVerse — Enterprise Multiplayer Trivia Engine

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)
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
| **Database** | Supabase PostgreSQL (Managed), Redis (Cache/Queue) |
| **Frontend** | Jinja2, Glassmorphism UI, Vanilla JS |
| **Bot System** | discord.py 2.6+ |
| **AI Integration**| OpenAI API (GPT-4), Gemini, Claude |
| **DevOps** | Docker, Nginx, GitHub Actions, Prometheus, Grafana |

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

Төслийн дэлгэрэнгүй бүтэц болон техникийн баримт бичгийг [DOCUMENTATION.md](./DOCUMENTATION.md) файлаас харна уу.

---

## ⚙️ Суулгах Заавар (Installation)

### 1. Репозиторийг хуулах
```bash
git clone https://github.com/ZERO1zx1/trivia-quiz-V1.git
cd trivia-quiz-V1
```

### 2. Docker ашиглан ажиллуулах (Санал болгож буй)
```bash
docker-compose up --build
```

### 3. Гараар ажиллуулах
	1. `.env` файлыг тохируулах (Supabase DATABASE_URL болон API түлхүүрүүдийг нэмэх).
2. `pip install -r requirements.txt`
3. `python run.py` (Вэб сервер)
4. `python discord_bot/bot.py` (Discord бот)

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
