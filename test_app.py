import unittest
import json
import os
import tempfile
import database
from app import app

class StudentBudgetTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary database for test isolation
        self.db_fd, self.temp_db_path = tempfile.mkstemp()
        database.init_db(self.temp_db_path)
        
        # Override the get_db_connection in database module for testing
        self.original_get_db = database.get_db_connection
        database.get_db_connection = lambda p=None: self.original_get_db(self.temp_db_path)
        
        app.config['TESTING'] = True
        self.client = app.test_client()

    def tearDown(self):
        database.get_db_connection = self.original_get_db
        try:
            os.close(self.db_fd)
        except OSError:
            pass
        import gc
        gc.collect()
        try:
            if os.path.exists(self.temp_db_path):
                os.remove(self.temp_db_path)
        except PermissionError:
            pass

    def test_summary_endpoint(self):
        response = self.client.get('/api/summary')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('monthly_budget', data)
        self.assertIn('total_spent', data)
        self.assertIn('remaining_balance', data)
        self.assertIn('categories', data)
        self.assertEqual(len(data['categories']), 5)

    def test_add_and_get_transaction(self):
        # Add valid expense
        new_tx = {
            'type': 'expense',
            'amount': 25.50,
            'category_id': 'food',
            'description': 'Late night study pizza',
            'date': '2026-10-14',
            'notes': 'Split with dorm roommate',
            'payment_method': 'debit'
        }
        res = self.client.post('/api/transactions', json=new_tx)
        self.assertEqual(res.status_code, 201)
        tx_data = json.loads(res.data)
        self.assertTrue(tx_data['success'])
        tx_id = tx_data['transaction']['id']

        # Verify in list
        list_res = self.client.get('/api/transactions?category=food')
        self.assertEqual(list_res.status_code, 200)
        list_data = json.loads(list_res.data)
        found = any(t['id'] == tx_id for t in list_data['transactions'])
        self.assertTrue(found)

        # Update transaction
        update_res = self.client.put(f'/api/transactions/{tx_id}', json={
            'amount': 30.00,
            'description': 'Late night study pizza + garlic bread'
        })
        self.assertEqual(update_res.status_code, 200)
        up_data = json.loads(update_res.data)
        self.assertEqual(up_data['transaction']['amount'], 30.00)

        # Delete transaction
        del_res = self.client.delete(f'/api/transactions/{tx_id}')
        self.assertEqual(del_res.status_code, 200)

    def test_invalid_transaction_validation(self):
        # Negative amount
        res = self.client.post('/api/transactions', json={
            'type': 'expense',
            'amount': -10,
            'category_id': 'food',
            'description': 'Invalid'
        })
        self.assertEqual(res.status_code, 400)

        # Empty description
        res = self.client.post('/api/transactions', json={
            'type': 'expense',
            'amount': 15,
            'category_id': 'food',
            'description': ''
        })
        self.assertEqual(res.status_code, 400)

    def test_budget_planning_update(self):
        # Update monthly budget and category budgets
        payload = {
            'monthly_budget': 900.0,
            'categories': [
                {'id': 'food', 'planned_budget': 300.0},
                {'id': 'travel', 'planned_budget': 100.0},
                {'id': 'education', 'planned_budget': 200.0},
                {'id': 'entertainment', 'planned_budget': 100.0},
                {'id': 'savings', 'planned_budget': 200.0}
            ]
        }
        res = self.client.post('/api/budget', json=payload)
        self.assertEqual(res.status_code, 200)

        summary_res = self.client.get('/api/summary')
        summary_data = json.loads(summary_res.data)
        self.assertEqual(summary_data['monthly_budget'], 900.0)
        self.assertEqual(summary_data['sum_planned_categories'], 900.0)
        self.assertEqual(summary_data['allocation_status'], 'balanced')

    def test_savings_goals_and_deposit(self):
        # Create goal
        new_goal = {
            'title': 'New Tablet for Notes',
            'target_amount': 400.0,
            'current_amount': 50.0,
            'target_date': '2026-12-01',
            'emoji': '📱',
            'color': '#8B5CF6'
        }
        res = self.client.post('/api/goals', json=new_goal)
        self.assertEqual(res.status_code, 201)
        goal_data = json.loads(res.data)
        goal_id = goal_data['goal']['id']

        # Deposit funds into goal
        dep_res = self.client.post(f'/api/goals/{goal_id}/deposit', json={'amount': 100.0, 'record_expense': True})
        self.assertEqual(dep_res.status_code, 200)
        dep_data = json.loads(dep_res.data)
        self.assertEqual(dep_data['new_total'], 150.0)

        # Delete goal
        del_res = self.client.delete(f'/api/goals/{goal_id}')
        self.assertEqual(del_res.status_code, 200)

    def test_index_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'CampusBudget', res.data)
        self.assertIn(b'Spending Analytics', res.data)

    def test_static_assets(self):
        css_res = self.client.get('/static/css/style.css')
        self.assertEqual(css_res.status_code, 200)
        css_res.close()
        js_res = self.client.get('/static/js/app.js')
        self.assertEqual(js_res.status_code, 200)
        js_res.close()

    def test_settings_update(self):
        payload = {
            'student_name': 'Jordan Lee',
            'college_name': 'Tech Institute',
            'currency_symbol': '€'
        }
        res = self.client.post('/api/settings', json=payload)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertEqual(data['settings']['student_name'], 'Jordan Lee')
        self.assertEqual(data['settings']['currency_symbol'], '€')

    def test_csv_export(self):
        res = self.client.get('/api/export/csv')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'text/csv')
        self.assertIn(b'Description', res.data)

if __name__ == '__main__':
    unittest.main()
