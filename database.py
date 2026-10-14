import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'budget.db')

DEFAULT_CATEGORIES = [
    {
        'id': 'food',
        'name': 'Food & Dining',
        'planned_budget': 280.0,
        'icon': 'utensils',
        'color': '#FF6B6B',
        'bg_color': '#FFF0F0',
        'border_color': '#FFA8A8'
    },
    {
        'id': 'travel',
        'name': 'Travel & Commute',
        'planned_budget': 90.0,
        'icon': 'bus',
        'color': '#0EA5E9',
        'bg_color': '#F0F9FF',
        'border_color': '#7DD3FC'
    },
    {
        'id': 'education',
        'name': 'Education & Supplies',
        'planned_budget': 180.0,
        'icon': 'graduation-cap',
        'color': '#8B5CF6',
        'bg_color': '#F5F3FF',
        'border_color': '#C4B5FD'
    },
    {
        'id': 'entertainment',
        'name': 'Entertainment & Fun',
        'planned_budget': 120.0,
        'icon': 'gamepad-2',
        'color': '#F59E0B',
        'bg_color': '#FFFBEB',
        'border_color': '#FCD34D'
    },
    {
        'id': 'savings',
        'name': 'Savings & Cushion',
        'planned_budget': 180.0,
        'icon': 'piggy-bank',
        'color': '#10B981',
        'bg_color': '#ECFDF5',
        'border_color': '#6EE7B7'
    }
]

