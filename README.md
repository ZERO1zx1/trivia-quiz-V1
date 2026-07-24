# 🎮 TriviaVerse - Бүрэн README

**TriviaVerse** нь бодит цагийн олон тоглогчийн trivia тоглоомын платформ бөгөөд Discord боттой бүрэн холбогдсон, Flask + Socket.IO дээр суурилсан вэбсайт юм.  
Найзуудтайгаа өрсөлдөх, тэргүүлэгчдийн самбарт гарах, өдөр тутмын шагнал авах, тусгай зүйлс цуглуулах зэрэг олон боломжтой.

---

## ✨ Онцлог шинжүүд

### 🔐 Хэрэглэгчийн систем
- Бүртгэл, нэвтрэлт (имэйл/нууц үг)
- Discord OAuth2 нэвтрэлт
- Профайл тохируулга (avatar, banner, bio, country)
- Role систем (Owner, Developer, Admin, Moderator, Helper, User)
- Premium гишүүнчлэл (3x coin multiplier, тусгай хүрээ, Discord роль)

### 🏠 Хувийн Dashboard
- Статистик картууд (Wins, Accuracy, Level, Coins)
- XP Progress Bar
- Өдрийн шагнал (Daily Reward)
- Өдрийн даалгавар (Daily Quests)
- Fortune Wheel (өдөр тутмын азын хүрд)
- Solo Practice товч (ганцаарчилсан дасгал)

### 🕹️ Тоглоомын горимууд
- **Classic**: Бүгд ижил асуулт, хамгийн өндөр оноотой нь ялна
- **Time Attack**: Богино хугацаанд хурдан хариулах
- **Survival**: Буруу хариулвал амь хасагдана
- **Solo Practice**: Өрөө үүсгэлгүйгээр дасгал хийх

### 🛒 Дэлгүүр, Инвентар
- Дэлгүүрээс frame, badge, title худалдаж авах
- Инвентарт цуглуулсан зүйлсээ equip/unequip хийх
- Авдар (Box) нээх, loot авах

### 🎡 Fortune Wheel
- Өдөрт 1 удаа үнэгүй эргүүлэх
- Шагнал: coins, XP, box, Jackpot (10,000 coins + Golden Aura Frame)

### 🏆 Амжилтууд (Achievements)
- Тодорхой нөхцөл хангахад unlock хийгдэнэ
- XP, coins шагналтай
- Профайл дээр badge хэлбэрээр харагдана

### 👥 Нийгмийн харилцаа
- Найзуудын систем (friend request, accept, decline, remove)
- Challenge (1v1 урилга)
- Gift илгээх (coffee, crown, xp_boost)
- Respect өгөх
- Mini-Chat (хөвөгч чат)

### 👑 Premium гишүүнчлэл
- 3x coin multiplier (бүх тоглолтонд)
- Өдөр бүр 3,000 coins claim
- Тусгай нэрний эффект (glow, gradient)
- Профайл хөгжим
- 500+ авдар хадгалах багтаамж
- Discord дээр Premium роль автоматаар олгогдоно

### 🌐 Олон хэлний дэмжлэг
- Flask-Babel ашиглан Англи, Монгол хэл дээр ажиллана
- Navbar дээрх товчлуураар шууд солих
- Хэрэглэгчийн профайлд сонгосон хэл хадгалагдана

### ⚡ Реал-тайм тоглолт
- Socket.IO ашиглан бодит цагийн асуулт, хариулт
- Тоглогчдын жагсаалт, онооны самбар, таймер
- Survival Mode-д амьдралын тоо, elimination
- Staff командууд (skip question, kick player)

### 🤖 Discord Bot
- `/profile`, `/daily`, `/spin`, `/shop`, `/inventory` зэрэг тушаалууд
- Автомат мэдэгдэл (найзын хүсэлт, тоглоомын урилга, level up)
- Webhook ашиглан серверийн алдааг Discord сувагт мэдэгдэх
- Premium роль автоматаар олгох/хураах

### 📊 Админ панел
- Хэрэглэгчдийн удирдлага (role өөрчлөх, ban, premium олгох, coins өгөх)
- Асуултын удирдлага (нэмэх, устгах, AI Generate)
- Дэлгүүрийн бараа нэмэх/устгах
- Амжилт, категори, мэдэгдэл харах
- Discord Announcement илгээх

### 🧠 AI асуулт үүсгэгч
- OpenAI API ашиглан автоматаар trivia асуулт үүсгэх
- Категори, хүндрэл, тоо ширхэгийг сонгох боломжтой
- Админ панелаас ажиллуулна

---

## 🛠️ Ашигласан технологи

