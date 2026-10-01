import os

DATA_DIR = os.getenv("BOT_DATA_DIR", ".")
DB_PATH = os.path.join(DATA_DIR, "loan_bot.db")
PERSISTENCE_PATH = os.path.join(DATA_DIR, "loan_bot_persistence.pkl")
