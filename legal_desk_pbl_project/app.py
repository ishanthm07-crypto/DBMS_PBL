"""Legal Desk web app (Flask + MySQL).  Run:  python app.py  ->  http://localhost:5000"""
import datetime, decimal
import mysql.connector
from flask import Flask, jsonify, request, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
import config

app = Flask(__name__, static_folder="static")
app.secret_key = config.SECRET_KEY
app.config.update(SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_HTTPONLY=True)

# api name -> (sql table, primary key, editable columns)
T = {
 "clients":   ("client", "client_id", ["full_name", "phone", "email", "address"]),
 "lawyers":   ("lawyer", "lawyer_id", ["full_name", "specialization", "bar_no", "phone"]),
 "courts":    ("court", "court_id", ["name", "city", "type"]),
 "cases":     ("legal_case", "case_id", ["title", "case_type", "status", "filed_on", "client_id", "court_id"]),
 "hearings":  ("hearing", "hearing_id", ["case_id", "hearing_date", "purpose", "outcome"]),
 "documents": ("document", "document_id", ["case_id", "title", "doc_type", "added_on"]),
 "billing":   ("billing", "bill_id", ["case_id", "description", "amount", "status"]),
 "users":     ("app_user", "user_id", ["username", "display_name", "role", "lawyer_id", "client_id"]),
}
BASE = ["clients", "lawyers", "courts", "cases", "hearings", "documents", "billing"]
PERM = {
 "admin":  {**{t: "rw" for t in T}, "reports": "r", "log": "r"},
 "clerk":  {"clients": "rw", "lawyers": "r", "courts": "rw", "cases": "rw", "hearings": "rw",
            "documents": "rw", "billing": "rw", "reports": "r"},
 "lawyer": {"clients": "r", "lawyers": "r", "courts": "r", "cases": "r", "hearings": "rw",
            "documents": "rw", "billing": "r"},
 "client": {t: "r" for t in BASE},
}

def db():
    return mysql.connector.connect(host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASS, database=config.DB_NAME)

def clean(v):
    if isinstance(v, datetime.datetime): return v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, datetime.date): return v.isoformat()
    if isinstance(v, decimal.Decimal): return float(v)
    return v

def rows_of(cur, sql, args=()):
    cur.execute(sql, args)
    return [{k: clean(v) for k, v in r.items()} for r in cur.fetchall()]

def friendly(e):
    return {1451: "This record is still used by other records. Remove or reassign those first.",
            1062: "That value already exists (duplicate username, email or bar number).",
            1452: "The selected client, court, case or lawyer does not exist.",
            3819: "A value is outside the allowed range (for example a negative amount).",
            4025: "A value is outside the allowed range (for example a negative amount)."}.get(e.errno, e.msg)

@app.errorhandler(mysql.connector.Error)
def dberr(e):
    return jsonify(error=friendly(e)), 400

def cur_user():
    uid = session.get("uid")
    if not uid: return None
    c = db(); cur = c.cursor(dictionary=True)
    cur.execute("SELECT user_id, username, display_name, role, lawyer_id, client_id FROM app_user WHERE user_id=%s", (uid,))
    u = cur.fetchone(); c.close()
    return u

def scope(u, t):
    """Row filter so lawyers and clients only see their own data."""
    r = u["role"]
    if r in ("admin", "clerk"): return "", []
    if r == "lawyer":
        cs, p = "SELECT case_id FROM case_lawyer WHERE lawyer_id=%s", [u["lawyer_id"]]
        if t in ("cases", "hearings", "documents", "billing"): return f"WHERE case_id IN ({cs})", p
        if t == "clients": return f"WHERE client_id IN (SELECT client_id FROM legal_case WHERE case_id IN ({cs}))", p
        return "", []
    cs, p = "SELECT case_id FROM legal_case WHERE client_id=%s", [u["client_id"]]
    if t in ("cases", "hearings", "documents", "billing"): return f"WHERE case_id IN ({cs})", p
    if t == "clients": return "WHERE client_id=%s", p
    if t == "lawyers": return f"WHERE lawyer_id IN (SELECT lawyer_id FROM case_lawyer WHERE case_id IN ({cs}))", p
    return "", []

