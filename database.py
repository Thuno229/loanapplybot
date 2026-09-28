from storage import DB_PATH
import os
import sqlite3

DB_NAME = os.path.join(os.getenv("BOT_DATA_DIR", "."), "loan_bot.db")


def get_connection():
    return sqlite3.connect(DB_NAME)



def migrate_schema(conn):
    """Ajoute les colonnes manquantes sans supprimer les données existantes."""
    conn.execute("PRAGMA busy_timeout=30000")

    migrations = {
        "users": {
            "blocked": "INTEGER DEFAULT 0",
            "kyc_photo_file_id": "TEXT",
            "updated_at": "TIMESTAMP",
            "last_seen_at": "TIMESTAMP",
        },
        "loan_requests": {
            "updated_at": "TIMESTAMP",
            "rejection_reason": "TEXT",
        },
        "loans": {
            "approved_at": "TIMESTAMP",
            "completed_at": "TIMESTAMP",
            "last_payment_at": "TIMESTAMP",
        },
        "loan_installments": {
            "amount_paid": "REAL DEFAULT 0",
        },
    }

    for table, columns in migrations.items():
        existing = {
            row[1]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }

        for column, definition in columns.items():
            if column not in existing:
                conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
                )
                print(f"✅ Colonne ajoutée : {table}.{column}")

    conn.execute(
        "UPDATE loan_installments "
        "SET amount_paid = COALESCE(amount_paid, 0)"
    )


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            language TEXT,
            first_name TEXT,
            last_name TEXT,
            country TEXT,
            phone TEXT,
            email TEXT,
            profession TEXT,
            photo_file_id TEXT,
            trc20_address TEXT,
            bep20_address TEXT,
            kyc_status TEXT DEFAULT 'not_submitted',
            blocked INTEGER DEFAULT 0,
            balance REAL DEFAULT 0,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            guarantee REAL NOT NULL,
            network TEXT,
            repayment_period TEXT,
            status TEXT DEFAULT 'pending',
            guarantee_status TEXT DEFAULT 'not_paid',
            txid TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER UNIQUE NOT NULL,
            reward REAL DEFAULT 5,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_request_id INTEGER UNIQUE NOT NULL,
            telegram_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            interest_rate REAL NOT NULL DEFAULT 1.0,
            total_repayment REAL NOT NULL,
            monthly_payment REAL NOT NULL,
            duration_months INTEGER NOT NULL,
            status TEXT DEFAULT 'approved',
            disbursement_status TEXT DEFAULT 'awaiting',
            disbursement_network TEXT,
            disbursement_amount REAL,
            disbursement_txid TEXT,
            disbursement_date TIMESTAMP,
            amount_repaid REAL DEFAULT 0,
            installments_paid INTEGER DEFAULT 0,
            next_due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS loan_installments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL,
            installment_number INTEGER NOT NULL,
            due_date TEXT,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            paid_at TIMESTAMP,
            payment_txid TEXT,
            UNIQUE(loan_id, installment_number)
        )
    """)

    migrate_schema(conn)
    conn.commit()
    conn.close()


def ensure_enterprise_schema():
    conn = get_connection()
    try:
        conn.execute("PRAGMA busy_timeout=30000")
        conn.executescript("CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS repayment_records(id INTEGER PRIMARY KEY AUTOINCREMENT,loan_id INTEGER NOT NULL,telegram_id INTEGER NOT NULL,amount REAL NOT NULL,txid TEXT NOT NULL,recorded_by INTEGER NOT NULL,status TEXT DEFAULT 'confirmed',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP); CREATE TABLE IF NOT EXISTS support_tickets(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id INTEGER NOT NULL,subject TEXT,message TEXT NOT NULL,status TEXT DEFAULT 'open',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,closed_at TIMESTAMP);")
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
    print("✅ Base de données créée avec succès.")
