# Khael Solutions — Operations Management System

A Django-based internal management system for tracking jobs, inventory, purchases, payments, alerts, and BI reports for Khael Solutions.

---

## Features

- **Job Management** — Create, assign, and track jobs through their lifecycle (Pending → In Progress → Completed)
- **Resource & Inventory** — Track stock levels, record usage per job, and get low-stock alerts
- **Purchase Orders** — Log purchase orders and link them to inventory resources
- **Client Payments** — Record payments against completed jobs (cash, mobile money, bank transfer, cheque)
- **Alert Engine** — Automated rule-based checks for overdue jobs, low stock, unresolved alerts, and budget overruns
- **BI Reports** — AI-powered business intelligence reports generated via OpenAI (gpt-4o-mini)
- **User & Department Management** — Role-based access control (Super Admin, Manager, Staff) with department assignments
- **Background Scheduler** — APScheduler runs alert checks automatically on a schedule

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 6.0.2 |
| Database | SQLite (dev) / MySQL (prod) |
| Background Jobs | APScheduler + django-apscheduler |
| AI Reports | OpenAI API (gpt-4o-mini) |
| Frontend | Bootstrap 5 + Bootstrap Icons |
| Environment | python-dotenv |

---

## Project Structure

```
khael_solutions/
├── core/                        # Single Django app (all logic lives here)
│   ├── models.py                # All models: User, Job, Resource, Purchase, Payment, Alert, Report, ...
│   ├── views.py                 # All views (CBV + FBV)
│   ├── urls.py                  # All URL patterns (namespace: core)
│   ├── services.py              # Business logic layer
│   ├── permissions.py           # Role-based access mixins
│   ├── scheduler.py             # APScheduler job definitions
│   ├── context_processors.py   # Global template context (e.g. alert_count)
│   └── admin.py                 # Django admin registrations
├── khael_solutions/             # Django project settings
│   ├── settings.py
│   └── urls.py
├── templates/                   # Flat template directory
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── jobs/
│   ├── resources/
│   ├── purchases/
│   ├── payments/
│   ├── alerts/
│   ├── reports/
│   ├── users/
│   └── departments/
├── static/
│   ├── css/main.css             # All styles
│   └── js/main.js               # All JavaScript
├── utils.py                     # Shared utilities
├── manage.py
├── requirements.txt
└── .env                         # Environment variables (not committed)
```

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd khael_solutions
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=replace_with_a_generated_secret
OPENAI_API_KEY=your_openai_api_key_here
SMSONLINE_API_KEY=your_smsonline_api_key_here
```

### 4. Run migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Load sample data (optional)

```bash
python manage.py load_dummy_data
```

### 6. Start the development server

```bash
python manage.py runserver
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

---

## User Roles

| Role | Permissions |
|---|---|
| **Super Admin** | Full access to all features including user and department management |
| **Manager** | Access to jobs, resources, purchases, payments, alerts, and reports |
| **Staff** | Limited access — view and update assigned jobs |

---

## Key Models

| Model | Description |
|---|---|
| `User` | Custom user with role and department |
| `Department` | Service department with optional Head of Department |
| `Job` | Client job with service type, priority, status, and price |
| `JobUpdate` | Timestamped status updates on a job |
| `Resource` | Inventory item with stock level and reorder threshold |
| `ResourceUsage` | Records resource consumption per job |
| `Purchase` | Purchase order linked to a supplier |
| `PurchaseResource` | Line items on a purchase order |
| `Payment` | Client payment recorded against a job |
| `Alert` | System-generated alert from the rule engine |
| `Report` | AI-generated BI report |

### Job Service Types
`printing` · `network_it` · `multimedia` · `general`

### Payment Methods
`cash` · `mobile_money` · `bank_transfer` · `cheque`

---

## Alert Engine

The system runs 5 automated checks (triggered manually or on a schedule):

1. Jobs overdue (past deadline and not completed)
2. Resources below reorder threshold (low stock)
3. Purchases with no resources linked
4. Jobs completed but no payment recorded
5. Budget overrun (amount paid exceeds quoted price)

Checks can be triggered from the Alerts page or run automatically via APScheduler.

---

## AI Reports

Reports are generated by sending a structured data prompt to OpenAI's `gpt-4o-mini` model. The response is stored as a `Report` record and can be viewed on the Reports page. Requires a valid `OPENAI_API_KEY` in `.env`.

---

## Static Files

In production, run:

```bash
python manage.py collectstatic
```

And configure your web server (nginx/gunicorn) to serve `/static/`.

---

## Database (Production)

The project includes `mysqlclient`. To switch to MySQL, update `settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'khael_db',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```
