# Legal Desk - Legal Case and Client Management System (DBMS Project 58)
M Srihari (25WU0103025)  |  Flask web app + MySQL database

## Files
- `sql/01_schema.sql`  database `legal_desk`: 10 tables, 2 views, 1 trigger
- `sql/02_seed.sql`    sample data and login accounts
- `sql/03_queries.sql` queries to show in the MySQL terminal
- `setup_db.py`        creates the database (works on Windows, no `mysql <` needed)
- `app.py`, `static/index.html`  the web app
- `config.py`          MySQL login settings

## Run (Windows / Mac / Linux)
1. Install and start MySQL. Open `config.py` and put your MySQL password in `DB_PASS`.
2. Open a terminal in this folder, then:
       pip install -r requirements.txt
       python setup_db.py
       python app.py
3. Open http://localhost:5000 and sign in.

## Logins (password in brackets)
| Role | Username | Can do |
|------|----------|--------|
| Admin | admin (admin123) | everything, users, activity log, reports |
| Clerk | clerk (clerk123) | clients, courts, cases, hearings, documents, billing, reports |
| Lawyer | meera, rohan (lawyer123) | sees only own cases; adds hearings and documents for them |
| Client | anita, vikram (client123) | read-only view of own cases, hearings, documents, bills |

## Show the database in the MySQL terminal
    mysql -u root -p
    USE legal_desk;
    SHOW TABLES;
    DESCRIBE legal_case;
    SELECT user_id, username, role FROM app_user;
    SELECT * FROM v_case_summary;
    SELECT * FROM activity_log ORDER BY log_id DESC LIMIT 10;
Or run everything in `sql/03_queries.sql`:  `mysql -u root -p < sql/03_queries.sql`

Demo flow: add a case in the web app, then run `SELECT * FROM legal_case;` and the activity_log query
in the terminal. Mark a bill paid in the app and see the `PAYMENT_RECEIVED` row the trigger writes.
`CASE` is reserved in MySQL, so that table is named `legal_case`.
