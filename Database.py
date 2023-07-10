import sqlite3

class Database:
    def create_table(self, database_name, table_name, columns):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name}({columns})')
        print('Created table: ' + str(table_name))
        conn.commit()

    def is_exist(self, database_name, table_name, columns):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table_name} WHERE {columns}')

        if cursor.fetchone() == None:
            return False
        else:
            return True

    def fetch_all(self, database_name, table_name):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table_name}')
        return cursor.fetchall()

    def filter_data(self, database_name, table_name, query):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table_name} WHERE {query}')
        return cursor.fetchall()

    def search_data(self, database_name, table_name, query):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'SELECT * FROM {table_name} WHERE {query}')
        return cursor.fetchone()

    def insert_data(self, database_name, table_name, columns, setting, data):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'INSERT INTO {table_name} VALUES({columns}) {setting}', data)
        conn.commit()

    def delete_data(self, database_name, table_name, columns):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table_name} WHERE {columns}')
        print('Deleted data: ' + str(columns))
        conn.commit()

    def update_data(self, database_name, table_name, columns):
        conn = sqlite3.connect(f'{database_name}.db')
        cursor = conn.cursor()
        cursor.execute(f'UPDATE {table_name} {columns}')
        print('Updated data: ' + str(columns))
        conn.commit()