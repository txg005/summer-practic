from typing import List, Optional

from .models import Rental, RentalView


class RentalsRepository:
    """Доступ к таблице rentals и связанным отчётным запросам"""

    def __init__(self, db):
        self.db = db

    def get_all_with_details(self) -> List[RentalView]:
        self.db.cursor.execute('''
            SELECT r.id, c.brand || ' ' || c.model || ' (' || c.license_plate || ')',
                   cl.full_name, r.start_date, r.end_date, r.total_cost, r.status
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN clients cl ON r.client_id = cl.id
            ORDER BY r.id
        ''')
        return [RentalView(*row) for row in self.db.cursor.fetchall()]

    def get_by_id(self, rental_id: int) -> Optional[Rental]:
        self.db.cursor.execute('SELECT * FROM rentals WHERE id=?', (rental_id,))
        row = self.db.cursor.fetchone()
        return Rental(*row) if row else None

    def insert(self, rental: Rental) -> int:
        self.db.cursor.execute('''
            INSERT INTO rentals (car_id, client_id, start_date, end_date, total_cost, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (rental.car_id, rental.client_id, rental.start_date,
              rental.end_date, rental.total_cost, rental.status))
        self.db.conn.commit()
        return self.db.cursor.lastrowid

    def update(self, rental: Rental) -> None:
        self.db.cursor.execute('''
            UPDATE rentals SET car_id=?, client_id=?, start_date=?, end_date=?, total_cost=?, status=?
            WHERE id=?
        ''', (rental.car_id, rental.client_id, rental.start_date, rental.end_date,
            rental.total_cost, rental.status, rental.id))
        self.db.conn.commit()

    def update_status(self, rental_id: int, status: str) -> None:
        self.db.cursor.execute('UPDATE rentals SET status=? WHERE id=?', (status, rental_id))
        self.db.conn.commit()

    def search(self, start_date: str = '', end_date: str = '',
            car_text: str = '', client_text: str = '', cost: str = '') -> List[RentalView]:
        query = '''
            SELECT r.id, c.brand || ' ' || c.model || ' (' || c.license_plate || ')',
                cl.full_name, r.start_date, r.end_date, r.total_cost, r.status
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN clients cl ON r.client_id = cl.id
            WHERE 1=1
        '''
        params = []

        # Диапазон дат начала
        if start_date:
            if '-' in start_date and len(start_date.split('-')) == 3:  # Полная дата
                query += ' AND date(r.start_date) >= ?'
                params.append(start_date)
            else:  # Поиск по части даты
                query += ' AND date(r.start_date) LIKE ?'
                params.append(f'%{start_date}%')

        if end_date:
            if '-' in end_date and len(end_date.split('-')) == 3:  # Полная дата
                query += ' AND date(r.end_date) <= ?'
                params.append(end_date)
            else:  # Поиск по части даты
                query += ' AND date(r.end_date) LIKE ?'
                params.append(f'%{end_date}%')

        if car_text:
            query += " AND LOWER(c.brand || ' ' || c.model || ' (' || c.license_plate || ')') LIKE LOWER(?)"
            params.append(f'%{car_text}%')
        if client_text:
            query += ' AND LOWER(cl.full_name) LIKE LOWER(?)'
            params.append(f'%{client_text}%')
        if cost:
            if '-' in cost:
                lo, hi = cost.split('-', 1)
                query += ' AND r.total_cost BETWEEN ? AND ?'
                params.extend([float(lo), float(hi)])
            elif cost.startswith('>'):
                query += ' AND r.total_cost > ?'
                params.append(float(cost[1:]))
            elif cost.startswith('<'):
                query += ' AND r.total_cost < ?'
                params.append(float(cost[1:]))
            else:
                query += ' AND r.total_cost = ?'
                params.append(float(cost))

        self.db.cursor.execute(query, params)
        return [RentalView(*row) for row in self.db.cursor.fetchall()]

    def has_date_conflict(self, car_id: int, start_dt: str, end_dt: str,
                        exclude_rental_id: int = None) -> bool:
        """Проверка пересечения дат для данного автомобиля"""
        query = '''
            SELECT COUNT(*) FROM rentals
            WHERE car_id = ? AND status IN ('активная', 'забронировано')
            AND start_date < ? AND datetime(end_date, '+1 hour') > datetime(?)
        '''
        params = [car_id, end_dt, start_dt]
        if exclude_rental_id:
            query += ' AND id != ?'
            params.append(exclude_rental_id)
        self.db.cursor.execute(query, params)
        return self.db.cursor.fetchone()[0] > 0

    def activate_due_bookings(self, today: str) -> None:
        """Переводит забронированные аренды в активные, если дата начала наступила"""
        self.db.cursor.execute('''
            SELECT id, car_id FROM rentals
            WHERE status = 'забронировано' AND start_date <= ?
        ''', (today,))
        due = self.db.cursor.fetchall()
        for rental_id, car_id in due:
            self.db.cursor.execute('UPDATE rentals SET status="активная" WHERE id=?', (rental_id,))
            self.db.cursor.execute('UPDATE cars SET status="арендован" WHERE id=?', (car_id,))
        if due:
            self.db.conn.commit()


    # --- Запросы для вкладки "Отчёты" ---

    def get_income_summary(self, start_date: str, end_date: str):
        self.db.cursor.execute('''
            SELECT COUNT(*), SUM(total_cost) FROM rentals
            WHERE date(start_date) >= ? AND date(start_date) <= ?
            AND status IN ('активная', 'завершенная')
        ''', (start_date, end_date))
        count, total = self.db.cursor.fetchone()
        return count, (total or 0)

    def get_income_by_car(self, start_date: str, end_date: str):
        self.db.cursor.execute('''
            SELECT c.brand, c.model, c.license_plate, COUNT(r.id), SUM(r.total_cost)
            FROM cars c
            LEFT JOIN rentals r ON c.id = r.car_id
                AND date(r.start_date) >= ? AND date(r.start_date) <= ?
                AND r.status IN ('активная', 'завершенная')
            GROUP BY c.id
            ORDER BY SUM(r.total_cost) DESC
        ''', (start_date, end_date))
        return self.db.cursor.fetchall()

    def get_income_by_month(self, start_date: str, end_date: str):
        self.db.cursor.execute('''
            SELECT strftime('%Y-%m', start_date) as month, COUNT(*), SUM(total_cost)
            FROM rentals
            WHERE date(start_date) >= ? AND date(start_date) <= ?
            AND status IN ('активная', 'завершенная')
            GROUP BY strftime('%Y-%m', start_date)
            ORDER BY month
        ''', (start_date, end_date))
        return self.db.cursor.fetchall()

    def get_active_rentals(self):
        self.db.cursor.execute('''
            SELECT c.brand, c.model, cl.full_name, r.start_date, r.end_date
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN clients cl ON r.client_id = cl.id
            WHERE r.status = 'активная'
            ORDER BY r.end_date
        ''')
        return self.db.cursor.fetchall()

    def get_overdue_rentals(self, today: str):
        self.db.cursor.execute('''
            SELECT c.brand, c.model, cl.full_name, cl.phone, r.end_date
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN clients cl ON r.client_id = cl.id
            WHERE r.status = 'активная' AND datetime(r.end_date) < datetime(?)
            ORDER BY r.end_date
        ''', (today,))
        return self.db.cursor.fetchall()

    def get_bookings_summary(self, start_date: str, end_date: str):
        self.db.cursor.execute('''
            SELECT COUNT(*), SUM(total_cost) FROM rentals
            WHERE date(start_date) >= ? AND date(start_date) <= ?
            AND status = 'забронировано'
        ''', (start_date, end_date))
        count, total = self.db.cursor.fetchone()
        return count, (total or 0)

    def get_booked_rentals(self, start_date: str, end_date: str):
        self.db.cursor.execute('''
            SELECT c.brand, c.model, cl.full_name, r.start_date, r.end_date, r.total_cost
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN clients cl ON r.client_id = cl.id
            WHERE date(r.start_date) >= ? AND date(r.start_date) <= ?
            AND r.status = 'забронировано'
            ORDER BY r.start_date
        ''', (start_date, end_date))
        return self.db.cursor.fetchall()

    def get_bookings_by_month(self):
        self.db.cursor.execute('''
            SELECT strftime('%Y-%m', date(start_date)), COUNT(*), SUM(total_cost)
            FROM rentals WHERE status = 'забронировано'
            GROUP BY strftime('%Y-%m', date(start_date)) ORDER BY 1
        ''')
        return self.db.cursor.fetchall()

    def get_bookings_by_car(self):
        self.db.cursor.execute('''
            SELECT c.brand, c.model, COUNT(r.id), SUM(r.total_cost)
            FROM cars c JOIN rentals r ON c.id = r.car_id
            WHERE r.status = 'забронировано'
            GROUP BY c.id HAVING COUNT(r.id) > 0
            ORDER BY SUM(r.total_cost) DESC
        ''')
        return self.db.cursor.fetchall()

    def get_export_data(self, start_date: str, end_date: str):
        self.db.cursor.execute('''
            SELECT r.id, c.brand, c.model, c.license_plate, cl.full_name,
                cl.phone, r.start_date, r.end_date, r.total_cost, r.status
            FROM rentals r
            JOIN cars c ON r.car_id = c.id
            JOIN clients cl ON r.client_id = cl.id
            WHERE r.date(start_date) >= ? AND r.date(start_date) <= ?
            ORDER BY r.id
        ''', (start_date, end_date))
        return self.db.cursor.fetchall()