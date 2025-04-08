from flask import Flask, render_template_string
import sqlite3
import random
from datetime import datetime, timedelta


# Генератор случайных номеров телефона
def generate_phone():
    return '+79' + ''.join(random.choices('0123456789', k=9))

# Создаем подключение к базе данных (файл my_database.db будет создан)
connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()
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
    client_id INTEGER UNIQUE NOT NULL,
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
    client_id INTEGER NOT NULL,
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
    client_id INTEGER NOT NULL,
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

time = datetime.now()
names = ['Alexander Petrov', 'Fedor Ivanov', 'Vasiliy Frolov', 'Alice Ivanova', 'Boris Petrov', 'Svetlana Orlova', 'Ivan Smirnov', 'Elena Volkova']
genders = ['M', 'M', 'M', 'F', 'M', 'F', 'M', 'F']
client_ids = [1001 + i for i in range(len(names))]
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





cursor.execute("SELECT COUNT(client_id), strftime ('%D',timestamp) FROM Authorizations GROUP BY 2")

data = cursor.fetchall()

# Сохраняем изменения и закрываем соединение
connection.commit()

connection.close()

app = Flask(__name__)


# Normally you'd have this in the templates directory but for simplicity of
# putting everything into one file for an example, I'm using a template string

template = """
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

<div id="plot_div" style="width: 100%; height: 100%"></div>

<script type="text/javascript">

var trace1 = {
    x: {{ plot_data.x_axis }},
    y: {{ plot_data.y_axis }},
    type: 'scatter',
    name: 'Example'
};

var layout = {
    title: "Test",
    titlefont: {
            family: 'Poppins',
            size: 18,
            color: '#7f7f7f'
        },
    showlegend: true,
    xaxis: {
        title: 'Axis Unit',
    },
    yaxis: {
        title: 'Other Axis Unit',
    },
    margin: {
        l: 70,
        r: 40,
        b: 50,
        t: 50,
        pad: 4
    }
};
var data = [trace1];

Plotly.newPlot("plot_div", data, layout);

</script>
"""

def get_plot_data():
    x = list(range(10))
    y = [random.randint(0, 100) for i in range(10)]
    return {'x_axis': x, 'y_axis': y}

@app.route('/')
def home():
    plot_data = get_plot_data()
    return render_template_string(template,
                                  plot_data=plot_data)

if __name__ == '__main__':
    app.run()
