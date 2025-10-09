
<p align="center">
	<img src="https://img.shields.io/github/actions/workflow/status/JakeyMarsh1/ledgerly/django.yml?branch=main&label=build" alt="Build Status" />
	<img src="https://img.shields.io/github/license/JakeyMarsh1/ledgerly" alt="License" />
	<img src="https://img.shields.io/badge/python-3.11%2B-blue.svg" alt="Python Version" />
	<img src="https://img.shields.io/badge/django-4.2-green.svg" alt="Django Version" />
	<a href="https://github.com/users/JakeyMarsh1/projects/9/views/1"><img src="https://img.shields.io/badge/project%20board-User%20Stories-blue" alt="Project Board" /></a>
</p>

# Ledgerly

A simple Django + Postgres web app to record incomes and outgoings, showing a monthly “available to spend” total. Built for clarity, speed, and a focused MVP, with room for future insights like average spend.

---

## Table of Contents
- [Features](#features)
- [Accessibility](#accessibility)
- [Screenshots](#Screenshots)
- [Testing](#Testing)
- [Overview](#overview)
- [Problem](#problem)
- [Solution](#solution)
- [Scope](#scope)
- [MVP](#mvp)
- [Ideation](#ideation)
- [Information Architecture](#information-architecture)
- [User Stories](#user-stories)
- [Tech Stack](#tech-stack)
- [Setup](#setup)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features
- Dashboard: shows current-month “available to spend” and recent transactions.

- Transactions: add, edit, and delete incomes and outgoings.

- Categories: global list; required for outgoings, optional for incomes.

- Authentication: sign up, log in, log out; per-user data isolation.

- Data integrity: store money in integer pence; format in views/templates.

## Accessibility
- Semantic structure: use headings, labels, and descriptive button text for assistive tech.

- Keyboard navigation: all interactive elements are reachable via Tab with a visible focus outline.

- Color and contrast: palette chosen to target WCAG AA contrast for text and controls.

- Forms: inputs have associated labels; errors and status messages are announced near the form heading.

- Touch targets: primary actions sized for comfortable tapping on mobile (approx. 44px minimum).

- Motion and feedback: no auto-playing or flashing content; feedback uses simple text alerts.

## Screenshots

![Dashboard](assets/readme_images/dashboard Outgoing form)
![Add Outgoing](assets/readme_images/add_out list)
![Transactions](assets/readme_images/transactions dashboard)
![Dashboard Mobile](assets/readme_images/dashboard the folder assets/readme_images/)

## Testing
Area            |  Test                 |  Steps                             |  Expected                                  |  Result
----------------+-----------------------+------------------------------------+--------------------------------------------+--------
Auth            |  Sign up              |  Register a new account            |  User created and logged in                |  ✅  
Auth            |  Log in/out           |  Log in, then log out              |  Session starts/ends correctly             |  ✅   
Transactions    |  Add income           |  Create income with valid data     |  Appears in list; total updates            |  ✅   
Transactions    |  Add outgoing         |  Create outgoing with category     |  Appears in list; total updates            |  ✅  
Transactions    |  Edit                 |  Edit an existing transaction      |  Changes persist; total recalcs            |  ✅  
Transactions    |  Delete               |  Delete an existing transaction    |  Row removed; total recalcs                |  ✅   
Categories      |  Validation           |  Submit outgoing without category  |  Form blocks submit with clear error       |  ✅   
Dashboard       |  Total recalculation  |  Create/edit/delete transactions   |  “Available to spend” updates immediately  |  ✅   
Security        |  Data isolation       |  Log in as second user             |  Only that user’s data visible             |  ✅   
Responsiveness  |  Mobile view          |  Use a small viewport              |  Layout remains readable and usable        |  ✅   

Validator results:

HTML

CSS

Python

JS

Known bugs / fixes

## Overview
Ledgerly helps users understand what they can safely spend this week by combining all recorded incomes and outgoings into one clear number. The app focuses on minimal screens, fast entry, and accurate calculations.

## Problem
Budget tools can feel heavy or too granular. Many people just want one trusted monthly number without spreadsheets or manual sums.

## Solution
- Quick forms for incomes and outgoings
- One weekly “available to spend” total on the dashboard
- Simple categories to keep organization lightweight

## Scope
**In scope (MVP):**
- Transaction CRUD (income and outgoing)
- Weekly available total on a dashboard
- Basic auth (sign up/in/out)
- Simple categories for outgoings
- Django Admin for support tasks

**Out of scope (for now):**
- CSV import/export
- Attachments/receipts
- Blog
- Average spending insights and projections

---

## MVP
The MVP delivers:
- Dashboard with “available to spend” for the current month
- Add/edit/delete incomes and outgoings
- Recent transactions list
- Secure per-user data isolation

**Success criteria:**
- Entering a transaction updates the monthly total immediately
- Core pages are simple to navigate and responsive

## Ideation
**Principles:**
- Keep actions to two clicks where possible
- Store money in integer pence; format at the view layer
- Start server-rendered; add charts/CSV later
- Write stories in “As a role, I can capability, so that benefit” format

**Why weekly?**
A single weekly number reduces cognitive load and supports everyday decisions.

## Information Architecture
- **Dashboard:** weekly total and a small summary
- **Transactions:** list, add income, add outgoing, edit/delete
- **Categories:** simple admin-managed list; dropdown on outgoing form
- **Auth:** sign up, log in, log out


---

## Entity Relationship Diagram (ERD)
### Visual ERD

![ERD Diagram](assets/readme_images/erd.png)

This diagram represents the relationships between the `User`, `Transaction`, and `Category` entities. Each `User` can have multiple `Transactions`, while each `Transaction` optionally belongs to a `Category`. Categories are shared globally and not user-specific.

### User
| Attribute      | Type         | Notes                                      |
|---------------|--------------|--------------------------------------------|
| id            | PK           | Unique identifier for the user.            |
| email         | String (unique) | Used for login; unique per user.           |
| password_hash | String       | Stored securely by auth system.            |
| created_at    | DateTime     | Record creation timestamp.                 |
| updated_at    | DateTime     | Last update timestamp.                     |

**Relationships:**
- User to Transaction: 1 to many (One User has many Transactions; each Transaction belongs to exactly one User)
- User to Category: none (Categories are global/shared; not owned by a specific User in the MVP)

### Category
| Attribute   | Type   | Notes                                         |
|-------------|--------|-----------------------------------------------|
| id          | PK     | Unique identifier for the category.           |
| name        | String | Display name (e.g., Groceries, Rent).         |
| is_active   | Boolean| Controls availability in forms.               |
| created_at  | DateTime | Record creation timestamp.                   |
| updated_at  | DateTime | Last update timestamp.                       |

**Relationships:**
- Category to Transaction: 1 to many (One Category is used by many Transactions)
- Category on INCOME: optional (For INCOME rows, category is null)
- Category on OUTGO: required (For OUTGO rows, category is required)

### Transaction
| Attribute        | Type                | Notes                                              |
|------------------|---------------------|----------------------------------------------------|
| id               | PK                  | Unique identifier for the transaction.              |
| user_id          | FK -> User(id)      | Owner; required.                                   |
| category_id      | FK -> Category(id), nullable | Required for OUTGO; null for INCOME.      |
| type             | Enum {INCOME, OUTGO}| Controls sign/behavior.                            |
| amount_in_cents  | Integer             | Store money in minor units for precision.           |
| occurred_on      | Date                | The transaction date (used for weekly grouping).    |
| note             | Text (optional)     | Freeform context.                                  |
| created_at       | DateTime            | Record creation timestamp.                         |
| updated_at       | DateTime            | Last update timestamp.                             |

**Relationships:**
- Transaction to User: many to 1 (Each Transaction belongs to exactly one User)
- Transaction to Category: many to 1 (optional) (Optional for INCOME; required for OUTGO)

---
## User Stories
User Stories (delivered)
As a user, I can view my “available to spend” total for the current week so that I immediately know what I can safely spend without overshooting my budget.

Acceptance:

Computes weekly total as sum(incomes) − sum(outgoings) for the current week.

Uses only the signed-in user’s data.

Week defaults to Monday–Sunday; shows 0.00 if no data.

As a user, I can record an income with amount and date (plus optional source and note) so that my inflows are accurately included in weekly availability.

Acceptance:

Amount > 0 and date required; saved as INCOME.

On success, redirect to a relevant page and show a success message.

As a user, I can record an expense with amount, date, and category (plus optional note) so that my outflows are properly tracked and categorized.

Acceptance:

Amount > 0, date, and category required; saved as OUTGO.

Category must be chosen from the active list.

As a user, I can edit or delete my own transactions so that mistakes don’t distort my weekly availability or reports.

Acceptance:

Can edit/delete only transactions owned by the signed-in user.

Delete requires a simple confirmation; totals recalculate.

As a user, I can see a paginated list of my recent transactions ordered by newest first so that I can quickly confirm entries and spot anomalies.

Acceptance:

Shows date, type, amount, category/source, and a short note snippet.

Ordered newest first; 25 per page; only the signed-in user’s data.

As a user, I can create an account, sign in, and sign out so that my financial data remains private and secure.

Acceptance:

Register with unique email and password.

Login starts a session; logout clears session.

Success/error messages are shown appropriately.

As an admin, I can browse, search, and edit users, categories, and transactions so that I can support users and keep data consistent.

Acceptance:

Models visible in Django Admin with list_display, filters, and basic search.

As a user, I can assign an active category to each outgoing so that my spending can be grouped for quick insights.

Acceptance:

Only active categories are selectable on the form.

User Stories (planned)
As a user, I can filter transactions by week and category so that I can answer targeted spending questions.

Acceptance:

Filters via URL query params; results update list and totals.

As a user, I can set my preferred weekly start day so that weekly availability matches how I plan my budget.

Acceptance:

Preference (0–6) changes week calculation and displays accordingly.

As an admin, I can create default categories and archive categories so that users see a clean, relevant set.

Acceptance:

Archived categories remain linked for history but don’t appear in forms.

As an admin, I can view weekly counts of created, edited, and deleted transactions so that I can detect usability issues and training needs.

Acceptance:

Simple counts per week on a staff-only page.

As a user, I can attach receipts or files to a transaction so that I have evidence and context.

Acceptance:

Upload small images/PDFs; show a thumbnail or download link.

As a user, I can import transactions from a CSV file so that I can batch-load my financial data efficiently.

Acceptance:

Upload CSV, preview parsed rows, confirm import.

As a user, I can export my (filtered) transactions to CSV so that I can back up or analyze externally.

Acceptance:

Download CSV for current filters with headers.

As an admin, I can flag accounts as read-only demo users so that stakeholders can explore safely without changing data.

Acceptance:

Demo users cannot create/edit/delete; a friendly banner is shown.

All current user stories are tracked on the project board:  
[User Stories & Project Board](https://github.com/users/JakeyMarsh1/projects/9/views/1)

## Epics
Secure access and data isolation

Sign up, log in, log out; session-based access ensuring each user only sees their own data.

Weekly available-to-spend dashboard

Single weekly total, recalculated immediately after transaction changes.

Transaction lifecycle

Add income, add outgoing (with active category), edit/delete transactions, recent list with pagination.

Category administration

Global categories with visibility controls; archived categories remain linked but hidden from forms.

Focused insights

Filter by week and category; lightweight operational reporting (planned).

Admin management

Browse/search/edit users, categories, transactions via Django Admin.

Data import/export and attachments

CSV import/export and receipt/file attachments (planned).

Safe demo exploration

Read-only demo users for stakeholder walkthroughs (planned).

## Tech Stack
- **Backend:** Django (Python), Django Admin
- **Database:** PostgreSQL
- **Templating:** Django templates; minimal JS (Chart.js later)
- **Auth:** Django auth (email login optional)

## Setup
**Requirements:** Python 3.11+, PostgreSQL 14+

# Deployment

## Heroku Deployment (via GitHub)

1. **Push to GitHub**
   - Make sure all changes are committed and pushed to your main branch on GitHub.

2. **Connect Heroku to GitHub**
   - In your Heroku dashboard, go to your app’s “Deploy” tab.
   - Under “Deployment method,” select **GitHub** and connect your repository.

3. **Set Config Vars**
   - In the “Settings” tab, add your environment variables (e.g., `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DATABASE_URL`, etc.) under “Config Vars.”

4. **Automatic Deploys**
   - Enable “Automatic Deploys” from the main branch if you want Heroku to redeploy on every push.

5. **Manual Deploy**
   - You can also trigger a manual deploy by clicking “Deploy Branch” in the Heroku dashboard.

6. **Static Files**
   - Heroku will run `python manage.py collectstatic` automatically during the build process.
   - Make sure your `STATIC_ROOT` and `STATICFILES_STORAGE` are set correctly in `settings.py`.

7. **Database Migrations**
   - After deployment, run migrations:
     ```bash
     heroku run python manage.py migrate
     ```

8. **Create Superuser (Optional)**
   - To access the Django admin panel:
     ```bash
     heroku run python manage.py createsuperuser
     ```

9. **Check Your App**
   - Visit your Heroku app’s URL to confirm everything is working.

---

**Note:**  
- Make sure your `requirements.txt` and `Procfile` are up to date.
- If you use custom domains, configure them in the Heroku dashboard and set up DNS as needed.

---

**Example Heroku App:**  
[https://your-app-name.herokuapp.com/](https://your-app-name.herokuapp.com/)
.

**Steps:**
1. Clone the repo and create a virtualenv
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables (`DATABASE_URL`, `SECRET_KEY`, `DEBUG`)
4. Run migrations: `python manage.py migrate`
5. Create a superuser: `python manage.py createsuperuser`
6. Start the server: `python manage.py runserver`

## Known Issues

Validation messages may vary by browser defaults; ensure forms surface clear errors near the field and at the top of the form.

Screenshot assets are placeholders until images are added under assets/readme_images/.

No CSV import/export yet; large historical imports require manual entry for now.

Category model is global; users cannot create private categories in the UI.

## Assumptions and Limitations

Money stored as integer pence and formatted at the view/template layer to avoid floating‑point errors.

Categories are shared across all users; OUTGO requires a category, INCOME does not.

Weekly “available to spend” derives from current month context and recent transactions; advanced analytics deferred.

Authentication relies on Django’s built‑in auth; no social login in MVP.

## Roadmap
- **MVP:** dashboard, transaction CRUD, auth, admin
- **Post‑MVP:** CSV import/export, attachments, average-spend insights, optional blog

## Contributing
- Open an issue or small PR
- Use feature branches and concise commit messages
- Add a simple test for each change

## License
Specify a license (e.g., MIT) in LICENSE

---

# Suggested Django Project Structure for Ledgerly

```
ledgerly/
├── ledgerly/                  # Project config (settings, urls, wsgi)
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── expenses/                  # Your main app (can be named 'expenses', 'core', etc.)
│   ├── __init__.py
│   ├── admin.py               # Register models for Django admin
│   ├── apps.py
│   ├── models.py              # User, Transaction, Category models
│   ├── views.py               # Views for dashboard, CRUD, etc.
│   ├── urls.py                # App-specific URLs
│   ├── forms.py               # Django forms for input
│   ├── tests.py               # Unit tests
│   ├── migrations/
│   │   └── __init__.py
│   └── templates/
│       └── expenses/
│           ├── dashboard.html
│           ├── transaction_list.html
│           └── ...           # Other templates
├── manage.py
├── requirements.txt
└── README.md
```

- Place your custom User model (if needed) and Transaction/Category models in `expenses/models.py`.
- Use `expenses/views.py` for dashboard and CRUD logic.
- Templates go in `expenses/templates/expenses/`.
- Register your app in `INSTALLED_APPS` in `ledgerly/settings.py`.

---

## Wireframe

![Wireframe](assets/readme_images/Screenshot%202025-09-25%20114035.png)

This wireframe shows the planned layout and user flow for the Ledgerly dashboard and transaction screens.