# 💰 FinSight — Personal Finance Intelligence Platform

A full-stack web application that helps college students understand 
and improve their spending habits through intelligent insights, 
visual breakdowns, and a what-if savings simulator.

## 🚀 Live Demo
[Link coming soon — deploying on Render]

## 📸 Screenshots

### Dashboard
![Dashboard](screenshots/dashboard.png)

### Honest Mirror Report
![Report](screenshots/report.png)

### What-If Simulator
![Simulator](screenshots/simulator.png)

## ✨ Features

- **Multi-user Authentication** — Secure signup/login with hashed passwords
- **Transaction Logging** — Log expenses with category, amount, and date
- **Category Breakdown** — Doughnut chart showing spending distribution
- **Spending Trends** — Month-over-month line chart with change indicators
- **Honest Mirror Report** — Plain-English monthly verdict with health score, 
  insights, and 5-year financial projection
- **What-If Simulator** — Interactive calculator showing how cutting spending 
  compounds into long-term savings
- **Unified Dashboard** — All key stats, charts, and recent transactions in one view

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLite (local), PostgreSQL (production) |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login, Werkzeug password hashing |
| Frontend | HTML5, Bootstrap 5, Chart.js |
| Deployment | Render |

## ⚙️ Run Locally

```bash
# Clone the repo
git clone https://github.com/[your-username]/finsight.git
cd finsight

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open `http://localhost:5000` in your browser.

## 👩‍💻 Built By

Nistha Agarwal — [linkedin.com/in/nistha-agarwal-a83966326/](https://linkedin.com/in/nistha-agarwal-a83966326/)