import sqlite3
import os

DB_PATH = 'instance/triviaverse.db'  # Хэрэв зам өөр бол засаарай

def get_existing_columns(conn):
    cursor = conn.execute("PRAGMA table_info(users)")
    return {row[1] for row in cursor.fetchall()}

def add_column(conn, col_name, col_type, default=None):
    existing = get_existing_columns(conn)
    if col_name in existing:
        print(f"Багана '{col_name}' аль хэдийн байгаа. Алгасаж байна.")
        return
    sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
    if default is not None:
        sql += f" DEFAULT {default}"
    try:
        conn.execute(sql)
        conn.commit()
        print(f"Багана '{col_name}' амжилттай нэмэгдлээ.")
    except sqlite3.OperationalError as e:
        print(f"Алдаа: {e}")

def main():
    if not os.path.exists(DB_PATH):
        print(f"Өгөгдлийн сан олдсонгүй: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # Нэмэх шаардлагатай баганууд (model-ийнхээ дагуу тохируулна уу)
    columns = [
        ('otp_code', 'VARCHAR(10)'),
        ('otp_expiry', 'DATETIME'),
        ('last_login_ip', 'VARCHAR(45)'),
        ('last_login_at', 'DATETIME'),
        ('email_notif_security', 'INTEGER', 1),
        ('email_notif_social', 'INTEGER', 1),
        ('email_notif_promo', 'INTEGER', 1),
        ('discord_rich_presence', 'INTEGER', 1),
        ('discord_dm_notifications', 'INTEGER', 1),
        ('showcase_badge_ids', 'TEXT'),
        ('nickname_effect', 'VARCHAR(50)'),
        ('profile_theme_music', 'VARCHAR(100)'),
        ('performance_mode', 'INTEGER', 0),
        ('preferred_difficulty', 'VARCHAR(20)'),
    ]
    
    for col in columns:
        if len(col) == 2:
            name, ctype = col
            default = None
        else:
            name, ctype, default = col
        add_column(conn, name, ctype, default)
    
    conn.close()
    print("Бүх баганууд нэмэгдсэн. Одоо 'python run.py' командаар аппаа эхлүүлнэ үү.")

if __name__ == '__main__':
    main()