| Төрөл | Технологи |
|-------|-----------|
| Backend | Python 3.12+, Flask, Flask-SocketIO |
| Database | SQLite (production-д PostgreSQL руу шилжүүлэх боломжтой) |
| Frontend | Jinja2, HTML5, CSS3, JavaScript |
| CSS Framework | Custom (Glassmorphism, CSS Grid, Flexbox) |
| Bot | discord.py 2.6+ |
| AI | OpenAI API (GPT-3.5-turbo) |
| Queue | Redis + RQ (background tasks) |
| Scheduler | APScheduler (premium expiry check) |
| Migration | Flask-Migrate (Alembic) |
| Security | Flask-WTF (CSRF), Flask-Limiter (Rate Limiting), Flask-CORS |

---

## 📦 Суулгах заавар

### 1. Репозиторыг хуулах
```bash
git clone https://github.com/yourusername/triviaverse.git
cd triviaverse
```

### 2. Python виртуал орчин үүсгэх
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Шаардлагатай сангуудыг суулгах
```bash
pip install -r requirements.txt
```

`requirements.txt` агуулга:
```
Flask==3.1.1
Werkzeug==3.1.3
Flask-SQLAlchemy==3.1.1
SQLAlchemy==2.0.43
Flask-Migrate==4.1.0
Flask-Login==0.6.3
Flask-WTF==1.2.2
WTForms==3.2.1
PyJWT==2.10.1
bcrypt==4.3.0
Flask-SocketIO==5.5.1
python-socketio==5.13.0
eventlet>=0.40.0
discord.py==2.6.0
aiohttp==3.12.15
python-dotenv==1.1.1
requests==2.32.4
Pillow==11.3.0
gunicorn==23.0.0
gevent==25.5.1
openai==1.99.9
flask-cors==5.0.0
Flask-Limiter==3.9.0
bleach==6.2.0
APScheduler==3.11.0
flask-babel==4.0.0
redis==5.0.0
rq==1.16.0
```

### 4. Тохиргоо хийх

Төслийн үндсэн хавтаст `.env` файл үүсгэж, дараах хувьсагчдыг тохируулна:

```env
# Flask
SECRET_KEY=your-super-secret-key-change-this

# Discord
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_GUILD_ID=your_guild_id

# OpenAI (заавал биш, AI Generate функцэд)
OPENAI_API_KEY=sk-your-openai-api-key

# Owner тохиргоо (аль нэгийг нь ашиглах)
OWNER_USERNAME=your_username
# OWNER_DISCORD_ID=your_discord_id
# OWNER_EMAIL=your_email@gmail.com

# Discord Webhook (алдаа мэдэгдэлд)
DISCORD_ERROR_WEBHOOK=https://discord.com/api/webhooks/...

# Gmail (имэйл илгээхэд)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

### 5. Өгөгдлийн сан үүсгэх

**Хөгжүүлэлтийн үед (анх удаа):**
```bash
python run.py
```
Сервер эхлэхэд `db.create_all()` автоматаар бүх хүснэгтийг үүсгэнэ.

**Production үед (Flask-Migrate ашиглах):**
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

---

## 🚀 Ажиллуулах

### Вэб сервер
```bash
python run.py
```
Хөтөч дээр `http://localhost:5000` хаягаар нээнэ.

### Discord Bot
```bash
python discord_bot/bot.py
```
Бот таны Discord серверт онлайн болж, тушаалуудыг хүлээн авахад бэлэн болно.

---

## 🌐 Олон хэлний дэмжлэг (Flask-Babel)

### Орчуулгын санг бэлтгэх
```bash
# 1. Орчуулгын түлхүүрүүдийг татах
pybabel extract -F babel.cfg -o messages.pot .

# 2. Монгол хэлний орчуулгын сан үүсгэх (анх удаа)
pybabel init -i messages.pot -d translations -l mn

# 3. Орчуулгын санг шинэчлэх (шинэ түлхүүр нэмэх)
pybabel update -i messages.pot -d translations -l mn

# 4. Орчуулгын файлыг засварлах
#    translations/mn/LC_MESSAGES/messages.po файлд msgstr хэсгийг бөглөх

# 5. Compile хийх
pybabel compile -d translations
```

### Хэрэглэгч хэл солих
- Navbar дээрх `🇬🇧 EN` / `🇲🇳 MN` товчлууруудаар шууд солино.
- Тохиргоо хуудаснаас мөн сонгож болно.
- Сонгосон хэл нь хэрэглэгчийн профайлд хадгалагдана.

---

## 📂 Төслийн бүтэц