def case_allowed(cur, u, case_id):
    w, p = scope(u, "cases")
    if not w: return True
    cur.execute(f"SELECT 1 FROM legal_case {w} AND case_id=%s", p + [case_id])
    return cur.fetchone() is not None

def log(cur, uid, action, table=None, rid=None, details=None):
    cur.execute("INSERT INTO activity_log (user_id,action,table_name,record_id,details) VALUES (%s,%s,%s,%s,%s)",
                (uid, action, table, rid, details))

def need(t, mode):
    u = cur_user()
    if not u: return None, (jsonify(error="Please sign in."), 401)
    p = PERM[u["role"]].get(t, "")
    if not p or (mode == "w" and p != "rw"):
        return None, (jsonify(error="You do not have permission to do this."), 403)
    return u, None

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.post("/api/login")
def login():
    b = request.get_json() or {}
    c = db(); cur = c.cursor(dictionary=True)
    cur.execute("SELECT * FROM app_user WHERE username=%s", (b.get("username", "").strip(),))
    u = cur.fetchone()
    if not u or not check_password_hash(u["password_hash"], b.get("password", "")):
        c.close(); return jsonify(error="Wrong username or password."), 401
    session["uid"] = u["user_id"]
    log(cur, u["user_id"], "LOGIN"); c.commit(); c.close()
    return me()

@app.post("/api/logout")
def logout():
    u = cur_user()
    if u:
        c = db(); cur = c.cursor(); log(cur, u["user_id"], "LOGOUT"); c.commit(); c.close()
    session.clear()
    return jsonify(ok=True)

@app.get("/api/me")
def me():
    u = cur_user()
    if not u: return jsonify(error="Not signed in."), 401
    return jsonify(user={k: u[k] for k in ("username", "display_name", "role")}, perms=PERM[u["role"]])

@app.get("/api/<t>")
def listing(t):
    if t not in T: return jsonify(error="Not found"), 404
    u, err = need(t, "r")
    if err: return err
    table, pk, cols = T[t]
    w, p = scope(u, t)
    c = db(); cur = c.cursor(dictionary=True)
    rows = rows_of(cur, f"SELECT {pk},{','.join(cols)} FROM {table} {w} ORDER BY {pk}", p)
    if t == "cases":
        cur.execute("SELECT case_id, lawyer_id FROM case_lawyer")
        links = cur.fetchall()
        for r in rows: r["lawyers"] = [l["lawyer_id"] for l in links if l["case_id"] == r["case_id"]]
    c.close()
    return jsonify(rows)

