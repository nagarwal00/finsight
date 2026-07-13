from sqlalchemy import extract
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from config import Config
from models import db, User
from models import db, User, Transaction

app = Flask(__name__)
app.jinja_env.globals.update(enumerate=enumerate)
app.config.from_object(Config)



# Initialize extensions
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables on first run
with app.app_context():
    db.create_all()

# ─── Home ───────────────────────────────────────────
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# ─── Signup ─────────────────────────────────────────
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        monthly_income = request.form.get('monthly_income') or 0

        # Check if email already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('signup'))

        # Create new user
        user = User(name=name, email=email, monthly_income=float(monthly_income))
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')

# ─── Login ──────────────────────────────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))

        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# ─── Logout ─────────────────────────────────────────
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ─── Dashboard ──────────────────────────────────────
# ─── Dashboard ──────────────────────────────────────
@app.route('/dashboard')
@login_required
def dashboard():
    from datetime import datetime
    from sqlalchemy import extract
    from collections import defaultdict

    now = datetime.now()

    # This month's transactions
    month_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).filter(
        extract('year', Transaction.date) == now.year,
        extract('month', Transaction.date) == now.month
    ).all()

    month_spent = round(sum(t.amount for t in month_transactions), 2)
    month_count = len(month_transactions)
    income = current_user.monthly_income or 0
    savings = round(income - month_spent, 2)
    savings_rate = round((savings / income) * 100, 1) if income > 0 else 0

    # Health score
    if income == 0:
        health_score = 50
    elif savings_rate < 0:
        health_score = 10
    elif savings_rate < 10:
        health_score = 30
    elif savings_rate < 20:
        health_score = 55
    elif savings_rate < 30:
        health_score = 70
    else:
        health_score = 90

    # Category breakdown for mini pie
    category_totals = defaultdict(float)
    for t in month_transactions:
        category_totals[t.category or 'Other'] += t.amount
    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    category_labels = [c[0] for c in sorted_cats]
    category_values = [round(c[1], 2) for c in sorted_cats]

    # Trend data (all months)
    all_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date).all()

    monthly = defaultdict(lambda: {'total': 0, 'sort': ''})
    for t in all_transactions:
        key = t.date.strftime('%b %Y')
        monthly[key]['total'] += t.amount
        monthly[key]['sort'] = t.date.strftime('%Y-%m')

    sorted_months = sorted(monthly.items(), key=lambda x: x[1]['sort'])
    trend_labels = [m[0] for m in sorted_months]
    trend_values = [round(m[1]['total'], 2) for m in sorted_months]

    # Recent 5 transactions
    recent_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date.desc()).limit(5).all()

    stats = {
        'month_spent': month_spent,
        'month_count': month_count,
        'savings': savings,
        'savings_rate': savings_rate,
        'health_score': health_score,
        'category_labels': category_labels,
        'category_values': category_values,
        'trend_labels': trend_labels,
        'trend_values': trend_values
    }

    return render_template('dashboard.html',
        user=current_user,
        stats=stats,
        recent_transactions=recent_transactions,
        current_month=now.strftime('%B %Y')
    )

# ─── Add Transaction ────────────────────────────────
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    if request.method == 'POST':
        description = request.form.get('description')
        amount = request.form.get('amount')
        category = request.form.get('category')
        date_str = request.form.get('date')

        from datetime import datetime
        transaction = Transaction(
            user_id=current_user.id,
            description=description,
            amount=float(amount),
            category=category,
            date=datetime.strptime(date_str, '%Y-%m-%d'),
            source='manual'
        )
        db.session.add(transaction)
        db.session.commit()

        flash('Transaction added successfully!', 'success')
        return redirect(url_for('add_transaction'))

    return render_template('add_transaction.html', user=current_user)

