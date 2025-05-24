from flask import Flask, render_template, jsonify, request
from db.connection import get_db_connection
from db.seed_data import seed
import plotly.graph_objs as go
import plotly
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')


def get_sessions_by_version(version_filter=None, date_from=None, date_to=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = '''
        SELECT
            pps.business_dt as dt,
            pps.app_version,
            COUNT(DISTINCT pps.session_id) as session_cnt
        FROM program_product_session pps
        WHERE 1 = 1
    '''

    params = []
    if version_filter:
        query += " AND pps.app_version = ?"
        params.append(version_filter)
    if date_from:
        query += " AND pps.business_dt >= ?"
        params.append(date_from)
    if date_to:
        query += " AND pps.business_dt < ?"
        params.append(date_to)

    query += " GROUP BY 1, 2 ORDER BY 1"
    cursor.execute(query, params)

    rows = cursor.fetchall()
    conn.close()

    # Группировка по версиям и создание traces
    version_data = {}
    for row in rows:
        ver = row['app_version']
        dt = row['dt']
        count = row['session_cnt']
        version_data.setdefault(ver, {}).setdefault(dt, 0)
        version_data[ver][dt] += count

    dates = sorted({dt for ver in version_data.values() for dt in ver.keys()})

    traces = []
    for ver, data in version_data.items():
        y_values = [data.get(dt, 0) for dt in dates]
        traces.append(go.Bar(
            x=dates,
            y=y_values,
            name=f'v{ver}',
            hovertemplate='Дата: %{x}<br>Сессий: %{y}<br>Версия: %{meta}',
            meta=[str(ver)] * len(dates)
        ))

    layout = go.Layout(
        title='Сессии по дням в разбивке по версии приложения',
        barmode='stack',
        xaxis=dict(title='Дата'),
        yaxis=dict(title='Кол-во сессий'),
        width=1024
    )

    return go.Figure(data=traces, layout=layout)


def get_transaction_sums(date_from=None, date_to=None, alpha=0.2):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
            SELECT
                DATE(ftr.transaction_dttm) as dt,
                SUM(ftr.transaction_amt) as total
            FROM financial_transaction ftr
            WHERE 1 = 1
        """

    params = []
    if date_from:
        query += " AND ftr.transaction_dttm >= ?"
        params.append(date_from)
    if date_to:
        query += " AND ftr.transaction_dttm < ?"
        params.append(date_to)

    query += " GROUP BY 1 ORDER BY 1"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    x = [row['dt'] for row in rows]
    y = [row['total'] for row in rows]

    # Расчет EMA вручную
    ema = []
    for i, val in enumerate(y):
        if i == 0:
            ema.append(val)
        else:
            ema_val = alpha * val + (1 - alpha) * ema[-1]
            ema.append(ema_val)

    # Создаем график
    fig = go.Figure()

    fig.add_trace(go.Bar(x=x, y=y, name='Сумма транзакций'))
    fig.add_trace(go.Scatter(x=x, y=ema, mode='lines', name=f'EMA (скользящее среднее)'))

    fig.update_layout(
        title='Сумма транзакций по дням',
        xaxis_title='Дата',
        yaxis_title='Сумма',
        hovermode='x unified',
        barmode='overlay',
        width=1024
    )
    return fig


def get_tasks_by_type(task_type=None, date_from=None, date_to=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
            SELECT
                DATE(del.task_create_dttm) as dt,
                del.task_type_code,
                COUNT(DISTINCT del.meeting_id) as cnt
            FROM orig_delivery del
            WHERE 1 = 1
        """

    params = []
    if task_type:
        query += " AND del.task_type_code = ?"
        params.append(task_type)
    if date_from:
        query += " AND del.task_create_dttm >= ?"
        params.append(date_from)
    if date_to:
        query += " AND del.task_create_dttm < ?"
        params.append(date_to)

    query += " GROUP BY 1, 2 ORDER BY 1"

    cursor.execute(query, params)
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
        traces.append(go.Scatter(
            x=all_dates,
            y=y_values,
            mode='lines+markers',
            name=code,
            hovertemplate='Дата: %{x}<br>Задач: %{y}<br>Тип: %{meta}',
            meta=[code] * len(all_dates)
        ))

    layout = go.Layout(
        title='Количество задач по дням в разбивке по типу задачи',
        xaxis=dict(title='Дата'),
        yaxis=dict(title='Кол-во задач'),
        width=1024
    )

    return go.Figure(data=traces, layout=layout)


def get_filter_options():
    conn = get_db_connection()
    cursor = conn.cursor()
    versions = [row[0] for row in cursor.execute('''
                                            SELECT DISTINCT pps.app_version
                                            FROM program_product_session pps
                                            ORDER BY pps.app_version
                                        ''').fetchall()]
    task_types = [row[0] for row in cursor.execute('''
                                            SELECT DISTINCT del.task_type_code
                                            FROM orig_delivery del
                                            ORDER BY del.task_type_code
                                        ''').fetchall()]
    conn.close()
    return versions, task_types


@app.route('/seed')
def seed_route():
    seed()
    return "База данных перегенерирована!"


@app.route('/get_versions')
def get_versions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT app_version FROM program_product_session")
    versions = [row['app_version'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(versions)


@app.route('/get_task_types')
def get_task_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT task_type_code FROM orig_delivery")
    task_types = [row['task_type_code'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(task_types)


@app.route('/')
def home():
    logger.info('Processing request to home page')

    version_filter = request.args.get('version')
    task_type_filter = request.args.get('task_type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')

    fig1 = get_sessions_by_version(version_filter, date_from, date_to)
    fig2 = get_transaction_sums(date_from, date_to)
    fig3 = get_tasks_by_type(task_type_filter, date_from, date_to)

    # Получаем список версий и типов задач
    versions, task_types = get_filter_options()

    return render_template('index.html',
                           graph1=json.dumps(fig1, cls=plotly.utils.PlotlyJSONEncoder),
                           graph2=json.dumps(fig2, cls=plotly.utils.PlotlyJSONEncoder),
                           graph3=json.dumps(fig3, cls=plotly.utils.PlotlyJSONEncoder),
                           versions=versions,
                           task_types=task_types,
                           selected_version=version_filter,
                           selected_task_type=task_type_filter,
                           selected_date_from=date_from,
                           selected_date_to=date_to)


if __name__ == '__main__':
    logger.info('Filling the database with synthetic data...')
    seed()  # Инициализация базы при запуске
    logger.info('Launching Flask application...')
    app.run(debug=True)
