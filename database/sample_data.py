import random
from datetime import datetime, timedelta

def populate_sample_data(db) -> None:
    """Добавление большого объема реалистичных тестовых данных (актуально на июль 2026)"""
    db.cursor.execute("SELECT COUNT(*) FROM cars")
    if db.cursor.fetchone()[0] != 0:
        return

    # Точка отсчета времени согласно текущему моменту системы
    CURRENT_DATE = datetime(2026, 7, 10, 12, 0)
    START_LOG_DATE = datetime(2026, 1, 1, 9, 0)
    END_LOG_DATE = datetime(2026, 8, 15, 21, 0) # захватываем бронирования на август

    # 1. Справочник брендов и моделей (+ базовая цена за сутки в BYN)
    car_models = {
        'Geely': [('Coolray', 95), ('Atlas Pro', 120), ('Tugella', 160)],
        'Belgee': [('X50', 90)],
        'Volkswagen': [('Polo', 75), ('Passat B8', 115), ('Tiguan', 140)],
        'Skoda': [('Rapid', 75), ('Octavia', 110), ('Kodiaq', 155)],
        'BMW': [('3 Series', 210), ('5 Series', 270), ('X5', 340)],
        'Audi': [('A4', 180), ('A6', 250), ('Q5', 260)],
        'Toyota': [('Camry', 140), ('RAV4', 150)],
        'Zeekr': [('001', 310), ('X', 230), ('007', 290)],
        'Lixiang': [('L7', 440), ('L9', 530)],
        'Tesla': [('Model 3', 260), ('Model Y', 320)]
    }

    # Генерация автомобилей (~45 штук)
    cars_list = []
    car_id_counter = 1
    used_plates = set()

    # Пулы для генерации белорусских номеров (Регион 7 — Минск, Регион 5 — Минская обл.)
    letters_pool = ['AA', 'AB', 'AC', 'AE', 'AK', 'AM', 'AO', 'AP', 'AT', 'AX', 'BC', 'BM', 'BT', 'BX', 'CK', 'CM', 'CT', 'CX', 'TP', 'OK', 'BA', 'HA', 'TA']

    def generate_by_plate(is_electric: bool) -> str:
        while True:
            region = random.choice([5, 7])
            if is_electric:
                # Номера для электромобилей начинаются с 'E'
                num = random.randint(100, 999)
                let = random.choice(['AA', 'AB', 'AC', 'EE', 'BI', 'AI'])
                plate = f"E{num} {let}-{region}"
            else:
                num = random.randint(1000, 9999)
                let = random.choice(letters_pool)
                plate = f"{num} {let}-{region}"
            
            if plate not in used_plates:
                used_plates.add(plate)
                return plate

    for brand, models in car_models.items():
        is_ev = brand in ['Zeekr', 'Lixiang', 'Tesla']
        # Создаем по 4-5 машин каждого бренда разного года выпуска
        for _ in range(random.randint(4, 5)):
            model, base_rate = random.choice(models)
            year = random.randint(2018, 2026)
            
            # Небольшая корректировка цены в зависимости от года выпуска
            rate_modifier = 1.0 + (year - 2022) * 0.04
            daily_rate = round(base_rate * rate_modifier, 1)
            plate = generate_by_plate(is_ev)
            
            cars_list.append({
                'id': car_id_counter,
                'brand': brand,
                'model': model,
                'year': year,
                'license_plate': plate,
                'daily_rate': daily_rate,
                'status': 'доступен',          # обновим позже по логам аренд
                'last_maintenance': '2026-01-01' # обновим позже
            })
            car_id_counter += 1

    # 2. ФИО клиентов
    full_names_pool = [
        "Ковалевский Дмитрий Сергеевич", "Романчук Анна Владимировна", "Савицкий Александр Игоревич",
        "Кравцов Максим Олегович", "Левчук Екатерина Николаевна", "Борисевич Артем Александрович",
        "Григорьев Илья Дмитриевич", "Павлюченко Ольга Михайловна", "Климович Сергей Васильевич",
        "Тарасевич Вероника Юрьевна", "Шевченко Даниил Игоревич", "Мартынова Алина Витальевна",
        "Карпович Егор Андреевич", "Дробышевская Мария Сергеевна", "Сидоренко Никита Олегович",
        "Ковальчук Елена Петровна", "Жук Виталий Николаевич", "Антонова Анастасия Игоревна",
        "Макаревич Павел Викторович", "Кузнецова Ирина Александровна", "Лысенко Денис Владимирович",
        "Степанова Ксения Эдуардовна", "Мельников Роман Сергеевич", "Захарова Дарья Алексеевна",
        "Тихонов Владислав Юрьевич", "Васильева Татьяна Николаевна", "Морозов Алексей Игоревич",
        "Федорова Юлия Дмитриевна", "Попов Кирилл Вадимович", "Орлова Наталья Владимировна",
        "Козлов Михаил Андреевич", "Новикова Елена Викторовна", "Белов Олег Семенович",
        "Соколова Марина Игоревна", "Гончаров Павел Артемьевич", "Кудрявцева Ольга Львовна",
        "Баранов Игорь Юрьевич", "Соболева Анна Семеновна", "Рудак Денис Олегович", "Станкевич Вера Петровна"
    ]

    clients_list = []
    client_id_counter = 1
    phone_prefixes = ['29', '44', '33', '25'] # МТС, А1, Life
    email_domains = ['gmail.com', 'yandex.by', 'mail.ru', 'tut.by']

    for name in full_names_pool:
        phone = f"+375 {random.choice(phone_prefixes)} {random.randint(100,999)}-{random.randint(10,99)}-{random.randint(10,99)}"
        # Генерация номера прав (например, 5JK 123456)
        driver_license = f"{random.randint(1,9)}{''.join(random.choices('ABCDEFGHJKLMNOPQRSTUVWXYZ', k=2))} {random.randint(100000, 999999)}"
        
        # Создаем простой email на основе ФИО
        email = f"{random.choice(['client', 'user', 'driver'])}{random.randint(10,999)}@{random.choice(email_domains)}"
        
        clients_list.append({
            'id': client_id_counter,
            'full_name': name,
            'driver_license': driver_license,
            'phone': phone,
            'email': email
        })
        client_id_counter += 1

    # 3. Симуляция истории аренд с учетом сезонности
    rentals_list = []

    for car in cars_list:
        pointer = START_LOG_DATE
        has_active_rental = False
        last_maint_date = START_LOG_DATE - timedelta(days=random.randint(15, 90))

        # Двигаемся по временной шкале для каждого автомобиля отдельно
        while pointer < END_LOG_DATE:
            month = pointer.month
            
            # Эмуляция сезонного спроса через простои (gap) и длительность аренды
            if month in [1, 2]: # Зима: простои большие, аренды короткие
                gap_days = random.randint(12, 22)
                rent_days = random.randint(1, 3)
            elif month in [3, 4]: # Весна: средний спрос
                gap_days = random.randint(6, 14)
                rent_days = random.randint(2, 5)
            elif month in [5, 6, 7]: # Май и Лето: высокий спрос (простои минимальные, аренды длиннее)
                gap_days = random.randint(1, 4)
                rent_days = random.randint(3, 11)
            else: # Август (будущие бронирования)
                gap_days = random.randint(4, 8)
                rent_days = random.randint(2, 7)

            pointer += timedelta(days=gap_days)
            if pointer >= END_LOG_DATE:
                break

            start_rental = pointer
            end_rental = start_rental + timedelta(days=rent_days)

            # Выбираем случайного клиента (они будут периодически повторяться)
            client = random.choice(clients_list)

            # Корректное определение статуса аренды относительно сегодняшней даты
            if end_rental <= CURRENT_DATE:
                rental_status = 'завершенная'
            elif start_rental <= CURRENT_DATE < end_rental:
                rental_status = 'активная'
                has_active_rental = True
            else:
                rental_status = 'забронировано'

            total_cost = round(rent_days * car['daily_rate'], 2)

            rentals_list.append({
                'car_id': car['id'],
                'client_id': client['id'],
                'start_date': start_rental.strftime('%Y-%m-%d %H:%M'),
                'end_date': end_rental.strftime('%Y-%m-%d %H:%M'),
                'total_cost': total_cost,
                'status': rental_status
            })

            # Эмуляция прохождения ТО (примерно каждые 3-4 месяца)
            if (start_rental - last_maint_date).days > 100 and rental_status == 'завершенная':
                last_maint_date = start_rental - timedelta(days=random.randint(1, 4))

            # Смещаем указатель времени на конец текущей аренды
            pointer = end_rental

        # Синхронизируем финальные свойства машины на основе симуляции
        car['last_maintenance'] = last_maint_date.strftime('%Y-%m-%d')
        if has_active_rental:
            car['status'] = 'арендован'
        else:
            # Если машина сейчас свободна, даем 7% шанс, что прямо сейчас она "на ТО"
            car['status'] = 'на ТО' if random.random() < 0.07 else 'доступен'

    # Подготовка кортежей для массовой вставки (executemany)
    cars_data = [
        (c['brand'], c['model'], c['year'], c['license_plate'], c['daily_rate'], c['status'], c['last_maintenance'])
        for c in cars_list
    ]
    
    clients_data = [
        (cl['full_name'], cl['driver_license'], cl['phone'], cl['email'])
        for cl in clients_list
    ]

    rentals_data = [
        (r['car_id'], r['client_id'], r['start_date'], r['end_date'], r['total_cost'], r['status'])
        for r in rentals_list
    ]

    # Сохранение в базу данных
    db.cursor.executemany('''
        INSERT INTO cars (brand, model, year, license_plate, daily_rate, status, last_maintenance)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', cars_data)

    db.cursor.executemany('''
        INSERT INTO clients (full_name, driver_license, phone, email)
        VALUES (?, ?, ?, ?)
    ''', clients_data)

    db.cursor.executemany('''
        INSERT INTO rentals (car_id, client_id, start_date, end_date, total_cost, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', rentals_data)

    db.conn.commit()







# def populate_sample_data(db) -> None:
#     """Добавление тестовых данных"""
#     db.cursor.execute("SELECT COUNT(*) FROM cars")
#     if db.cursor.fetchone()[0] != 0:
#         return

#     cars_data = [
#         ('Toyota', 'Camry', 2020, '1204 AB-7', 140.0, 'доступен', '2025-01-15'),
#         ('BMW', 'X5', 2019, '5678 CK-7', 220.0, 'арендован', '2025-02-20'),
#         ('Audi', 'A4', 2021, '9012 TP-7', 190.0, 'арендован', '2025-03-10'),
#         ('Mercedes', 'C-Class', 2018, '3456 AX-7', 450.0, 'доступен', '2024-12-22'),
#         ('Volkswagen', 'Passat', 2022, '7890 AC-7', 130.0, 'на ТО', '2024-06-15'),
#         ('Lixiang', 'L9', 2024, 'E303AA-7', 580.0, 'арендован', '2025-04-11'),
#         ('Zeekr', '007', 2024, 'E204AA-7', 350.0, 'доступен', '2025-06-01'),
#         ('Tesla', 'Model 3', 2023, 'E001AB-7', 300.0, 'арендован', '2025-05-10'),
#     ]
#     db.cursor.executemany('''
#         INSERT INTO cars (brand, model, year, license_plate, daily_rate, status, last_maintenance)
#         VALUES (?, ?, ?, ?, ?, ?, ?)
#     ''', cars_data)

#     clients_data = [
#         ('Волынская Алиса Денисовна', '5JK 789012', '+375 29 581-27-93', 'volynskaya.ad@mailbox.org'),
#         ('Кирьянов Макар Олегович', '7NM 345678', '+375 44 239-65-18', 'm.kiryanov@gmail.com'),
#         ('Штефанюк Елизавета Романовна', '8PQ 901234', '+375 33 715-48-26', 'lizashtefan@yandex.ru'),
#         ('Якубович Артём Валерьевич', '9RS 567890', '+375 25 894-12-37', 'yakubovich_av@gmail.com'),
#         ('Гареева Амина Фаридовна', '2TV 123789', '+375 29 346-59-01', 'gareeva1995@rambler.ru'),
#         ('Дроздович Никита Игоревич', '4WX 456123', '+375 44 672-93-45', 'drozdov.nik@fastmail.com'),
#         ('Цыбулько Вера Константиновна', '6YZ 890456', '+375 33 281-64-79', 'vera.tsibulko@gmail.com'),
#     ]
#     db.cursor.executemany('''
#         INSERT INTO clients (full_name, driver_license, phone, email)
#         VALUES (?, ?, ?, ?)
#     ''', clients_data)

#     rentals_data = [
#         (3, 1, '2025-06-13 10:00', '2025-06-25 10:00', 2280.0, 'активная'),
#         (1, 2, '2025-06-01 10:00', '2025-06-05 10:00', 560.0, 'завершенная'),
#         (2, 3, '2025-05-15 10:00', '2025-05-20 10:00', 1100.0, 'завершенная'),
#         (7, 5, '2025-05-28 10:00', '2025-05-30 10:00', 700.0, 'завершенная'),
#         (8, 6, '2025-06-16 10:00', '2025-06-19 10:00', 900.0, 'активная'),
#         (2, 4, '2025-05-23 10:00', '2025-05-26 10:00', 660.0, 'завершенная'),
#         (2, 2, '2025-06-11 10:00', '2025-06-14 10:00', 660.0, 'активная'),
#         (6, 3, '2025-06-17 10:00', '2025-06-19 10:00', 1160.0, 'активная'),
#     ]
#     db.cursor.executemany('''
#         INSERT INTO rentals (car_id, client_id, start_date, end_date, total_cost, status)
#         VALUES (?, ?, ?, ?, ?, ?)
#     ''', rentals_data)

#     db.conn.commit()