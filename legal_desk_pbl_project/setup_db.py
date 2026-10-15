"""Creates the legal_desk database in MySQL.   Run:  python setup_db.py"""
import re, sys
import mysql.connector
import config

try:
    c = mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS)
except mysql.connector.Error as e:
    sys.exit(f"Cannot connect to MySQL: {e.msg}\nCheck DB_USER / DB_PASS in config.py and that MySQL is running.")
cur = c.cursor()
for f in ("sql/01_schema.sql", "sql/02_seed.sql"):
    text = re.sub(r"^\s*--.*$", "", open(f, encoding="utf-8").read(), flags=re.M)
    for stmt in text.split(";"):
        if stmt.strip():
            try:
                cur.execute(stmt)
            except mysql.connector.Error as e:
                if "TRIGGER" in stmt.upper():
                    print("Warning: trigger not created (", e.msg, ") - the app still works.")
                else:
                    sys.exit(f"Error in {f}: {e.msg}")
    c.commit()
    print("Ran", f)
print("Done. Database 'legal_desk' is ready.")
