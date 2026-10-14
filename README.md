# 🎓 CampusBudget — Student Budget & Expense Planner

An encouraging, responsive, and thoughtfully designed financial management platform built specifically for students. CampusBudget helps students balance everyday campus life—from cafeteria runs and textbook costs to semester transit passes, weekend social outings, and rainy-day savings.

![CampusBudget Preview](https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?auto=format&fit=crop&w=1200&q=80)

---

## ✨ Design & Visual Philosophy

CampusBudget avoids dry, confusing accounting spreadsheets. Instead, it provides a warm, student-friendly interface:
- **Palette**: Warm cream (`#FAF8F5`) and clean white cards paired with confident Royal Indigo (`#6366F1`), vivid Coral (`#FF6B6B`), Sky Azure (`#0EA5E9`), Royal Violet (`#8B5CF6`), Sunshine Amber (`#F59E0B`), and Lush Emerald (`#10B981`).
- **Typography**: Display headings set in **Outfit** (modern, geometric, friendly) paired with interface text in **Plus Jakarta Sans** and financial tabular figures in **JetBrains Mono**.
- **Visual Centerpiece**: Monthly financial health dashboard with remaining allowance, safe daily spend calculation, real-time pacing advice, and multi-color category consumption bars.
- **Micro-Interactions**: Smooth glassmorphism navigation, dark/light theme switch, floating action buttons for mobile, responsive modals with quick amount buttons (+$5, +$10, +$25, +$50), and celebratory confetti animations upon hitting savings milestones!

---

## 🚀 Core Features

### 1. 📊 Student Dashboard
- **Monthly Spending Centerpiece**: Prominently displays Remaining Allowance, Planned Budget, Total Expenses, and Net Cashflow (Income vs Spent).
- **Daily Safe Allowance Gauge**: Automatically calculates how much you can safely spend per day (`Remaining / Days left in month`) so you never run out of money before the month ends.
- **Five Core Categories Grid**:
  - 🍕 **Food & Dining**: Cafeteria meals, groceries, late-night study snacks, coffee.
  - 🚌 **Travel & Commute**: Metro/subway passes, bus fares, bike rentals, ride shares.
  - 📚 **Education & Books**: Secondhand textbooks, lab notebooks, stationery, software subscriptions.
  - 🎮 **Entertainment & Fun**: Campus film club, weekend outings, streaming, gaming.
  - 💰 **Savings & Cushion**: Emergency fund, tech upgrades, summer trip stash.
- **Visual Analytics**: Interactive switch between **Donut Breakdown** and **Planned vs Actual Comparison Bar Chart** (powered by Chart.js).
- **Smart Student Insights**:
  - Category closest to its budget limit.
  - Largest single expense of the month.
  - Total stash accumulated across savings goals.

### 2. ⚖️ Budget Planning & Allocation Inspector
- **Overall Monthly Allowance**: Set or adjust your total funding for the month.
- **Interactive Category Allocators**: Fine-tune each category using sliders or numeric inputs.
- **Budget Mismatch Detection**:
  - Live indicator comparing the sum of categories against your total monthly budget.
  - **Unallocated Cushion**: Alerts you when you have unassigned funds and offers a 1-click **"Distribute to Savings"** button.
  - **Over-allocated Warning**: Alerts you when planned amounts exceed your budget and provides an **"Auto-Fit / Auto-Proportion"** button to scale allocations seamlessly.

### 3. 🎯 Savings Goals Hub
- Create custom savings targets (e.g. *New M3 MacBook*, *Summer Roadtrip*, *Emergency Cushion*, *Graduation Photography*).
- Visual progress bars with percentage completion and countdown to target date.
- **Deposit Funds**: Quick modal to add money to any goal, with optional automatic logging as a savings expense in the monthly budget.
- **Confetti Celebration**: Triggers celebratory particles when a goal reaches 100%!

