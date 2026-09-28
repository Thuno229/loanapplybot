from flask import Flask, jsonify, request
import sqlite3
import os

app = Flask(__name__)

DB = "loan_bot.db"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def admin_required():
    key = request.headers.get("X-API-Key")
    expected = os.environ.get("ADMIN_API_KEY")

    if not expected or key != expected:
        return False

    return True


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
        "database": DB
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


@app.route("/api/admin/stats")
def admin_stats():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

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

    kyc_pending = cur.execute(
        "SELECT COUNT(*) FROM users WHERE kyc_status = 'pending'"
    ).fetchone()[0]

    conn.close()

    return jsonify({
        "users": users,
        "loan_requests": loans,
        "pending_loans": pending,
        "pending_kyc": kyc_pending
    })


@app.route("/api/admin/users")
def admin_users():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            id,
            telegram_id,
            username,
            language,
            first_name,
            last_name,
            country,
            email,
            profession,
            kyc_status,
            created_at
        FROM users
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify({
        "users": [dict(row) for row in rows]
    })


@app.route("/api/admin/loans")
def admin_loans():
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    rows = cur.execute("""
        SELECT
            id,
            telegram_id,
            amount,
            guarantee,
            network,
            repayment_period,
            status,
            guarantee_status,
            txid,
            wallet_address,
            created_at
        FROM loan_requests
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return jsonify({
        "loans": [dict(row) for row in rows]
    })


@app.route("/api/admin/loans/<int:loan_id>")
def admin_loan(loan_id):
    if not admin_required():
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db()
    cur = conn.cursor()

    row = cur.execute("""
        SELECT
            id,
            telegram_id,
            amount,
            guarantee,
            network,
            repayment_period,
            status,
            guarantee_status,
            txid,
            wallet_address,
            created_at
        FROM loan_requests
        WHERE id = ?
    """, (loan_id,)).fetchone()

    conn.close()

    if row is None:
        return jsonify({
            "error": "Loan request not found"
        }), 404

    return jsonify(dict(row))


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