def save(t, id=None):
    if t not in T: return jsonify(error="Not found"), 404
    u, err = need(t, "w")
    if err: return err
    table, pk, cols = T[t]
    cols = list(cols)
    body = request.get_json() or {}
    vals = [(body.get(k) if body.get(k) not in ("", None) else None) for k in cols]
    c = db(); cur = c.cursor(dictionary=True)
    try:
        if u["role"] == "lawyer" and "case_id" in cols:
            ok = case_allowed(cur, u, body.get("case_id"))
            if ok and id:
                cur.execute(f"SELECT case_id FROM {table} WHERE {pk}=%s", (id,))
                old = cur.fetchone()
                ok = bool(old) and case_allowed(cur, u, old["case_id"])
            if not ok: raise ValueError("You can only change records for your own cases.")
        if t == "users":
            role = body.get("role")
            if role == "lawyer" and not body.get("lawyer_id"): raise ValueError("Choose the lawyer this account belongs to.")
            if role == "client" and not body.get("client_id"): raise ValueError("Choose the client this account belongs to.")
            if role in ("admin", "clerk"): vals[cols.index("lawyer_id")] = vals[cols.index("client_id")] = None
            if role == "lawyer": vals[cols.index("client_id")] = None
            if role == "client": vals[cols.index("lawyer_id")] = None
            pw = body.get("password")
            if id is None and not pw: raise ValueError("Set a password for the new user.")
            if pw:
                cols.append("password_hash"); vals.append(generate_password_hash(pw, method="pbkdf2:sha256"))
        if id is None:
            cur.execute(f"INSERT INTO {table} ({','.join(cols)}) VALUES ({','.join(['%s'] * len(cols))})", vals)
            id, action = cur.lastrowid, "CREATE"
        else:
            cur.execute(f"UPDATE {table} SET {','.join(k + '=%s' for k in cols)} WHERE {pk}=%s", vals + [id])
            action = "UPDATE"
        if t == "cases":
            cur.execute("DELETE FROM case_lawyer WHERE case_id=%s", (id,))
            for lid in body.get("lawyers", []): cur.execute("INSERT INTO case_lawyer VALUES (%s,%s)", (id, lid))
        log(cur, u["user_id"], action, table, id, str(body.get("title") or body.get("full_name") or body.get("name") or body.get("description") or body.get("username") or "")[:100])
        c.commit()
    except ValueError as e:
        c.rollback(); return jsonify(error=str(e)), 400
    except mysql.connector.Error:
        c.rollback(); raise
    finally:
        c.close()
    return jsonify(ok=True, id=id)

@app.post("/api/<t>")
def create(t): return save(t)

@app.put("/api/<t>/<int:id>")
def update(t, id): return save(t, id)

@app.delete("/api/<t>/<int:id>")
def delete(t, id):
    if t not in T: return jsonify(error="Not found"), 404
    u, err = need(t, "w")
    if err: return err
    table, pk, cols = T[t]
    if t == "users" and id == u["user_id"]: return jsonify(error="You cannot delete your own account."), 400
    c = db(); cur = c.cursor(dictionary=True)
    try:
        if u["role"] == "lawyer" and "case_id" in cols:
            cur.execute(f"SELECT case_id FROM {table} WHERE {pk}=%s", (id,))
            old = cur.fetchone()
            if not old or not case_allowed(cur, u, old["case_id"]):
                return jsonify(error="You can only change records for your own cases."), 403
        cur.execute(f"DELETE FROM {table} WHERE {pk}=%s", (id,))
        log(cur, u["user_id"], "DELETE", table, id)
        c.commit()
    except mysql.connector.Error:
        c.rollback(); raise
    finally:
        c.close()
    return jsonify(ok=True)

@app.get("/api/reports")
def reports():
    u, err = need("reports", "r")
    if err: return err
    c = db(); cur = c.cursor(dictionary=True)
    out = {
     "pending": rows_of(cur, "SELECT full_name, pending_amount AS amount FROM v_pending_fees ORDER BY pending_amount DESC"),
     "workload": rows_of(cur, "SELECT l.full_name, COUNT(cla.case_id) AS total FROM lawyer l LEFT JOIN case_lawyer cla ON cla.lawyer_id=l.lawyer_id GROUP BY l.lawyer_id, l.full_name ORDER BY total DESC"),
     "status": rows_of(cur, "SELECT status, COUNT(*) AS total FROM legal_case GROUP BY status"),
     "billing": rows_of(cur, "SELECT status, SUM(amount) AS total FROM billing GROUP BY status"),
    }
    c.close()
    return jsonify(out)

@app.get("/api/log")
def activity():
    u, err = need("log", "r")
    if err: return err
    c = db(); cur = c.cursor(dictionary=True)
    rows = rows_of(cur, "SELECT a.log_id, a.created_at, COALESCE(u.username,'system') AS username, a.action, a.table_name, a.record_id, a.details FROM activity_log a LEFT JOIN app_user u USING (user_id) ORDER BY a.log_id DESC LIMIT 200")
    c.close()
    return jsonify(rows)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
