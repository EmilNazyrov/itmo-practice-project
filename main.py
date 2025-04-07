from flask import Flask, render_template_string
import sqlite3
import random
from datetime import datetime, timedelta

# Создаем подключение к базе данных (файл my_database.db будет создан)
connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS GraphData (
id INTEGER PRIMARY KEY,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
value REAL NOT NULL,
type INTEGER NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Meetings (
id INTEGER PRIMARY KEY,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
client_id INTEGER NOT NULL,
type INTEGER NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Clients (
id INTEGER PRIMARY KEY,
registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
name TEXT NOT NULL

)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Authorizations (
id INTEGER PRIMARY KEY,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
app_version INTEGER NOT NULL,
client_id INTEGER NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Transactions (
id INTEGER PRIMARY KEY,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
value REAL NOT NULL,
client_id INTEGER NOT NULL,
recipient_id INTEGER NOT NULL,
type INTEGER NOT NULL
)
''')

time = datetime.now()
names = ["Alexander Petrov", "Fedor Ivanov", "Vasiliy Frolov"]
app_versions = [1, 2, 3]
for i in range(len(names)):
    cursor.execute('INSERT INTO Clients (registration_date, name) VALUES (?, ?)', (time, names[i]))
cursor.execute('SELECT id FROM Clients')
ids = cursor.fetchall()
print(ids)
for i in range(200):
    time_str = (time + timedelta(i / 10, 0))
    id_index = random.randint(0, len(ids) - 1)
    app_version_id = random.randint(0, len(app_versions) - 1)
    client_id = ids[id_index][0]
    app_version = app_versions[app_version_id]
    cursor.execute('INSERT INTO Authorizations (timestamp, app_version, client_id) VALUES (?, ?, ?)', (time_str, app_version, client_id))

cursor.execute("SELECT COUNT(client_id), strftime ('%D',timestamp) FROM Authorizations GROUP BY 2")

data = cursor.fetchall()
print(data)

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