# ─── View Transactions ───────────────────────────────
@app.route('/transactions')
@login_required
def transactions():
    from datetime import datetime

    category_filter = request.args.get('category', '')
    month_filter = request.args.get('month', '')

    query = Transaction.query.filter_by(user_id=current_user.id)

    if category_filter:
        query = query.filter_by(category=category_filter)

    if month_filter:
        year, month = month_filter.split('-')
        query = query.filter(
            extract('year', Transaction.date) == int(year),
            extract('month', Transaction.date) == int(month)
        )

    all_transactions = query.order_by(Transaction.date.desc()).all()

    total_spent = round(sum(t.amount for t in all_transactions), 2)
    avg_amount = round(total_spent / len(all_transactions), 2) if all_transactions else 0

    return render_template('transactions.html',
        user=current_user,
        transactions=all_transactions,
        total_spent=total_spent,
        avg_amount=avg_amount,
        selected_category=category_filter,
        selected_month=month_filter
    )

# ─── Delete Transaction ──────────────────────────────
@app.route('/delete/<int:transaction_id>')
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)

    # Make sure users can only delete their own transactions
    if transaction.user_id != current_user.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('transactions'))

    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted.', 'success')
    return redirect(url_for('transactions'))

# ─── Category Breakdown ──────────────────────────────
@app.route('/breakdown')
@login_required
def breakdown():
    from sqlalchemy import extract

    month_filter = request.args.get('month', '')
    query = Transaction.query.filter_by(user_id=current_user.id)

    if month_filter:
        year, month = month_filter.split('-')
        query = query.filter(
            extract('year', Transaction.date) == int(year),
            extract('month', Transaction.date) == int(month)
        )

    all_transactions = query.all()

    if not all_transactions:
        return render_template('breakdown.html',
            user=current_user,
            breakdown=[],
            total_spent=0,
            total_count=0,
            labels=[],
            values=[],
            selected_month=month_filter
        )

    # Group by category
    category_data = {}
    for t in all_transactions:
        cat = t.category or 'Other'
        if cat not in category_data:
            category_data[cat] = {'total': 0, 'count': 0}
        category_data[cat]['total'] += t.amount
        category_data[cat]['count'] += 1

    total_spent = round(sum(t.amount for t in all_transactions), 2)
    total_count = len(all_transactions)

    # Build breakdown list sorted by total descending
    breakdown_list = []
    for cat, data in sorted(category_data.items(), key=lambda x: x[1]['total'], reverse=True):
        percentage = round((data['total'] / total_spent) * 100, 1)
        breakdown_list.append({
            'category': cat,
            'total': round(data['total'], 2),
            'count': data['count'],
            'percentage': percentage
        })

    labels = [item['category'] for item in breakdown_list]
    values = [item['total'] for item in breakdown_list]

    return render_template('breakdown.html',
        user=current_user,
        breakdown=breakdown_list,
        total_spent=total_spent,
        total_count=total_count,
        labels=labels,
        values=values,
        selected_month=month_filter
    )

# ─── Spending Trends ─────────────────────────────────
@app.route('/trends')
@login_required
def trends():
    from sqlalchemy import extract
    from collections import defaultdict

    all_transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).order_by(Transaction.date).all()

    if not all_transactions:
        return render_template('trends.html',
            user=current_user,
            monthly_data=[],
            month_labels=[],
            month_values=[],
            highest_month='—', highest_amount=0,
            lowest_month='—', lowest_amount=0,
            avg_monthly=0, trend='stable'
        )

