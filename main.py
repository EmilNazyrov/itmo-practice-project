from flask import Flask, render_template
from db.connection import get_db_connection
from db.seed_data import seed
import plotly.graph_objs as go
import plotly
import json
# import os
import logging


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


app = Flask(__name__)


def get_sessions_by_version():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            pps.business_dt,
            pps.app_version,
            COUNT(DISTINCT pps.session_id) as session_cnt
        FROM program_product_session pps
        GROUP BY 1, 2
        ORDER BY 1
    ''')
    rows = cursor.fetchall()
    conn.close()

    # Группируем по версии
    version_data = {}
    for row in rows:
        version = row['app_version']
        dt = row['business_dt']
        count = row['session_cnt']
        version_data.setdefault(version, {}).setdefault(dt, 0)
        version_data[version][dt] += count

    # Получаем уникальные даты
    dates = sorted({dt for version in version_data.values() for dt in version.keys()})

    # Создаём traces по версиям
    traces = []
    for version, data in version_data.items():
        y_values = [data.get(dt, 0) for dt in dates]
        traces.append(go.Bar(x=dates, y=y_values, name=f'v{version}'))

    layout = go.Layout(
        title='Сессии по дням в разбивке по версии приложения',
        barmode='stack',
        xaxis=dict(title='Дата'),
        yaxis=dict(title='Кол-во сессий')
    )

    return go.Figure(data=traces, layout=layout)


def get_transaction_sums():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            DATE(ftr.transaction_dttm) as dt,
            SUM(ftr.transaction_amt) as total
        FROM financial_transaction ftr
        GROUP BY 1
        ORDER BY 1
    ''')
    rows = cursor.fetchall()
    conn.close()

    x = [row['dt'] for row in rows]
    y = [row['total'] for row in rows]

    fig = go.Figure(data=[go.Bar(x=x, y=y)])
    fig.update_layout(
        title='Сумма транзакций по дням',
        xaxis_title='Дата',
        yaxis_title='Сумма'
    )
    return fig


def get_tasks_by_type():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT
            DATE(del.task_create_dttm) as dt,
            del.task_type_code,
            COUNT(DISTINCT del.meeting_id) as cnt
        FROM orig_delivery del
        GROUP BY 1, 2
        ORDER BY 1
    ''')
    rows = cursor.fetchall()
    conn.close()

    type_data = {}
    for row in rows:
        code = row['task_type_code']
        dt = row['dt']
        cnt = row['cnt']
        type_data.setdefault(code, {}).setdefault(dt, 0)
        type_data[code][dt] += cnt

    all_dates = sorted({dt for type_dict in type_data.values() for dt in type_dict})

    traces = []
    for code, data in type_data.items():
        y_values = [data.get(dt, 0) for dt in all_dates]
        traces.append(go.Scatter(x=all_dates, y=y_values, mode='lines+markers', name=code))

    layout = go.Layout(
        title='Количество задач по дням в разбивке по типу задачи',
        xaxis=dict(title='Дата'),
        yaxis=dict(title='Кол-во задач')
    )

    return go.Figure(data=traces, layout=layout)


@app.route('/seed')
def seed_route():
    seed()
    return 'Data loaded successfully'


@app.route('/')
def home():
    logger.info('Processing request to home page')
    fig1 = get_sessions_by_version()
    fig2 = get_transaction_sums()
    fig3 = get_tasks_by_type()

    return render_template('index.html',
                           graph1=json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder),
                           graph2=json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder),
                           graph3=json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder))


# def is_db_empty():
#     conn = get_db_connection()
#     cursor = conn.cursor()
#     cursor.execute("SELECT COUNT(*) FROM client_x_account")
#     count = cursor.fetchone()[0]
#     conn.close()
#     return count == 0


# if __name__ == '__main__':
#     if not os.path.exists('my_database.db'):  # Путь к базе данных
#         logger.info('Файл базы данных не найден, создаем и заполняем...')
#         seed()
#     elif is_db_empty():
#         logger.info('База пуста — заполняем seed-данными...')
#         seed()
#     else:
#         logger.info('База уже содержит данные, пропускаем seed')
#     app.run(debug=True)

if __name__ == '__main__':
    logger.info('Filling the database with synthetic data...')
    seed()  # Инициализация базы при запуске
    logger.info('Launching Flask application...')
    app.run(debug=True)
