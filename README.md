# 🎮 TriviaVerse — Enterprise Multiplayer Trivia Engine

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)
![Discord.py](https://img.shields.io/badge/Discord.py-2.6+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**TriviaVerse** нь бодит цагийн (Real-time) олон тоглогчийн trivia тоглоомын платформ бөгөөд Discord боттой бүрэн холбогдсон, Flask + Socket.IO дээр суурилсан веб экосистем юм. Энэхүү систем нь зөвхөн асуулт хариулт төдийгүй, RPG элемент, виртуал эдийн засаг, амжилтын системүүдийг өөртөө багтаасан **AAA түвшний MMO** архитектуртай.

---

## ✨ Онцлох боломжууд (Features)

### 🔗 Веб & Discord Hybrid Систем
* **Нэгдсэн Бааз:** Вебсайт болон Discord сервер дээрх зоос (Coins), инвентарь, XP зэрэг нь хоорондоо бодит цагт синхрончлогдоно.
* **OAuth2 Нэвтрэлт:** Discord хаягаараа нэг товшилтоор бүртгэл үүсгэж, нэвтрэх боломж.
* **Premium Sync:** Вэбээс Premium авахад Discord дээр автоматаар Role олгогдоно.

### 🕹️ Тоглоомын Горимууд (Live Modes)
* **Classic & Time Attack:** Бодит цагийн өрсөлдөөн, цагтай уралдах систем.
* **Survival Mode:** Буруу хариулбал амь хасагдах (Elimination) хатуу горим.
* **Quiz Duel (PvP):** 1v1 бооцоотой тулаан болон Elo Rating эрэмбэ.

### 💰 Эдийн Засаг & RPG (Economy)
* **Дэлгүүр & Инвентарь:** Avatar хүрээ, цол, хөдөлгөөнт эффект худалдаж авах.
* **Fortune Wheel & Rewards:** Өдөр тутмын азын хүрд болон Daily Quest систем.
* **Сошиал Харилцаа:** Marriage (гэрлэх), Respect өгөх, Найзууд нэмэх, Бэлэг илгээх.

---

## 🚀 Хөгжүүлэлтийн Замнал (Roadmap)

Бид төслийн архитектурыг дараах **4 үе шаттайгаар (Phases)** хөгжүүлж байна:

### ✅ Phase 0: Үндсэн Цөм (Completed)
- [x] OTP & Discord OAuth бүртгэлийн систем
- [x] Socket.IO бодит цагийн холболт
- [x] Classic, Time Attack, Solo горимууд
- [x] AI Асуулт үүсгэгч (OpenAI интеграци)
- [x] Олон хэлний дэмжлэг (EN, MN)
- [x] Docker & Docker Compose тохиргоо

### 🔄 Phase 1: Тоглоомын Контент (In Progress)
- [ ] **Multimedia Quiz:** Voice (дуу таах), Image (зураг таах), Video горимууд.
- [ ] **Puzzle & Learning:** Санах ойн дасгал, үгийн сүлжээ, тайлбартай сургалтын горим.
- [ ] **AI Coach:** Тоглогчийн алдаан дээр дүн шинжилгээ хийх туслах.

### 🔄 Phase 2: Өрсөлдөөн ба Сошиал (Upcoming)
- [ ] **Guild System 2.0:** Бүлгэм байгуулж, Guild Wars болон Guild Boss-д оролцох.
- [ ] **Tournament System:** Bracket, Swiss хэлбэрийн шагналт тэмцээнүүд.
- [ ] **Battle Pass & Events:** Улирлын чанартай шагналын систем, тусгай эвентүүд.
- [ ] **Advanced Chat:** Global, Guild, Private чат болон Community Forum.

### 🔄 Phase 3: Эдийн Засаг ба RPG элементүүд
- [ ] **Marketplace:** Тоглогчид хоорондоо айтем зарах, солилцох.
- [ ] **Crafting & Pets:** Илүүдэл зүйлсийг нэгтгэж шинийг урлах, туслах амьтан дагуулах.
- [ ] **Collection Book:** Цуглуулсан ховор зүйлсээ хадгалах визуал сан.

### 🔄 Phase 4: Enterprise Дэд Бүтэц
- [ ] **Security 2.0:** 2FA, Ban Appeal, Төхөөрөмжийн түүх.
- [ ] **Spectator & Replay:** Тоглолтын бичлэг ухрааж үзэх, шууд дамжуулалт хянах.
- [ ] **DevOps Analytics:** Prometheus, Grafana, CI/CD автоматжуулалт.

---

## 🛠️ Технологийн Стек (Tech Stack)

| Төрөл | Технологи |
| --- | --- |
| **Backend** | Python 3.12+, Flask, Flask-SocketIO |
| **Database** | PostgreSQL (Production), SQLite (Dev), Redis (Cache/Queue) |
| **Frontend** | HTML5, CSS3 (Glassmorphism, Dark Theme), Vanilla JS, Jinja2 |
| **Bot System** | discord.py 2.6+ |
| **AI Integration**| OpenAI API (GPT-3.5/4) |
| **DevOps** | Docker, Docker Compose, Nginx, GitHub Actions |

---

## 🎨 UI / UX Загвар (Design System)

Төсөл нь **AAA Gaming Style** буюу орчин үеийн бараан өнгөний хослол дээр суурилсан.
* **Theme:** Dark Theme (`#09090B`) + Glassmorphism (Frosted Cards)
* **Accents:** Purple (`#7C3AED`) & Blue Gradient, Neon гэрэлтэлт.
* **Typography:** Space Grotesk (Гарчиг), Inter (Бичвэр), JetBrains Mono (Тооцоолол).
* **Animations:** Smooth transitions, Hover Glow, Particle backgrounds.

---

## ⚙️ Суулгах Заавар (Installation)

### 1. Репозиторийг хуулах
```bash
git clone [https://github.com/ZERO1zx1/trivia-quiz-V1.git](https://github.com/ZERO1zx1/trivia-quiz-V1.git)
cd trivia-quiz-V1

```

### 2. Python Виртуал орчин үүсгэх (Virtual Environment)

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

```

### 3. Сангуудыг суулгах

```bash
pip install -r requirements.txt

```

### 4. Орчны хувьсагч тохируулах (.env)

Үндсэн хавтаст `.env` файл үүсгээд дараах тохиргоог хийнэ үү:

```env
SECRET_KEY=your-super-secret-key
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_BOT_TOKEN=your_discord_bot_token
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
OPENAI_API_KEY=sk-your-openai-api-key

```

### 5. Сервер болон Ботыг ажиллуулах

Веб серверийг эхлүүлэх (Өгөгдлийн сан автоматаар үүснэ):

```bash
python run.py

```

*Хөтөч дээр: `http://localhost:5000*`

Discord Ботыг асаах (Шинэ терминал дээр):

```bash
python discord_bot/bot.py

```

---

## 🤖 Discord Bot Командууд

| Команд | Тайлбар | Эрх |
| --- | --- | --- |
| `/profile [user]` | Профайл болон статистикаа харах | Хүн бүр |
| `/daily` & `/spin` | Өдрийн шагнал авах, Азын хүрд эргүүлэх | Хүн бүр |
| `/quiz-duel @user` | 1v1 бооцоот тулаанд дуудах | Хүн бүр |
| `/shop` & `/buy` | Дэлгүүрээс айтем харах, худалдаж авах | Хүн бүр |
| `/marry @user` | Өөр тоглогчтой гэрлэх 💍 | Хүн бүр |
| `/rep @user` | Тоглогчид хүндэтгэл (Respect) илэрхийлэх | Хүн бүр |
| `/attack` | World Boss руу дайралт хийх | Хүн бүр |
| `/ban`, `/kick` | Тоглогчийг серверээс хөөх, хориглох | Модератор |
| `/add-xp` | Хэрэглэгчид туршлагын оноо өгөх | Админ |

---

## 🤝 Хамтран Ажиллах (Contributing)

Хэрэв та энэхүү төсөлд хувь нэмрээ оруулахыг хүсвэл `Pull Request` илгээх эсвэл `Issue` үүсгэж бидэнтэй нэгдээрэй.

## 📄 Лиценз (License)

Энэхүү төсөл нь **MIT License**-ийн дагуу түгээгддэг. Дэлгэрэнгүйг `LICENSE` файлаас харна уу.

---

*© 2026 TriviaVerse. Бүх эрх хуулиар хамгаалагдсан.*

```

```