# Group transactions by month — sorted chronologically
    monthly = defaultdict(lambda: {'total': 0, 'count': 0})
    month_order = {}
    for t in all_transactions:
        key = t.date.strftime('%b %Y')
        sort_key = t.date.strftime('%Y-%m')  # for correct chronological sorting
        monthly[key]['total'] += t.amount
        monthly[key]['count'] += 1
        month_order[key] = sort_key

    # Build ordered list sorted by actual date not alphabetically
    monthly_data = []
    for month_key in sorted(monthly.keys(), key=lambda x: month_order[x]):
        monthly_data.append({
            'month': month_key,
            'total': round(monthly[month_key]['total'], 2),
            'count': monthly[month_key]['count']
        })

    month_labels = [item['month'] for item in monthly_data]
    month_values = [item['total'] for item in monthly_data]

    # Summary stats
    highest = max(monthly_data, key=lambda x: x['total'])
    lowest = min(monthly_data, key=lambda x: x['total'])
    avg_monthly = round(sum(month_values) / len(month_values), 2)

    # Trend — compare last two months
    if len(month_values) >= 2:
        if month_values[-1] > month_values[-2]:
            trend = 'up'
        elif month_values[-1] < month_values[-2]:
            trend = 'down'
        else:
            trend = 'stable'
    else:
        trend = 'stable'

    return render_template('trends.html',
        user=current_user,
        monthly_data=monthly_data,
        month_labels=month_labels,
        month_values=month_values,
        highest_month=highest['month'],
        highest_amount=highest['total'],
        lowest_month=lowest['month'],
        lowest_amount=lowest['total'],
        avg_monthly=avg_monthly,
        trend=trend
    )

# ─── Honest Mirror Report ────────────────────────────
@app.route('/report')
@login_required
def report():
    from sqlalchemy import extract
    from datetime import datetime

    # Default to current month
    now = datetime.now()
    selected_month = request.args.get('month', now.strftime('%Y-%m'))
    year, month = selected_month.split('-')

    transactions = Transaction.query.filter_by(
        user_id=current_user.id
    ).filter(
        extract('year', Transaction.date) == int(year),
        extract('month', Transaction.date) == int(month)
    ).all()

    if not transactions:
        return render_template('report.html',
            user=current_user,
            report=None,
            selected_month=selected_month
        )

    # Core numbers
    total_spent = round(sum(t.amount for t in transactions), 2)
    income = current_user.monthly_income or 0
    monthly_savings = round(income - total_spent, 2) if income > 0 else 0
    savings_rate = round((monthly_savings / income) * 100, 1) if income > 0 else 0
    transaction_count = len(transactions)

    # Category breakdown
    category_totals = {}
    for t in transactions:
        cat = t.category or 'Other'
        category_totals[cat] = category_totals.get(cat, 0) + t.amount
    top_category = max(category_totals, key=category_totals.get)
    top_category_amount = round(category_totals[top_category], 2)
    top_category_pct = round((top_category_amount / total_spent) * 100, 1)

    # Health score calculation
    health_score = 100
    if income > 0:
        if savings_rate < 0:
            health_score = 10
        elif savings_rate < 10:
            health_score = 30
        elif savings_rate < 20:
            health_score = 55
        elif savings_rate < 30:
            health_score = 70
        else:
            health_score = 90
    else:
        health_score = 50  # no income set

    # Verdict text
    if income == 0:
        verdict = f"You logged {transaction_count} transactions totalling ₹{total_spent} this month. Set your monthly income in your profile to unlock your full financial health score and savings analysis."
    elif savings_rate < 0:
        verdict = f"You spent ₹{abs(monthly_savings)} more than you earned this month. This is a red flag — you're running a deficit. Immediate action is needed to cut discretionary spending."
    elif savings_rate < 20:
        verdict = f"You saved {savings_rate}% of your income this month. That's below the recommended 20% minimum. Your biggest drain is {top_category} at ₹{top_category_amount} ({top_category_pct}% of spending)."
    elif savings_rate < 40:
        verdict = f"Decent month — you saved {savings_rate}% of your income. You're in the safe zone but there's room to do better. Watch your {top_category} spending which is your largest category."
    else:
        verdict = f"Excellent month! You saved {savings_rate}% of your income. That's well above average. Keep this up and your future self will thank you."

    # Insights
    insights = []

    # Top category insight
    insights.append({
        'icon': '🏆',
        'title': f'{top_category} is your biggest expense',
        'detail': f'₹{top_category_amount} ({top_category_pct}% of total spending) went to {top_category} this month.'
    })

    # Transaction frequency
    avg_per_day = round(total_spent / 30, 2)
    insights.append({
        'icon': '📅',
        'title': f'You spend ₹{avg_per_day} per day on average',
        'detail': f'{transaction_count} transactions this month, averaging ₹{round(total_spent/transaction_count, 2)} each.'
    })

    # Savings insight
    if income > 0:
        if monthly_savings > 0:
            insights.append({
                'icon': '💰',
                'title': f'You saved ₹{monthly_savings} this month',
                'detail': f'That\'s {savings_rate}% of your income. Financial advisors recommend saving at least 20%.'
            })
        else:
            insights.append({
                'icon': '⚠️',
                'title': f'You overspent by ₹{abs(monthly_savings)}',
                'detail': 'You spent more than your income this month. Review your largest expense categories immediately.'
            })

    # Subscriptions check
    sub_total = category_totals.get('Subscriptions', 0)
    if sub_total > 0:
        insights.append({
            'icon': '📱',
            'title': f'₹{round(sub_total, 2)} on subscriptions',
            'detail': f'That\'s ₹{round(sub_total * 12, 2)} per year. Are you actively using all of them?'
        })

    # 5 year projection
    five_year_savings = round(monthly_savings * 60, 2) if income > 0 else 0
    five_year_invested = round(monthly_savings * ((1.07**5 - 1) / 0.07) * 12, 2) if monthly_savings > 0 else 0

    longview_message = ''
    if monthly_savings > 0:
        longview_message = f"If you maintain this savings rate for 5 years and invest at 7% annual returns, you could have ₹{five_year_invested} — without doing anything extra."
    elif income > 0:
        longview_message = "You're currently not saving anything. Even saving ₹500/month invested at 7% gives you ₹35,000+ in 5 years."

    # Action plan
    action_plan = []
    if top_category_pct > 40:
        action_plan.append(f"Set a monthly budget cap for {top_category} — aim to reduce it by 15%")
    if sub_total > 300:
        action_plan.append("Audit your subscriptions — cancel at least one you rarely use")
    if income > 0 and savings_rate < 20:
        action_plan.append("Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings")
    action_plan.append("Log every transaction this month — awareness alone reduces spending by ~10%")
    action_plan.append("Check your breakdown page weekly to catch overspending early")

    month_name = datetime(int(year), int(month), 1).strftime('%B %Y')

    report_data = {
        'month_name': month_name,
        'total_spent': total_spent,
        'income': income,
        'monthly_savings': monthly_savings,
        'savings_rate': savings_rate,
        'transaction_count': transaction_count,
        'health_score': health_score,
        'verdict': verdict,
        'insights': insights,
        'five_year_savings': five_year_savings,
        'five_year_invested': five_year_invested,
        'longview_message': longview_message,
        'action_plan': action_plan
    }

    return render_template('report.html',
        user=current_user,
        report=report_data,
        selected_month=selected_month
    )

