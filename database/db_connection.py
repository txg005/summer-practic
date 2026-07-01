import sqlite3


class Database:
    """Подключение к SQLite и создание схемы таблиц"""

    def __init__(self, db_path: str = 'car_rental.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER NOT NULL,
                license_plate TEXT UNIQUE NOT NULL,
                daily_rate REAL NOT NULL,
                status TEXT DEFAULT 'доступен',
                last_maintenance DATE
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                driver_license TEXT UNIQUE NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rentals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                client_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                total_cost REAL NOT NULL,
                status TEXT DEFAULT 'активная',
                FOREIGN KEY (car_id) REFERENCES cars (id),
                FOREIGN KEY (client_id) REFERENCES clients (id)
            )
        ''')

        self.conn.commit()

    def close(self):
        self.conn.close()