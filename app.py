from flask import Flask, render_template, request, jsonify, Response
import sqlite3
import calendar
from datetime import datetime
import io
import csv
import database

app = Flask(__name__, static_folder='static', template_folder='templates')

# Ensure DB initialized on start
database.init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Returns dashboard summary, category totals, daily pacing, and insights."""
    selected_month = request.args.get('month')
    if not selected_month:
        selected_month = datetime.now().strftime('%Y-%m')

    conn = database.get_db_connection()
    cursor = conn.cursor()

    # Settings
    cursor.execute('SELECT * FROM settings WHERE id = 1')
    settings_row = cursor.fetchone()
    settings = dict(settings_row) if settings_row else {
        'monthly_budget': 850.0,
        'currency_symbol': '$',
        'student_name': 'Alex Rivera',
        'college_name': 'Oakridge University',
        'theme': 'light'
    }

    # Categories
    cursor.execute('SELECT * FROM categories ORDER BY id')
    categories = [dict(row) for row in cursor.fetchall()]

    # Spending by category for selected month
    cursor.execute('''
        SELECT category_id, SUM(amount) as total_spent, COUNT(*) as count
        FROM transactions
        WHERE type = 'expense' AND date LIKE ?
        GROUP BY category_id
    ''', (f'{selected_month}%',))
    spent_map = {row['category_id']: row['total_spent'] for row in cursor.fetchall()}

    # Income in selected month
    cursor.execute('''
        SELECT SUM(amount) as total_income
        FROM transactions
        WHERE type = 'income' AND date LIKE ?
    ''', (f'{selected_month}%',))
    income_row = cursor.fetchone()
    total_income = income_row['total_income'] or 0.0

    # Total expenses in selected month
    total_spent = sum(spent_map.values())
    monthly_budget = float(settings['monthly_budget'])
    remaining_balance = monthly_budget - total_spent
    budget_progress = round((total_spent / monthly_budget * 100), 1) if monthly_budget > 0 else 0

    # Calculate days in month & remaining days
    try:
        year, month_num = map(int, selected_month.split('-'))
        days_in_month = calendar.monthrange(year, month_num)[1]
        now = datetime.now()
        if now.year == year and now.month == month_num:
            current_day = now.day
            days_remaining = max(1, days_in_month - current_day + 1)
        elif datetime(year, month_num, 1) < datetime(now.year, now.month, 1):
            days_remaining = 0
            current_day = days_in_month
        else:
            days_remaining = days_in_month
            current_day = 1
    except Exception:
        days_in_month = 30
        days_remaining = 15
        current_day = 15

    safe_daily_spend = round(remaining_balance / days_remaining, 2) if days_remaining > 0 and remaining_balance > 0 else 0.0

    # Total accumulated in savings goals
    cursor.execute('SELECT SUM(current_amount) as total_goals_saved, SUM(target_amount) as total_goals_target FROM savings_goals')
    goals_summary = cursor.fetchone()
    total_goals_saved = goals_summary['total_goals_saved'] or 0.0
    total_goals_target = goals_summary['total_goals_target'] or 0.0

    # Process each category
    sum_planned_categories = 0.0
    category_cards = []
    highest_spent_cat = None
    highest_percent_cat = None
    max_pct = -1.0
    max_amt = -1.0

    for cat in categories:
        cat_id = cat['id']
        planned = float(cat['planned_budget'])
        sum_planned_categories += planned
        spent = float(spent_map.get(cat_id, 0.0))
        pct = round((spent / planned * 100), 1) if planned > 0 else (100.0 if spent > 0 else 0.0)
        rem = planned - spent

        if pct < 75.0:
            status = 'safe'
            status_text = 'On Track'
        elif pct <= 100.0:
            status = 'approaching'
            status_text = 'Near Limit'
        else:
            status = 'over'
            status_text = 'Exceeded'

        if pct > max_pct and spent > 0:
            max_pct = pct
            highest_percent_cat = cat['name']

        if spent > max_amt:
            max_amt = spent
            highest_spent_cat = cat['name']

        category_cards.append({
            'id': cat_id,
            'name': cat['name'],
            'planned_budget': planned,
            'spent': spent,
            'remaining': rem,
            'percentage': pct,
            'status': status,
            'status_text': status_text,
            'icon': cat['icon'],
            'color': cat['color'],
            'bg_color': cat['bg_color'],
            'border_color': cat['border_color']
        })

    # Recent transactions (top 5 for dashboard)
    cursor.execute('''
        SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.date LIKE ?
        ORDER BY t.date DESC, t.id DESC
        LIMIT 6
    ''', (f'{selected_month}%',))
    recent_transactions = [dict(row) for row in cursor.fetchall()]

    # Largest expense of the month
    cursor.execute('''
        SELECT description, amount, category_id, date
        FROM transactions
        WHERE type = 'expense' AND date LIKE ?
        ORDER BY amount DESC
        LIMIT 1
    ''', (f'{selected_month}%',))
    top_expense_row = cursor.fetchone()
    top_expense = dict(top_expense_row) if top_expense_row else None

    # Budget Allocation Mismatch Analysis
    diff = round(sum_planned_categories - monthly_budget, 2)
    if abs(diff) < 0.01:
        allocation_status = 'balanced'
        allocation_message = 'Perfect! Category budgets match 100% of your monthly budget.'
    elif diff < 0:
        allocation_status = 'unallocated'
        allocation_message = f'{settings["currency_symbol"]}{abs(diff):.2f} unallocated buffer remaining in overall budget.'
    else:
        allocation_status = 'over_allocated'
        allocation_message = f'Category budgets exceed overall monthly budget by {settings["currency_symbol"]}{diff:.2f}.'

    # Student Friendly Encouraging Insights
    if budget_progress <= 40:
        encouragement = "🌟 You're doing amazing! Your spending is well under control with plenty of room to save."
    elif budget_progress <= 75:
        encouragement = "✨ Great pacing! You are keeping a balanced rhythm and staying on track."
    elif budget_progress <= 95:
        encouragement = "⚡ Approaching your limit. Focus on essentials for the next few days to stay balanced."
    else:
        encouragement = "💡 You have utilized your monthly budget. Review non-essential categories or lean on your savings cushion."

    conn.close()

    return jsonify({
        'success': True,
        'month': selected_month,
        'settings': settings,
        'monthly_budget': monthly_budget,
        'total_spent': round(total_spent, 2),
        'total_income': round(total_income, 2),
        'remaining_balance': round(remaining_balance, 2),
        'net_cashflow': round(total_income - total_spent, 2),
        'budget_progress': budget_progress,
        'days_in_month': days_in_month,
        'days_remaining': days_remaining,
        'safe_daily_spend': safe_daily_spend,
        'categories': category_cards,
        'recent_transactions': recent_transactions,
        'top_expense': top_expense,
        'total_goals_saved': round(total_goals_saved, 2),
        'total_goals_target': round(total_goals_target, 2),
        'sum_planned_categories': round(sum_planned_categories, 2),
        'allocation_diff': diff,
        'allocation_status': allocation_status,
        'allocation_message': allocation_message,
        'highest_percent_category': highest_percent_cat,
        'highest_spent_category': highest_spent_cat,
        'encouragement': encouragement
    })

@app.route('/api/budget', methods=['GET', 'POST'])
def manage_budget():
    """Get or update overall budget and category planned amounts."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM settings WHERE id = 1')
        settings = dict(cursor.fetchone())
        cursor.execute('SELECT * FROM categories ORDER BY id')
        categories = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({
            'success': True,
            'settings': settings,
            'categories': categories
        })

    # POST: Update budget
    data = request.get_json() or {}
    if 'monthly_budget' in data:
        try:
            new_budget = float(data['monthly_budget'])
            if new_budget < 0:
                return jsonify({'success': False, 'error': 'Budget cannot be negative'}), 400
            cursor.execute('UPDATE settings SET monthly_budget = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1', (new_budget,))
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid budget value'}), 400

    if 'categories' in data and isinstance(data['categories'], list):
        for item in data['categories']:
            cat_id = item.get('id')
            planned = float(item.get('planned_budget', 0))
            if planned < 0:
                return jsonify({'success': False, 'error': f'Budget for {cat_id} cannot be negative'}), 400
            cursor.execute('''
                UPDATE categories
                SET planned_budget = ?
                WHERE id = ?
            ''', (planned, cat_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Budget updated successfully!'})

@app.route('/api/settings', methods=['POST'])
def update_settings():
    """Update profile and display preferences."""
    data = request.get_json() or {}
    conn = database.get_db_connection()
    cursor = conn.cursor()

    fields = []
    values = []
    if 'currency_symbol' in data:
        fields.append('currency_symbol = ?')
        values.append(data['currency_symbol'])
    if 'student_name' in data:
        fields.append('student_name = ?')
        values.append(data['student_name'].strip())
    if 'college_name' in data:
        fields.append('college_name = ?')
        values.append(data['college_name'].strip())
    if 'theme' in data:
        fields.append('theme = ?')
        values.append(data['theme'])

    if fields:
        fields.append('updated_at = CURRENT_TIMESTAMP')
        query = f"UPDATE settings SET {', '.join(fields)} WHERE id = 1"
        cursor.execute(query, values)
        conn.commit()

    cursor.execute('SELECT * FROM settings WHERE id = 1')
    updated = dict(cursor.fetchone())
    conn.close()
    return jsonify({'success': True, 'settings': updated})

@app.route('/api/transactions', methods=['GET', 'POST'])
def manage_transactions():
    """List or create transactions."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        category = request.args.get('category', 'all')
        tx_type = request.args.get('type', 'all')
        month = request.args.get('month', 'all')
        search = request.args.get('search', '').strip()
        sort = request.args.get('sort', 'date_desc')

        query = '''
            SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
            FROM transactions t
            LEFT JOIN categories c ON t.category_id = c.id
            WHERE 1=1
        '''
        params = []

        if category and category != 'all':
            query += ' AND t.category_id = ?'
            params.append(category)

        if tx_type and tx_type != 'all':
            query += ' AND t.type = ?'
            params.append(tx_type)

        if month and month != 'all':
            query += ' AND t.date LIKE ?'
            params.append(f'{month}%')

        if search:
            query += ' AND (t.description LIKE ? OR t.notes LIKE ?)'
            params.extend([f'%{search}%', f'%{search}%'])

        if sort == 'date_asc':
            query += ' ORDER BY t.date ASC, t.id ASC'
        elif sort == 'amount_desc':
            query += ' ORDER BY t.amount DESC'
        elif sort == 'amount_asc':
            query += ' ORDER BY t.amount ASC'
        else: # date_desc
            query += ' ORDER BY t.date DESC, t.id DESC'

        cursor.execute(query, params)
        transactions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'success': True, 'transactions': transactions, 'count': len(transactions)})

    # POST: Add new transaction
    data = request.get_json() or {}
    tx_type = data.get('type', 'expense').lower()
    description = (data.get('description') or '').strip()
    date_val = data.get('date') or datetime.now().strftime('%Y-%m-%d')
    category_id = data.get('category_id') or ('food' if tx_type == 'expense' else 'income')
    notes = (data.get('notes') or '').strip()
    payment_method = data.get('payment_method') or 'debit'

    # Validation
    try:
        amount = float(data.get('amount', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid amount value'}), 400

    if amount <= 0:
        return jsonify({'success': False, 'error': 'Amount must be greater than zero'}), 400

    if not description:
        return jsonify({'success': False, 'error': 'Description is required'}), 400

    if tx_type not in ('expense', 'income'):
        return jsonify({'success': False, 'error': 'Type must be expense or income'}), 400

    # Ensure valid category if expense
    if tx_type == 'expense' and category_id not in ['food', 'travel', 'education', 'entertainment', 'savings']:
        return jsonify({'success': False, 'error': 'Invalid category for expense'}), 400

    cursor.execute('''
        INSERT INTO transactions (type, amount, category_id, description, date, notes, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (tx_type, amount, category_id, description, date_val, notes, payment_method))
    new_id = cursor.lastrowid
    conn.commit()

    cursor.execute('''
        SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = ?
    ''', (new_id,))
    created_tx = dict(cursor.fetchone())
    conn.close()

    return jsonify({'success': True, 'transaction': created_tx, 'message': 'Transaction added successfully!'}), 201

@app.route('/api/transactions/<int:tx_id>', methods=['GET', 'PUT', 'DELETE'])
def transaction_detail(tx_id):
    """View, update or delete a transaction."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM transactions WHERE id = ?', (tx_id,))
    tx = cursor.fetchone()
    if not tx:
        conn.close()
        return jsonify({'success': False, 'error': 'Transaction not found'}), 404

    if request.method == 'GET':
        conn.close()
        return jsonify({'success': True, 'transaction': dict(tx)})

    if request.method == 'DELETE':
        cursor.execute('DELETE FROM transactions WHERE id = ?', (tx_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Transaction removed successfully'})

    # PUT: Update
    data = request.get_json() or {}
    tx_type = data.get('type', tx['type']).lower()
    description = (data.get('description') or tx['description']).strip()
    date_val = data.get('date') or tx['date']
    category_id = data.get('category_id') or tx['category_id']
    notes = data.get('notes', tx['notes'])
    payment_method = data.get('payment_method', tx['payment_method'])

    try:
        amount = float(data.get('amount', tx['amount']))
    except (ValueError, TypeError):
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid amount value'}), 400

    if amount <= 0:
        conn.close()
        return jsonify({'success': False, 'error': 'Amount must be greater than zero'}), 400

    if not description:
        conn.close()
        return jsonify({'success': False, 'error': 'Description cannot be empty'}), 400

    cursor.execute('''
        UPDATE transactions
        SET type = ?, amount = ?, category_id = ?, description = ?, date = ?, notes = ?, payment_method = ?
        WHERE id = ?
    ''', (tx_type, amount, category_id, description, date_val, notes, payment_method, tx_id))
    conn.commit()

    cursor.execute('''
        SELECT t.*, c.name as category_name, c.color as category_color, c.icon as category_icon
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.id = ?
    ''', (tx_id,))
    updated_tx = dict(cursor.fetchone())
    conn.close()

    return jsonify({'success': True, 'transaction': updated_tx, 'message': 'Transaction updated successfully!'})

@app.route('/api/goals', methods=['GET', 'POST'])
def manage_goals():
    """List or create savings goals."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    if request.method == 'GET':
        cursor.execute('SELECT * FROM savings_goals ORDER BY id ASC')
        goals = []
        for row in cursor.fetchall():
            g = dict(row)
            target = float(g['target_amount'])
            current = float(g['current_amount'])
            pct = round((current / target * 100), 1) if target > 0 else 0
            g['progress_percentage'] = min(pct, 100.0)
            g['is_completed'] = current >= target
            g['remaining_amount'] = max(0.0, round(target - current, 2))
            goals.append(g)
        conn.close()
        return jsonify({'success': True, 'goals': goals})

    # POST: Add new goal
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    try:
        target_amount = float(data.get('target_amount', 0))
        current_amount = float(data.get('current_amount', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid numeric values for amounts'}), 400

    if not title:
        return jsonify({'success': False, 'error': 'Goal title is required'}), 400
    if target_amount <= 0:
        return jsonify({'success': False, 'error': 'Target amount must be greater than zero'}), 400
    if current_amount < 0:
        return jsonify({'success': False, 'error': 'Current amount cannot be negative'}), 400

    target_date = data.get('target_date') or None
    emoji = data.get('emoji') or '🎯'
    color = data.get('color') or '#10B981'

    cursor.execute('''
        INSERT INTO savings_goals (title, target_amount, current_amount, target_date, emoji, color)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (title, target_amount, current_amount, target_date, emoji, color))
    goal_id = cursor.lastrowid
    conn.commit()

    cursor.execute('SELECT * FROM savings_goals WHERE id = ?', (goal_id,))
    new_goal = dict(cursor.fetchone())
    conn.close()

    return jsonify({'success': True, 'goal': new_goal, 'message': 'Savings goal established!'}), 201

@app.route('/api/goals/<int:goal_id>', methods=['PUT', 'DELETE'])
def goal_detail(goal_id):
    """Update or delete savings goal."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM savings_goals WHERE id = ?', (goal_id,))
    goal = cursor.fetchone()
    if not goal:
        conn.close()
        return jsonify({'success': False, 'error': 'Savings goal not found'}), 404

    if request.method == 'DELETE':
        cursor.execute('DELETE FROM savings_goals WHERE id = ?', (goal_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Savings goal deleted successfully'})

    # PUT: Update
    data = request.get_json() or {}
    title = (data.get('title') or goal['title']).strip()
    try:
        target_amount = float(data.get('target_amount', goal['target_amount']))
        current_amount = float(data.get('current_amount', goal['current_amount']))
    except (ValueError, TypeError):
        conn.close()
        return jsonify({'success': False, 'error': 'Invalid amount value'}), 400

    target_date = data.get('target_date', goal['target_date'])
    emoji = data.get('emoji', goal['emoji'])
    color = data.get('color', goal['color'])

    cursor.execute('''
        UPDATE savings_goals
        SET title = ?, target_amount = ?, current_amount = ?, target_date = ?, emoji = ?, color = ?
        WHERE id = ?
    ''', (title, target_amount, current_amount, target_date, emoji, color, goal_id))
    conn.commit()

    cursor.execute('SELECT * FROM savings_goals WHERE id = ?', (goal_id,))
    updated_goal = dict(cursor.fetchone())
    conn.close()

    return jsonify({'success': True, 'goal': updated_goal, 'message': 'Savings goal updated!'})

@app.route('/api/goals/<int:goal_id>/deposit', methods=['POST'])
def goal_deposit(goal_id):
    """Add funds to a savings goal and optionally record as a savings expense."""
    data = request.get_json() or {}
    try:
        deposit_amount = float(data.get('amount', 0))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': 'Invalid deposit amount'}), 400

    if deposit_amount <= 0:
        return jsonify({'success': False, 'error': 'Deposit amount must be greater than zero'}), 400

    record_as_expense = bool(data.get('record_expense', True))

    conn = database.get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM savings_goals WHERE id = ?', (goal_id,))
    goal = cursor.fetchone()
    if not goal:
        conn.close()
        return jsonify({'success': False, 'error': 'Savings goal not found'}), 404

    new_total = float(goal['current_amount']) + deposit_amount
    cursor.execute('UPDATE savings_goals SET current_amount = ? WHERE id = ?', (new_total, goal_id))

    # Record as a savings transaction
    if record_as_expense:
        today_str = datetime.now().strftime('%Y-%m-%d')
        desc = f"Saved for {goal['title']}"
        cursor.execute('''
            INSERT INTO transactions (type, amount, category_id, description, date, notes, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('expense', deposit_amount, 'savings', desc, today_str, f"Deposit toward goal #{goal_id}", 'debit'))

    conn.commit()

    cursor.execute('SELECT * FROM savings_goals WHERE id = ?', (goal_id,))
    updated_goal = dict(cursor.fetchone())
    conn.close()

    is_celebration = new_total >= float(updated_goal['target_amount'])
    return jsonify({
        'success': True,
        'goal': updated_goal,
        'new_total': new_total,
        'is_completed': is_celebration,
        'message': f'🎉 Successfully deposited to {updated_goal["title"]}!'
    })

@app.route('/api/reset-sample-data', methods=['POST'])
def reset_sample_data():
    """Resets database with fresh realistic student sample data."""
    conn = database.get_db_connection()
    database.seed_sample_data(conn)
    conn.close()
    return jsonify({'success': True, 'message': 'Sample data successfully restored!'})

@app.route('/api/export/csv', methods=['GET'])
def export_csv():
    """Export all transactions as a CSV file."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, t.date, t.type, t.amount, t.category_id, c.name as category_name,
               t.description, t.payment_method, t.notes
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.date DESC, t.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Type', 'Amount', 'Category ID', 'Category Name', 'Description', 'Payment Method', 'Notes'])

    for row in rows:
        writer.writerow([
            row['id'], row['date'], row['type'], f"{row['amount']:.2f}",
            row['category_id'], row['category_name'] or 'Income',
            row['description'], row['payment_method'], row['notes'] or ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=student_budget_transactions.csv'}
    )

if __name__ == '__main__':
    print("[CampusBudget] Student Budget Planner running on http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)
