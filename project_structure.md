# 📂 TriviaVerse V1 Project Structure

Төслийн үндсэн хавтас болон файлын бүтэц. Энэхүү төсөл нь **Flask** (Вэб) болон **Discord.py** (Бот) дээр суурилсан систем юм.

## 🏗️ Үндсэн бүтэц

```text
trivia-quiz-V1/
├── app/                    # 🌐 Flask Application (Үндсэн логик)
│   ├── models/             # 📊 Өгөгдлийн сангийн моделиуд (User, Post, Chat, etc.)
│   ├── routes/             # 🛣️ Вэб чиглүүлэлтүүд (Blueprints)
│   ├── sockets/            # 🔌 WebSocket үйл явдлууд (Chat, Room, Notifications)
│   ├── static/             # 📁 Статик файлууд (CSS, JS, Images)
│   ├── utils/              # 🛠️ Туслах функцууд (Email, Notify, Admin)
│   ├── extensions.py       # 🔌 Flask өргөтгөлүүдийн тохиргоо (DB, SocketIO, Login)
│   └── __init__.py         # 🚀 Апп эхлүүлэх ба Blueprint бүртгэл
├── discord_bot/            # 🤖 Discord Bot-ын эх код
│   ├── cogs/               # ⚙️ Ботын модулиуд (Guild, Marketplace, Tournament)
│   └── bot.py              # 🔌 Ботын үндсэн файл
├── templates/              # 🎨 HTML темплэйтүүд (Jinja2)
│   ├── account/            # Хэрэглэгчийн тохиргоо, профайл
│   ├── admin/              # Админ удирдлагын хэсэг
│   ├── auth/               # Нэвтрэх, бүртгүүлэх, 2FA
│   ├── chat/               # Глобал чат
│   ├── community/          # Форум, пост, хавчуурга
│   ├── guild/              # Гильдийн систем
│   ├── layouts/            # Үндсэн бүтэц (base.html)
│   ├── marketplace/        # Зах зээлийн систем
│   └── quiz/               # Тоглоомын хэсэг (Solo, Multiplayer)
├── static/                 # 🖼️ Нийтийн статик файлууд
│   ├── css/                # Style sheets (design-system, app, animations)
│   ├── js/                 # Client-side скриптүүд (socket.js, chat.js, app.js)
│   └── avatars/            # Хэрэглэгчийн аватарууд
├── migrations/             # 📦 Өгөгдлийн сангийн шилжилтүүд (Alembic)
├── logs/                   # 📝 Системийн логууд
├── config.py               # ⚙️ Аппликейшны тохиргоо
├── run.py                  # 🚀 Вэб серверийг ажиллуулах файл
├── requirements.txt        # 📦 Шаардлагатай сангуудын жагсаалт
├── .env.example            # 🔑 Орчны хувьсагчдын жишээ
├── README.md               # 📖 Төслийн танилцуулга
└── DOCUMENTATION.md        # 📚 Техникийн дэлгэрэнгүй баримт бичиг
```

## 📂 Хавтас бүрийн тайлбар

| Хавтас / Файл | Тайлбар |
| :--- | :--- |
| `app/routes/` | Вэб хуудсуудын логик болон API endpoint-ууд байрлана. |
| `app/models/` | SQLAlchemy ашиглан тодорхойлсон өгөгдлийн сангийн хүснэгтүүд. |
| `app/sockets/` | Socket.IO ашиглан бодит хугацааны (Real-time) чат, тоглоомын өрөөний үйлдлүүд. |
| `templates/layouts/` | Бүх хуудасны үндсэн загвар болох `base.html` энд байрлана. |
| `static/js/` | Чат, мэдэгдэл, тоглоомын логикийг удирдаж буй JavaScript файлууд. |
| `discord_bot/` | Вэб системтэй нэгдсэн Discord ботын функцууд. |
| `run.py` | Аппликейшныг ажиллуулах үндсэн цэг. |

---
*Бэлтгэсэн: Manus AI*
