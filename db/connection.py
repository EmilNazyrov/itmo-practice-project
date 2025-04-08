import sqlite3


def get_db_connection():
    connection = sqlite3.connect('my_database.db')
    connection.row_factory = sqlite3.Row  # Чтобы работать с именованными полями
    return connection
