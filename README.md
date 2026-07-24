# Car Rental Management System

A desktop application for managing a car rental business. Built with Python, SQLite, and CustomTkinter. Features a dark-themed UI with full CRUD operations, booking logic, conflict detection, and income reporting with charts.

## Features

**Cars**
- Add, edit, and delete vehicles
- Track status: available, rented, under maintenance
- Log maintenance dates
- Search and filter by brand, model, year, license plate, price, and status
- Column sorting with direction indicator

**Clients**
- Register and manage client profiles
- Phone input with country selector and input mask (Belarus, Russia, Kazakhstan, Ukraine, Lithuania, Latvia, Poland, Estonia)
- Case-insensitive Cyrillic name search
- Validation for driver license number format

**Rentals**
- Create rentals with date/time picker and cost calculator
- Two rental types: active (starts today) and booked (future date)
- Booking conflict detection with a 1-hour buffer between rentals
- Update rental details (car, client, dates, cost)
- Complete or cancel a rental with automatic car status update
- Search by car, client, date range, and cost
- Color-coded status rows in the table

**Reports**
- Income report for a selected date range
- Separate sections for confirmed rentals and bookings
- Overdue rental alerts
- Export to Excel (.xlsx)
- Six embedded charts: income by month, rental count by month, income by car, rental count by car, and two booking charts
- Hover tooltips on chart bars showing exact values
- Resizable split view between the text report and charts

## Tech Stack

- Python 3.10+
- CustomTkinter 5.x
- SQLite3 (via standard library)
- matplotlib
- openpyxl
- tkcalendar (replaced by custom dark calendar widget)

## Project Structure

```
car_rental_diploma/
├── main.py
├── database/
│   ├── __init__.py
│   ├── db_connection.py        # SQLite connection and schema
│   ├── models.py               # Dataclasses: Car, Client, Rental, RentalView
│   ├── cars_repository.py      # CRUD and search for cars
│   ├── clients_repository.py   # CRUD and search for clients
│   ├── rentals_repository.py   # CRUD, search, and report queries
│   └── sample_data.py          # Initial seed data
├── gui/
│   ├── __init__.py
│   ├── main_window.py          # App window, top navigation, tab routing
│   ├── theme.py                # Color constants
│   ├── cars_tab.py
│   ├── clients_tab.py
│   ├── rentals_tab.py
│   ├── reports_tab.py
│   ├── ctk_calendar.py         # Custom dark calendar popup widget
│   └── ctk_phone_picker.py     # Country selector + masked phone input
└── utils/
    ├── __init__.py
    ├── validators.py            # License plate and driver license validators
    └── tooltip.py               # Hover tooltip widget
```

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/txg005/summer-practic.git
   cd summer-practic
   ```

2. Install dependencies:
   ```
   pip install customtkinter matplotlib openpyxl
   ```

3. Run the application:
   ```
   python main.py
   ```

The SQLite database file (`car_rental.db`) is created automatically on first launch and populated with sample data.

## Requirements

- Python 3.10 or higher
- Windows 10/11 (tested); macOS and Linux should work but are not the primary target

## Architecture Notes

The project follows a layered structure without a dedicated service layer:

- `database/` handles all SQL queries through repository classes. Each table has its own repository. Raw tuples from SQLite are mapped to dataclasses before being returned.
- `gui/` contains one class per tab. Tabs communicate through callback functions passed via the constructor (e.g., when a rental is created, `CarsTab.load_cars()` is called to reflect the updated car status).
- `utils/` contains stateless helper functions and widgets with no dependency on the database layer.

## Known Limitations

- `ttk.Treeview` does not support fully custom styling (rounded corners, custom fonts per cell). This is a Tkinter limitation.
- `SQLite LOWER()` does not handle Cyrillic characters. All case-insensitive search on Russian text is performed on the Python side after fetching results.
- Phone number validation is handled by the input mask in `CTkPhonePicker`. The stored format depends on the country selected.

## License

MIT