def get_db_connection(db_path=None):
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path=None):
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            monthly_budget REAL NOT NULL DEFAULT 850.0,
            currency_symbol TEXT NOT NULL DEFAULT '$',
            student_name TEXT DEFAULT 'Alex Rivera',
            college_name TEXT DEFAULT 'Oakridge University',
            theme TEXT DEFAULT 'light',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            planned_budget REAL NOT NULL DEFAULT 0.0,
            icon TEXT,
            color TEXT,
            bg_color TEXT,
            border_color TEXT
        )
    ''')

    # Transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL CHECK (type IN ('expense', 'income')),
            amount REAL NOT NULL,
            category_id TEXT NOT NULL,
            description TEXT NOT NULL,
            date TEXT NOT NULL,
            notes TEXT,
            payment_method TEXT DEFAULT 'debit',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Savings goals table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS savings_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0.0,
            target_date TEXT,
            emoji TEXT DEFAULT '🎯',
            color TEXT DEFAULT '#10B981',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()

    # Seed default settings if empty
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO settings (id, monthly_budget, currency_symbol, student_name, college_name, theme)
            VALUES (1, 850.0, '$', 'Alex Rivera', 'Oakridge University', 'light')
        ''')

    # Seed categories if empty
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        for cat in DEFAULT_CATEGORIES:
            cursor.execute('''
                INSERT INTO categories (id, name, planned_budget, icon, color, bg_color, border_color)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (cat['id'], cat['name'], cat['planned_budget'], cat['icon'], cat['color'], cat['bg_color'], cat['border_color']))

    # Seed sample transactions and goals if empty
    cursor.execute('SELECT COUNT(*) FROM transactions')
    if cursor.fetchone()[0] == 0:
        seed_sample_data(conn)

    conn.commit()
    conn.close()

def seed_sample_data(conn):
    cursor = conn.cursor()
    
    # Reset transactions and goals
    cursor.execute('DELETE FROM transactions')
    cursor.execute('DELETE FROM savings_goals')

    # Ensure settings & category defaults
    cursor.execute('''
        INSERT OR REPLACE INTO settings (id, monthly_budget, currency_symbol, student_name, college_name, theme)
        VALUES (1, 850.0, '$', 'Alex Rivera', 'Oakridge University', 'light')
    ''')

    for cat in DEFAULT_CATEGORIES:
        cursor.execute('''
            INSERT OR REPLACE INTO categories (id, name, planned_budget, icon, color, bg_color, border_color)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (cat['id'], cat['name'], cat['planned_budget'], cat['icon'], cat['color'], cat['bg_color'], cat['border_color']))

    # Realistic dates in current month/year
    today = datetime.now()
    year_month = today.strftime('%Y-%m')

    sample_transactions = [
        # Income
        ('income', 240.0, 'income', 'Campus Library Assistant Stipend', f'{year_month}-01', 'Bi-weekly student work-study', 'campus_card'),
        ('income', 160.0, 'income', 'Weekend Math Tutoring', f'{year_month}-06', 'High school calculus prep session', 'upi_venmo'),
        ('income', 50.0, 'income', 'Birthday Gift from Aunt', f'{year_month}-10', 'Early birthday check', 'cash'),

        # Expenses - Food ($164.20 of $280 planned)
        ('expense', 11.50, 'food', 'Campus Hub Burrito Bowl', f'{year_month}-02', 'Quick lunch between lectures', 'campus_card'),
        ('expense', 54.80, 'food', 'Weekly Trader Joe’s Dorm Groceries', f'{year_month}-04', 'Oats, milk, bananas, pasta, eggs', 'debit'),
        ('expense', 6.20, 'food', 'Library Latte & Bagel', f'{year_month}-07', 'Late night exam study snack', 'debit'),
        ('expense', 48.90, 'food', 'Fresh Produce & Pantry Staples', f'{year_month}-10', 'Shared meal prep with roommate', 'debit'),
        ('expense', 18.50, 'food', 'Sunday Pizza Study Group', f'{year_month}-12', 'Group study session dinner split', 'upi_venmo'),
        ('expense', 24.30, 'food', 'Cafeteria Bento Box & Juice', f'{year_month}-13', 'Midweek dinner after lab', 'campus_card'),

        # Expenses - Travel ($42.00 of $90 planned)
        ('expense', 30.00, 'travel', 'Monthly Metro Student Transit Pass', f'{year_month}-01', 'Unlimited subway and city buses', 'debit'),
        ('expense', 12.00, 'travel', 'Late Night Ride Home After Hackathon', f'{year_month}-09', 'Rideshare split with dorm friends', 'upi_venmo'),

        # Expenses - Education ($104.99 of $180 planned)
        ('expense', 58.00, 'education', 'Used Physics Principles Textbook', f'{year_month}-03', 'Bought secondhand from senior', 'cash'),
        ('expense', 24.99, 'education', 'Scientific Lab Notebook & Pens', f'{year_month}-05', 'Campus bookstore supplies', 'campus_card'),
        ('expense', 22.00, 'education', 'Notion Student Pro & Cloud Backup', f'{year_month}-08', 'Course syllabus & lecture organizer', 'debit'),

        # Expenses - Entertainment ($63.99 of $120 planned)
        ('expense', 5.99, 'entertainment', 'Spotify Student Bundle', f'{year_month}-02', 'Monthly streaming discount plan', 'debit'),
        ('expense', 24.00, 'entertainment', 'Campus Film Club Festival Ticket', f'{year_month}-08', 'Friday evening indie cinema screening', 'debit'),
        ('expense', 34.00, 'entertainment', 'Board Games & Snacks Night', f'{year_month}-11', 'Dorm weekend game lounge hosting', 'cash'),

        # Expenses - Savings ($90.00 of $180 planned)
        ('expense', 50.00, 'savings', 'Transferred to Emergency Cushion', f'{year_month}-03', 'High-yield student savings account', 'debit'),
        ('expense', 40.00, 'savings', 'Deposit for Laptop Upgrade', f'{year_month}-10', 'Saving for new M3 MacBook Air', 'debit'),
    ]

    for item in sample_transactions:
        cursor.execute('''
            INSERT INTO transactions (type, amount, category_id, description, date, notes, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', item)

    sample_goals = [
        ('New M3 MacBook Air', 650.0, 390.0, f'{today.year}-12-20', '💻', '#6366F1'),
        ('Summer Roadtrip & Camping', 300.0, 160.0, f'{today.year + 1}-06-15', '🏕️', '#F59E0B'),
        ('Emergency Peace-of-Mind Fund', 500.0, 310.0, f'{today.year}-11-30', '🛡️', '#10B981'),
        ('Graduation Photography & Attire', 200.0, 75.0, f'{today.year + 1}-05-01', '🎓', '#EC4899')
    ]

    for goal in sample_goals:
        cursor.execute('''
            INSERT INTO savings_goals (title, target_amount, current_amount, target_date, emoji, color)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', goal)

    conn.commit()
