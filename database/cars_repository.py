from typing import List, Optional

from .models import Car


class CarsRepository:
    """Доступ к таблице cars"""

    def __init__(self, db):
        self.db = db

    def get_all(self) -> List[Car]:
        self.db.cursor.execute('SELECT * FROM cars ORDER BY id')
        return [Car(*row) for row in self.db.cursor.fetchall()]

    def get_by_id(self, car_id: int) -> Optional[Car]:
        self.db.cursor.execute('SELECT * FROM cars WHERE id=?', (car_id,))
        row = self.db.cursor.fetchone()
        return Car(*row) if row else None

    def get_available(self) -> List[Car]:
        self.db.cursor.execute('SELECT * FROM cars WHERE status="доступен"')
        return [Car(*row) for row in self.db.cursor.fetchall()]

    def insert(self, car: Car) -> int:
        self.db.cursor.execute('''
            INSERT INTO cars (brand, model, year, license_plate, daily_rate, status, last_maintenance)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (car.brand, car.model, car.year, car.license_plate,
              car.daily_rate, car.status, car.last_maintenance))
        self.db.conn.commit()
        return self.db.cursor.lastrowid

    def update(self, car: Car) -> None:
        self.db.cursor.execute('''
            UPDATE cars SET brand=?, model=?, year=?, license_plate=?, daily_rate=?, status=?, last_maintenance=?
            WHERE id=?
        ''', (car.brand, car.model, car.year, car.license_plate,
              car.daily_rate, car.status, car.last_maintenance, car.id))
        self.db.conn.commit()

    def delete(self, car_id: int) -> None:
        self.db.cursor.execute('DELETE FROM cars WHERE id=?', (car_id,))
        self.db.conn.commit()

    def update_status(self, car_id: int, status: str) -> None:
        self.db.cursor.execute('UPDATE cars SET status=? WHERE id=?', (status, car_id))
        self.db.conn.commit()

    def mark_maintenance(self, car_id: int, date_str: str) -> None:
        """Отметка о техническом обслуживании"""
        self.db.cursor.execute('''
            UPDATE cars SET status='на ТО', last_maintenance=?
            WHERE id=?
        ''', (date_str, car_id))
        self.db.conn.commit()

    def search(self, brand: str = '', model: str = '', license_plate: str = '',
               status: str = '', year: str = '', rate: str = '') -> List[Car]:
        query = 'SELECT * FROM cars WHERE 1=1'
        params = []

        if brand:
            query += ' AND brand LIKE ?'
            params.append(f'%{brand}%')
        if model:
            query += ' AND model LIKE ?'
            params.append(f'%{model}%')
        if license_plate:
            query += ' AND license_plate LIKE ?'
            params.append(f'%{license_plate}%')
        if status and status != 'все':
            query += ' AND status = ?'
            params.append(status)

        # Обработка диапазонов для года
        if year:
            if '-' in year:  # Диапазон 2018-2020
                start_year, end_year = year.split('-')
                query += ' AND year BETWEEN ? AND ?'
                params.extend([int(start_year), int(end_year)])
            elif year.startswith('>'):  # >2019
                query += ' AND year > ?'
                params.append(int(year[1:]))
            elif year.startswith('<'):  # <2020
                query += ' AND year < ?'
                params.append(int(year[1:]))
            else:  # Точное значение
                query += ' AND year = ?'
                params.append(int(year))

        # Обработка диапазонов для цены
        if rate:
            if '-' in rate:  # Диапазон 100-200
                start_rate, end_rate = rate.split('-')
                query += ' AND daily_rate BETWEEN ? AND ?'
                params.extend([float(start_rate), float(end_rate)])
            elif rate.startswith('>'):  # >150
                query += ' AND daily_rate > ?'
                params.append(float(rate[1:]))
            elif rate.startswith('<'):  # <200
                query += ' AND daily_rate < ?'
                params.append(float(rate[1:]))
            else:  # Точное значение
                query += ' AND daily_rate = ?'
                params.append(float(rate))

        self.db.cursor.execute(query, params)
        return [Car(*row) for row in self.db.cursor.fetchall()]

    def filter_available(self, text: str) -> List[Car]:
        """Используется для автодополнения в комбобоксе аренды"""
        self.db.cursor.execute('''
            SELECT * FROM cars
            WHERE status="доступен" AND
            (LOWER(brand || ' ' || model || ' ' || license_plate) LIKE ?)
        ''', (f'%{text.lower()}%',))
        return [Car(*row) for row in self.db.cursor.fetchall()]
    
    def filter_all(self, text: str) -> List[Car]:
        self.db.cursor.execute('''
            SELECT * FROM cars
            WHERE LOWER(brand || ' ' || model || ' ' || license_plate) LIKE ?
        ''', (f'%{text.lower()}%',))
        return [Car(*row) for row in self.db.cursor.fetchall()]