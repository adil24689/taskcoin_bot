# db.py

import sqlite3
from config import DB_NAME

def get_conn():
    return sqlite3.connect(DB_NAME)

def init_db():
    with get_conn() as conn, open("schema.sql") as f:
        conn.executescript(f.read())

def create_user(telegram_id, name):
    with get_conn() as conn:
        conn.execute("""
            INSERT OR IGNORE INTO users (telegram_id, name)
            VALUES (?, ?)""", (telegram_id, name))
        conn.commit()

def get_user(telegram_id):
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,))
        return cur.fetchone()

def update_balance(telegram_id, amount):
    with get_conn() as conn:
        conn.execute("UPDATE users SET balance = balance + ? WHERE telegram_id=?", (amount, telegram_id))
        conn.commit()

def add_earning(telegram_id, amount):
    with get_conn() as conn:
        conn.execute("UPDATE users SET earnings = earnings + ? WHERE telegram_id=?", (amount, telegram_id))
        conn.commit()

def post_task(title, description, proof_required, slots, poster_id):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO tasks (title, description, proof_required, total_slots, posted_by)
            VALUES (?, ?, ?, ?, ?)""", (title, description, proof_required, slots, poster_id))
        conn.commit()

def get_active_tasks():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM tasks WHERE active=1").fetchall()

def submit_task(user_id, task_id, proof):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO submissions (user_id, task_id, proof)
            VALUES (?, ?, ?)""", (user_id, task_id, proof))
        conn.commit()

def get_pending_submissions():
    with get_conn() as conn:
        return conn.execute("""
            SELECT submissions.id, users.name, tasks.title, submissions.proof
            FROM submissions
            JOIN users ON submissions.user_id = users.telegram_id
            JOIN tasks ON submissions.task_id = tasks.id
            WHERE submissions.status = 'pending'
        """).fetchall()

def set_submission_status(submission_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE submissions SET status=? WHERE id=?", (status, submission_id))
        conn.commit()

def count_users():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

def count_tasks():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]

def count_pending_submissions():
    with get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM submissions WHERE status='pending'").fetchone()[0]

def get_user_id_from_submission(submission_id):
    with get_conn() as conn:
        cur = conn.execute("SELECT user_id FROM submissions WHERE id=?", (submission_id,))
        result = cur.fetchone()
        return result[0] if result else None

def add_recharge(user_id, amount, method, trx_id):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO recharges (user_id, amount, method, trx_id)
            VALUES (?, ?, ?, ?)
        """, (user_id, amount, method, trx_id))
        conn.commit()


    


def get_pending_recharges():
    query = """
    SELECT r.id, u.name, r.amount, r.method, r.trx_id
    FROM recharges r
    JOIN users u ON r.user_id = u.telegram_id
    WHERE r.status = 'pending'
    """
    with get_conn() as conn:
        cursor = conn.execute(query)
        return cursor.fetchall()