### 4. 💳 Transaction Ledger
- **Complete CRUD**: Create, view, search, filter, edit, and delete transactions.
- **Type Toggle**: Easily switch between **Expenses** and **Income** (scholarships, part-time jobs, tutoring, gifts).
- **Filters & Search**: Real-time debounced search by description or note, category filter chips, type filters, and multiple sorting options (Newest, Oldest, Highest, Lowest).
- **Confirmation Protection**: Non-destructive confirmation dialog before deleting any record.
- **CSV Data Export**: 1-click download of all transaction history for your own backups or records.
- **Sample Data Reset**: 1-click button to restore realistic student test data at any time.

### 5. 💡 Student Money Guide
- Practical, actionable student finance advice covering:
  - Unlocking student discounts (UNiDAYS, Student Beans, GitHub Student Pack).
  - Sunday meal-prep hacks to save up to $120/month.
  - Textbook rental and library course reserve strategies.
  - University transit subsidies and campus bike co-ops.
  - The student-adapted 50/30/20 budgeting rule.

---

## 🔒 Data & Privacy

- **100% Local & Private**: All data is stored in a local SQLite database (`budget.db`) directly on your machine.
- **Zero Third-Party Financial Linking**: CampusBudget never asks for, stores, or connects to your bank credentials or account numbers.
- **Offline First**: The application runs completely on your local network/machine.

---

## 🛠️ Stack & Architecture

- **Backend**: Python 3 with Flask 3.1.3 and standard SQLite3.
- **Frontend**: HTML5, Tailwind CSS (via CDN), Google Fonts (Plus Jakarta Sans, Outfit, JetBrains Mono), Lucide Icons, Chart.js 4.4, and Canvas-Confetti.
- **Testing**: Python standard `unittest` test suite with 9 passing tests covering all API endpoints, data validation, budget mismatch calculations, and template rendering.

---

## 🏃 Quick Start Guide

### Prerequisites
- Python 3.8+ (Python 3.12+ recommended)
- Flask (`pip install Flask` — already installed if running in this environment)

### Running the App

1. Open your terminal in the project directory:
   ```bash
   py app.py
   # Or on macOS/Linux:
   python3 app.py
   ```

2. Open your web browser and visit:
   ```
   http://127.0.0.1:5000
   ```

3. The application comes pre-loaded with realistic student sample data for immediate exploration!

---

## 🧪 Running Automated Tests

To run the unit and integration tests:

```bash
py -m unittest test_app.py
# Or:
python -m unittest test_app.py
```

### Checks Passed:
- `test_summary_endpoint`: Validates summary metrics, calculation of remaining balance, and category structures.
- `test_add_and_get_transaction`: Validates full CRUD operations for income and expenses.
- `test_invalid_transaction_validation`: Verifies boundary conditions (negative amounts, empty descriptions).
- `test_budget_planning_update`: Validates category updates and sum-check mismatch detection.
- `test_savings_goals_and_deposit`: Verifies creating goals, depositing funds, and automatic expense recording.
- `test_csv_export`: Validates generation and header output for downloadable CSV transactions.
- `test_index_page`: Confirms template rendering and HTML integrity.
- `test_static_assets`: Confirms delivery of custom CSS and JavaScript files.
- `test_settings_update`: Confirms persistence of user name, university, and currency symbol.

---

## 📂 Project Structure

```
project3/
├── app.py                # Main Flask application and RESTful API endpoints
├── database.py           # SQLite database schema, connections, and sample data seeder
├── test_app.py           # Automated unit and API integration tests
├── budget.db             # Local SQLite database file (created automatically)
├── README.md             # Documentation and usage instructions
├── templates/
│   └── index.html        # Responsive frontend template with student-centric UI
└── static/
    ├── css/
    │   └── style.css     # Custom animations, glassmorphism, and color variables
    └── js/
        └── app.js        # State manager, Chart.js graphs, modals, and reactive updates
```
