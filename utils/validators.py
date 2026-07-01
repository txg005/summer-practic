import re


def validate_belarusian_phone(phone: str) -> bool:
    """Валидация белорусского номера телефона"""
    pattern = r'^\+375 \d{2} \d{3}-\d{2}-\d{2}$'
    return bool(re.match(pattern, phone))


def validate_belarusian_license_plate(plate: str) -> bool:
    """Валидация белорусского номера автомобиля"""
    pattern = r'^(\d{4} [A-Z]{2}-\d|E\d{3}[A-Z]{2}-\d)$'
    return bool(re.match(pattern, plate))


def validate_driver_license(license_num: str) -> bool:
    """Валидация номера водительских прав"""
    pattern = r'^\d[A-Z]{2} \d{6}$'
    return bool(re.match(pattern, license_num))