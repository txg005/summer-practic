from dataclasses import dataclass
from typing import Optional


@dataclass
class Car:
    """Строка таблицы cars"""
    id: Optional[int] = None
    brand: str = ""
    model: str = ""
    year: int = 0
    license_plate: str = ""
    daily_rate: float = 0.0
    status: str = "доступен"
    last_maintenance: Optional[str] = None


@dataclass
class Client:
    """Строка таблицы clients"""
    id: Optional[int] = None
    full_name: str = ""
    driver_license: str = ""
    phone: str = ""
    email: str = ""


@dataclass
class Rental:
    """Строка таблицы rentals (сырые данные, без JOIN)"""
    id: Optional[int] = None
    car_id: int = 0
    client_id: int = 0
    start_date: str = ""
    end_date: str = ""
    total_cost: float = 0.0
    status: str = "активная"


@dataclass
class RentalView:
    """Аренда вместе с данными автомобиля и клиента (результат JOIN), для отображения в таблице"""
    id: int
    car_info: str
    client_name: str
    start_date: str
    end_date: str
    total_cost: float
    status: str