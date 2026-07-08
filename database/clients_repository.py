from typing import List, Optional

from .models import Client


class ClientsRepository:
    """Доступ к таблице clients"""

    def __init__(self, db):
        self.db = db

    def get_all(self) -> List[Client]:
        self.db.cursor.execute('SELECT * FROM clients ORDER BY id')
        return [Client(*row) for row in self.db.cursor.fetchall()]

    def get_by_id(self, client_id: int) -> Optional[Client]:
        self.db.cursor.execute('SELECT * FROM clients WHERE id=?', (client_id,))
        row = self.db.cursor.fetchone()
        return Client(*row) if row else None

    def insert(self, client: Client) -> int:
        self.db.cursor.execute('''
            INSERT INTO clients (full_name, driver_license, phone, email)
            VALUES (?, ?, ?, ?)
        ''', (client.full_name, client.driver_license, client.phone, client.email))
        self.db.conn.commit()
        return self.db.cursor.lastrowid

    def update(self, client: Client) -> None:
        self.db.cursor.execute('''
            UPDATE clients SET full_name=?, driver_license=?, phone=?, email=?
            WHERE id=?
        ''', (client.full_name, client.driver_license, client.phone, client.email, client.id))
        self.db.conn.commit()

    def delete(self, client_id: int) -> None:
        self.db.cursor.execute('DELETE FROM clients WHERE id=?', (client_id,))
        self.db.conn.commit()

    def search(self, name: str = '', license_num: str = '', phone: str = '', email: str = '') -> List[Client]:
        query = 'SELECT * FROM clients WHERE 1=1'
        params = []

        if license_num:
            query += ' AND driver_license LIKE ?'
            params.append(f'%{license_num}%')
        if phone:
            query += ' AND phone LIKE ?'
            params.append(f'%{phone}%')
        if email:
            query += ' AND email LIKE ?'
            params.append(f'%{email}%')

        self.db.cursor.execute(query, params)
        results = [Client(*row) for row in self.db.cursor.fetchall()]

        if name:
            results = [c for c in results if name.lower() in c.full_name.lower()]
        return results

    def filter_by_name(self, text: str) -> List[Client]:
        """Используется для автодополнения в комбобоксе аренды"""
        self.db.cursor.execute('SELECT * FROM clients')
        all_clients = [Client(*row) for row in self.db.cursor.fetchall()]
        return [c for c in all_clients if text.lower() in c.full_name.lower()]