```
triviaverse/
├── app/                          # Үндсэн Flask апп
│   ├── models/                   # Өгөгдлийн сангийн загварууд
│   │   ├── user.py               # Хэрэглэгч, DiscordAccount, Friend
│   │   ├── question.py           # Category, Question, Answer
│   │   ├── room.py               # Room, RoomPlayer, Match, Score
│   │   ├── economy.py            # Transaction, LeaderboardEntry
│   │   ├── shop.py               # ShopItem, UserInventory
│   │   ├── achievement.py        # Achievement, UserAchievement
│   │   ├── notification.py       # Notification
│   │   ├── quest.py              # DailyQuest
│   │   ├── box.py                # Box, UserBox
│   │   ├── boss.py               # Boss
│   │   ├── profile.py            # ProfileView, UserRespect
│   │   └── title.py              # Title
│   ├── routes/                   # Blueprint-үүд (маршрутууд)
│   │   ├── home.py               # Нүүр хуудас, about, api/stats
│   │   ├── auth.py               # Бүртгэл, нэвтрэлт, Discord OAuth
│   │   ├── dashboard.py          # Хэрэглэгчийн хянах самбар
│   │   ├── rooms.py              # Өрөө үүсгэх, нэгдэх, гарах
│   │   ├── quiz.py               # Тоглоомын асуултууд, Solo тоглолт
│   │   ├── leaderboard.py        # Тэргүүлэгчдийн самбар
│   │   ├── social.py             # Найзууд
│   │   ├── account.py            # Профайл, тохиргоо
│   │   ├── shop.py               # Дэлгүүр
│   │   ├── inventory.py          # Инвентар
│   │   ├── api.py                # API endpoint-үүд
│   │   ├── admin.py              # Админ панел
│   │   ├── quests.py             # Өдрийн даалгаврууд
│   │   ├── fortune.py            # Fortune Wheel
│   │   ├── box_api.py            # Авдар нээх API
│   │   ├── boss_api.py           # Boss API
│   │   ├── user_api.py           # Хэрэглэгчийн харилцааны API
│   │   ├── language.py           # Хэл солих
│   │   └── api_v1.py             # RESTful API v1
│   ├── sockets/                  # Socket.IO event handler-ууд
│   │   ├── room_socket.py        # Өрөөний сокет (join, leave, ready, chat)
│   │   ├── game_socket.py        # Тоглоомын сокет (start, question, answer)
│   │   └── notification_socket.py # Мэдэгдлийн сокет
│   ├── utils/                    # Туслах функцүүд
│   │   ├── admin.py              # admin_required, role_required decorators
│   │   ├── ai.py                 # OpenAI API интеграц
│   │   ├── notify.py             # Мэдэгдэл илгээх
│   │   ├── scheduler.py          # Premium хугацаа шалгах
│   │   ├── email.py              # Имэйл илгээх
│   │   ├── error_logger.py       # Discord-т алдаа мэдэгдэх
│   │   └── role_helpers.py       # Role-н өнгө, нэр
│   ├── extensions.py             # Flask өргөтгөлүүд (db, mail, socketio, csrf, ...)
│   └── __init__.py               # Application factory (create_app)
├── discord_bot/                  # Discord ботын код
│   ├── bot.py                    # Ботын үндсэн тохиргоо
│   └── cogs/                     # Bot командууд
│       ├── quiz.py               # /trivia, /create-room, /join-room
│       ├── economy.py            # /daily, /balance, /shop, /buy
│       ├── profile.py            # /profile, /leaderboard
│       ├── level.py              # /rank, /top, /add-xp
│       ├── social.py             # /add-friend
│       ├── fortune.py            # /spin
│       ├── premium.py            # /premium
│       ├── inventory.py          # /inventory
│       ├── boss.py               # /attack (World Boss)
│       └── integration.py        # Role sync
├── static/                       # Статик файлууд
│   ├── css/
│   │   ├── app.css               # Үндсэн загвар
│   │   ├── quiz.css              # Тоглоомын загвар
│   │   └── animations.css        # Анимейшнууд
│   └── js/
│       ├── app.js                # Үндсэн JS
│       ├── socket.js             # Socket.IO клиент
│       ├── dashboard.js          # Dashboard функцүүд
│       ├── quiz.js               # Тоглоомын логик
│       ├── solo_quiz.js          # Solo тоглолтын логик
│       └── notifications.js      # Мэдэгдлийн систем
├── templates/                    # Jinja2 загварууд
│   ├── layouts/
│   │   └── base.html             # Үндсэн layout (sidebar, navbar)
│   ├── home/
│   │   ├── index.html            # Нүүр хуудас (лендинг)
│   │   └── about.html            # Тухай хуудас
│   ├── auth/
│   │   ├── login.html            # Нэвтрэх
│   │   ├── register.html         # Бүртгүүлэх
│   │   ├── forgot_password.html  # Нууц үг мартсан
│   │   └── reset_password.html   # Нууц үг сэргээх
│   ├── dashboard/
│   │   └── index.html            # Хэрэглэгчийн хянах самбар
│   ├── rooms/
│   │   ├── lobby.html            # Өрөөний лобби
│   │   └── room.html             # Өрөөний дэлгэрэнгүй
│   ├── quiz/
│   │   ├── play.html             # Тоглоомын дэлгэц
│   │   └── solo_play.html        # Solo тоглолт
│   ├── leaderboard/
│   │   └── index.html            # Тэргүүлэгчид
│   ├── social/
│   │   └── friends.html          # Найзууд
│   ├── account/
│   │   ├── profile.html          # Профайл
│   │   └── settings.html         # Тохиргоо
│   ├── shop/
│   │   └── index.html            # Дэлгүүр
│   ├── inventory/
│   │   └── index.html            # Инвентар
│   ├── admin/                    # Админ панелын хуудаснууд
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── questions.html
│   │   ├── categories.html
│   │   ├── shop.html
│   │   ├── achievements.html
│   │   └── notifications.html
│   └── errors/
│       ├── 404.html
│       └── 500.html
├── translations/                 # Flask-Babel орчуулгын файлууд
│   └── mn/
│       └── LC_MESSAGES/
│           ├── messages.po       # Орчуулгын эх файл
│           └── messages.mo       # Compile хийсэн файл
├── config.py                     # Тохиргооны файл
├── run.py                        # Вэб серверийг ажиллуулах
├── requirements.txt              # Python сангууд
├── babel.cfg                     # Babel тохиргоо
├── Dockerfile                    # Docker контейнер тохиргоо
├── docker-compose.yml            # Docker Compose тохиргоо
└── README.md                     # Энэ файл
```

