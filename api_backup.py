from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

DB = "loan_bot.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "service": "Loan Request Assistant API"
    })


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "database": "loan_bot.db"
    })


@app.route("/api/stats")
def stats():
    conn = get_db()
    cur = conn.cursor()

    users = cur.execute(
        "SELECT COUNT(*) FROM users"
    ).fetchone()[0]

    loans = cur.execute(
        "SELECT COUNT(*) FROM loan_requests"
    ).fetchone()[0]

    pending = cur.execute(
        "SELECT COUNT(*) FROM loan_requests WHERE status = 'pending'"
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "users": users,
        "loan_requests": loans,
        "pending_loans": pending
    })


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