# ─── What-If Simulator ───────────────────────────────
@app.route('/simulator')
@login_required
def simulator():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()

    # Get average monthly spend per category
    from collections import defaultdict
    category_totals_raw = defaultdict(list)
    for t in transactions:
        cat = t.category or 'Other'
        month_key = t.date.strftime('%Y-%m')
        category_totals_raw[cat].append((month_key, t.amount))

    # Average monthly spend per category
    category_totals = {}
    for cat, entries in category_totals_raw.items():
        months = len(set(e[0] for e in entries))
        total = sum(e[1] for e in entries)
        category_totals[cat] = round(total / max(months, 1), 2)

    # Sort by amount descending
    category_totals = dict(
        sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    )

    # Pre-build scenario table (based on total monthly spending)
    total_monthly = sum(category_totals.values())
    scenarios = []
    for pct in [10, 20, 30, 50]:
        monthly = round(total_monthly * pct / 100, 2)
        flat = round(monthly * 60, 2)
        monthly_rate = 0.07 / 12
        invested = round(monthly * ((pow(1 + monthly_rate, 60) - 1) / monthly_rate), 2)
        scenarios.append({
            'label': f'{pct}% of total spending',
            'monthly': monthly,
            'flat': flat,
            'invested': invested
        })

    return render_template('simulator.html',
        user=current_user,
        category_totals=category_totals,
        scenarios=scenarios
    )
if __name__ == '__main__':
    app.run(debug=True)