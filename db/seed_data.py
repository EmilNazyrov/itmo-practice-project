import random
# import sqlite3
import uuid
from faker import Faker
from datetime import datetime, timedelta
from .connection import get_db_connection  # Подключение из connection.py
import logging


logger = logging.getLogger(__name__)

fake = Faker()
now = datetime.now()

# conn = sqlite3.connect('my_database.db')
# cursor = conn.cursor()


def generate_phone():
    return '+79' + ''.join(random.choices('0123456789', k=9))


def seed():
    logger.info("Начинаем генерацию данных...")

    conn = get_db_connection()
    cursor = conn.cursor()

    logger.info("Удаляем старые таблицы...")
    cursor.executescript('''
        DROP TABLE IF EXISTS client_x_account;
        DROP TABLE IF EXISTS program_product_session;
        DROP TABLE IF EXISTS orig_delivery;
        DROP TABLE IF EXISTS financial_transaction;
    ''')

    logger.info("Создаём таблицы...")
    # Таблица client_x_account
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS client_x_account (
        account_id TEXT PRIMARY KEY,
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
    CREATE TABLE IF NOT EXISTS program_product_session (
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
    CREATE TABLE IF NOT EXISTS orig_delivery (
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
    CREATE TABLE IF NOT EXISTS financial_transaction (
        transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT NOT NULL,
        transaction_amt REAL,
        transaction_dttm DATETIME,
        transaction_status_code TEXT,
        currency_code TEXT,
        rejected_flg BOOLEAN DEFAULT 0,
        FOREIGN KEY (account_id) REFERENCES client_x_account(account_id)
    )
    ''')

    # Генерация клиентов и аккаунтов
    names = [fake.name() for _ in range(200)]
    genders = [random.choice(['M', 'F']) for _ in names]
    client_ids = [str(uuid.uuid4()) for _ in names]
    account_ids = []

    start_date = datetime(2025, 2, 5)
    end_date = datetime(2025, 5, 5)
    days_range = (end_date - start_date).days + 1
    dates = [start_date + timedelta(days=i) for i in range(days_range)]

    for i in range(len(client_ids)):
        account_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO client_x_account (account_id, client_id, phone_no, name, gender_cd, created_dttm)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            account_id,
            client_ids[i],
            generate_phone(),
            names[i],
            genders[i],
            start_date - timedelta(days=random.randint(0, 180))
        ))
        account_ids.append(account_id)

    # Генерация сессий (DAU + смена версий)
    base_dau = 1024  # Среднее количество пользователей в день

    for dt in dates:
        dau = int(base_dau * random.uniform(0.9, 1.1))

        if dt.date() == datetime(2025, 3, 14).date():
            dau = int(dau * 1.2)  # Всплеск на релизе версии 3.14

        if dt < datetime(2025, 3, 14):
            versions = [1.618] * (dau // 2) + [2.72] * (dau - dau // 2)
        elif dt < datetime(2025, 4, 18):
            v3 = int(dau * 0.4)
            v1 = int((dau - v3) * 0.5)
            v2 = dau - v3 - v1
            versions = [3.14] * v3 + [1.618] * v1 + [2.72] * v2
        else:
            v5 = int(dau * 0.3)
            v3 = int(dau * 0.3)
            v1 = int(dau * 0.2)
            v2 = dau - v5 - v3 - v1
            versions = [5.55] * v5 + [3.14] * v3 + [1.618] * v1 + [2.72] * v2

        random.shuffle(versions)

        for version in versions:
            cursor.execute('''
                INSERT INTO program_product_session (client_id, business_dt, os_type_code, app_version)
                VALUES (?, ?, ?, ?)
            ''', (
                random.choice(client_ids),
                dt.date(),
                random.choice(['iOS', 'Android']),
                version
            ))

    # orig_delivery (по 16 задач на клиента)
    # Динамическое распределение задач по дням
    task_types = {
        "Debit Card": 128,
        "Installation": 64,
        "Agent Visit": 16
    }

    for dt in dates:
        weekday = dt.weekday()
        seasonality_multiplier = 0.6 if weekday >= 5 else 1.0  # Меньше задач по выходным

        for task_type, base_count in task_types.items():
            fluctuation = random.uniform(0.7, 1.3)
            task_count = int(base_count * fluctuation * seasonality_multiplier)

            for _ in range(task_count):
                client_id = random.choice(client_ids)
                hour = random.randint(8, 18)  # С 8 утра до 7 вечера
                minute = random.randint(0, 59)
                start_time = datetime.combine(dt, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
                end_time = start_time + timedelta(minutes=random.randint(10, 60))

                cursor.execute('''
                    INSERT INTO orig_delivery (
                        client_id, task_type_code, task_status_code, task_success_flg, 
                        task_create_dttm, meeting_start_dttm
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    client_id,
                    task_type,
                    random.choice(['Done', 'Pending', 'Cancelled']),
                    random.choice([0, 1]),
                    start_time,
                    end_time
                ))

    holiday_boost_dates = {
        datetime(2025, 2, 14).date(),
        datetime(2025, 2, 23).date(),
        datetime(2025, 3, 8).date(),
        datetime(2025, 5, 1).date(),
    }

    # financial_transaction (по 64 транзакций на аккаунт)
    for account_id in account_ids:
        for _ in range(64):
            tx_date = (now - timedelta(days=random.randint(0, 105))).date()
            # tx_date = start_date + timedelta(days=random.randint(0, days_range - 1))
            base_amt = round(random.uniform(100, 5000), 2)
            boost_multiplier = 1.5 if tx_date in holiday_boost_dates else 1.0
            amount = round(base_amt * boost_multiplier, 2)
        # tx_date = start_date + timedelta(days=i)
        # for _ in range(random.randint(1, 5)):  # Несколько транзакций в день
        #     base_amt = round(random.uniform(100, 5000), 2)
        #     boost_multiplier = 1.5 if tx_date in holiday_boost_dates else 1.0
        #     amount = round(base_amt * boost_multiplier, 2)

            cursor.execute('''
                            INSERT INTO financial_transaction (
                                account_id, transaction_amt, transaction_dttm,
                                transaction_status_code, currency_code, rejected_flg
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        ''', (
                account_id,
                amount,
                datetime.combine(tx_date, datetime.min.time()) + timedelta(
                    hours=random.randint(8, 23), minutes=random.randint(0, 59)
                ),
                random.choice(['Success', 'Pending', 'Failed']),
                random.choice(['RUB', 'USD', 'EUR', 'KZT']),
                random.choice([0, 1])
            ))

    # Индексы
    cursor.executescript('''
        CREATE INDEX IF NOT EXISTS idx_client_id ON client_x_account(client_id);
        CREATE INDEX IF NOT EXISTS idx_pps_client_id ON program_product_session(client_id);
        CREATE INDEX IF NOT EXISTS idx_pps_business_dt ON program_product_session(business_dt);
        CREATE INDEX IF NOT EXISTS idx_od_client_id ON orig_delivery(client_id);
        CREATE INDEX IF NOT EXISTS idx_ft_account_id ON financial_transaction(account_id);
        CREATE INDEX IF NOT EXISTS idx_ft_dttm ON financial_transaction(transaction_dttm);
    ''')

    conn.commit()
    conn.close()
    logger.info("Генерация данных завершена.")
