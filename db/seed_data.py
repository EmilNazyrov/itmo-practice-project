import random
import uuid
from datetime import datetime, timedelta
from .connection import get_db_connection  # Подключение из connection.py


# Генератор случайных номеров телефона
def generate_phone():
    return '+79' + ''.join(random.choices('0123456789', k=9))


def seed():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.executescript('''
        DROP TABLE IF EXISTS client_x_account;
        DROP TABLE IF EXISTS program_product_session;
        DROP TABLE IF EXISTS orig_delivery;
        DROP TABLE IF EXISTS financial_transaction;
    ''')

    # Таблица client_x_account
    cursor.execute('''
    CREATE TABLE client_x_account (
        account_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT UNIQUE NOT NULL,
        phone_no TEXT,
        name TEXT,
        gender_cd TEXT,
        created_dttm DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_flg BOOLEAN DEFAULT 0
    )
    ''')

    # Таблица program_product_session
    cursor.execute('''
    CREATE TABLE program_product_session (
        session_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        business_dt DATE,
        os_type_code TEXT,
        app_version REAL,
        FOREIGN KEY (client_id) REFERENCES client_x_account(client_id)
    )
    ''')

    # Таблица orig_delivery
    cursor.execute('''
    CREATE TABLE orig_delivery (
        meeting_id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_id TEXT NOT NULL,
        task_type_code TEXT,
        task_status_code TEXT,
        task_success_flg BOOLEAN,
        task_create_dttm DATETIME,
        meeting_start_dttm DATETIME,
        FOREIGN KEY (client_id) REFERENCES client_x_account(client_id)
    )
    ''')

    # Таблица financial_transaction
    cursor.execute('''
    CREATE TABLE financial_transaction (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER NOT NULL,
        transaction_amt REAL,
        transaction_dttm DATETIME,
        transaction_status_code TEXT,
        currency_code TEXT,
        rejected_flg BOOLEAN DEFAULT 0,
        FOREIGN KEY (account_id) REFERENCES client_x_account(account_id)
    )
    ''')

    names = ['Alexander Petrov', 'Fedor Ivanov', 'Vasiliy Frolov', 'Alice Ivanova', 'Boris Petrov', 'Svetlana Orlova', 'Ivan Smirnov', 'Elena Volkova']
    genders = ['M', 'M', 'M', 'F', 'M', 'F', 'M', 'F']
    # client_ids = [1001 + i for i in range(len(names))]
    client_ids = []
    for _ in range(len(names)):
        client_id = str(uuid.uuid4())  # UUID как строка
        client_ids.append(client_id)

    now = datetime.now()

    # client_x_account
    account_ids = []
    for i in range(len(client_ids)):
        cursor.execute('''
            INSERT INTO client_x_account (client_id, phone_no, name, gender_cd, created_dttm)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            client_ids[i],
            generate_phone(),
            names[i],
            genders[i],
            now - timedelta(days=random.randint(0, 365))
        ))
        account_ids.append(cursor.lastrowid)

    # program_product_session (по 128 сессий на клиента)
    for client_id in client_ids:
        for _ in range(128):
            cursor.execute('''
                INSERT INTO program_product_session (client_id, business_dt, os_type_code, app_version)
                VALUES (?, ?, ?, ?)
            ''', (
                client_id,
                (now - timedelta(days=random.randint(0, 60))).date(),
                random.choice(['iOS', 'Android']),
                random.choice([1.618, 2.72, 3.14, 5.55])
            ))

    # orig_delivery (по 16 задач на клиента)
    for client_id in client_ids:
        for _ in range(16):
            start_time = now - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 60))
            cursor.execute('''
                INSERT INTO orig_delivery (
                    client_id, task_type_code, task_status_code, task_success_flg, 
                    task_create_dttm, meeting_start_dttm
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                client_id,
                random.choice(['Debit Card', 'Installation', 'Agent Visit']),
                random.choice(['Done', 'Pending', 'Cancelled']),
                random.choice([0, 1]),
                start_time,
                start_time + timedelta(minutes=random.randint(10, 60))
            ))

    # financial_transaction (по 64 транзакций на аккаунт)
    for account_id in account_ids:
        for _ in range(64):
            cursor.execute('''
                INSERT INTO financial_transaction (
                    account_id, transaction_amt, transaction_dttm,
                    transaction_status_code, currency_code, rejected_flg
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                account_id,
                round(random.uniform(100, 5000), 2),
                now - timedelta(days=random.randint(0, 90)),
                random.choice(['Success', 'Pending', 'Failed']),
                random.choice(['RUB', 'USD', 'EUR', 'KZT']),
                random.choice([0, 1])
            ))

    conn.commit()
    conn.close()