---

## 🤖 Discord Bot командууд

| Команд | Тайлбар | Эрх |
|--------|----------|-----|
| `/profile [user]` | Профайл харах | Хүн бүр |
| `/daily` | Өдрийн шагнал авах | Хүн бүр |
| `/spin` | Fortune Wheel эргүүлэх | Хүн бүр |
| `/shop` | Дэлгүүр үзэх | Хүн бүр |
| `/buy <item_id>` | Бараа худалдаж авах | Хүн бүр |
| `/inventory` | Инвентар харах | Хүн бүр |
| `/equip <item_id>` | Зүйлс equip хийх | Хүн бүр |
| `/balance` | Зоосны үлдэгдэл харах | Хүн бүр |
| `/leaderboard [period]` | Тэргүүлэгчдийг харах | Хүн бүр |
| `/create-room <name>` | Өрөө үүсгэх | Хүн бүр |
| `/join-room <code>` | Өрөөнд нэгдэх | Хүн бүр |
| `/trivia [category]` | Ганцаарчилсан асуулт | Хүн бүр |
| `/rank [user]` | Түвшин, XP харах | Хүн бүр |
| `/top` | Топ тоглогчид | Хүн бүр |
| `/add-friend <username>` | Найзлах хүсэлт илгээх | Хүн бүр |
| `/premium` | Premium статус харах | Хүн бүр |
| `/attack` | World Boss руу дайрах | Хүн бүр |
| `/add-xp <user> <amount>` | XP нэмэх | Админ |
| `/sync-roles` | Бүх роль синк хийх | Админ |

---

## 🧪 Хөгжүүлэлтийн төлөв

Төсөл идэвхтэй хөгжүүлэлтийн шатандаа байгаа.  
Одоогоор дараах боломжуудыг нэмэхээр төлөвлөж байна:

- [ ] Улирлын тэмцээн, тусгай арга хэмжээ
- [ ] Гар утасны PWA апп
- [ ] Илүү дэлгэрэнгүй аналитик, тайлан
- [ ] WebSocket-оор дамжуулан амьд spectator mode
- [ ] Групп (Guild) систем
- [ ] Marketplace (хэрэглэгчдийн хооронд бараа зарах)

---

## 📄 Лиценз

Энэ төслийг MIT лицензийн дагуу түгээдэг. Дэлгэрэнгүйг `LICENSE` файлаас үзнэ үү.

---

## 🤝 Холбоо барих

- Discord: [TriviaVerse Server]()
- GitHub: [github.com/yourusername/triviaverse](https://github.com/ZERO1zx1/trivia-quiz-V1)

---

© 2026 TriviaVerse. Бүх эрх хуулиар хамгаалагдсан.
