import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import sqlite3
from database import get_db_connection
from config import ADMIN_IDS

logger = logging.getLogger(__name__)

CHANNEL_USERNAME = "@GLOBALUSDTFINANCE1"
CHANNEL_ID = None # mets -100xxxx si tu l'as, sinon on utilise le username

def ensure_channel_schema():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS channel_config (
            id INTEGER PRIMARY KEY,
            channel_id TEXT,
            channel_username TEXT,
            enabled INTEGER DEFAULT 1
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS channel_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_request_id INTEGER,
            message_id INTEGER,
            channel_id TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        cur.execute("SELECT id FROM channel_config LIMIT 1")
        if not cur.fetchone():
            cur.execute("INSERT INTO channel_config (channel_id, channel_username, enabled) VALUES (?,?, 1)", (str(CHANNEL_ID or CHANNEL_USERNAME), CHANNEL_USERNAME))
        conn.commit()
        conn.close()
        logger.info("📢 Module Canal Telegram activé.")
    except Exception as e:
        logger.error(f"Canal schema error: {e}")

async def channel_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Si tu veux taper un message custom à publier
    text = update.message.text
    if context.user_data.get("channel_admin_mode") == "awaiting_custom":
        try:
            await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=f"📢 {text}")
            await update.message.reply_text(f"✅ Publié dans {CHANNEL_USERNAME}")
        except Exception as e:
            await update.message.reply_text(f"❌ Erreur publish: {e}")
        context.user_data["channel_admin_mode"] = None
        return
    # sinon on ignore

def get_channel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Publier", callback_data="admin_channel_publish")],
        [InlineKeyboardButton("📅 Programmer", callback_data="admin_channel_program")],
        [InlineKeyboardButton("📂 Publications", callback_data="admin_channel_list")],
        [InlineKeyboardButton("📊 Statistiques", callback_data="admin_channel_stats")],
        [InlineKeyboardButton("↩️ Panneau admin", callback_data="admin_panel")],
    ])

async def channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS:
        await query.answer("Non autorisé", show_alert=True)
        return

    if data == "admin_channel":
        ensure_channel_schema()
        txt = f"📢 GESTION DU CANAL\n\nCanal : {CHANNEL_USERNAME}\nChoisissez une action :"
        await query.edit_message_text(txt, reply_markup=get_channel_keyboard())
        return

    if data == "admin_channel_publish":
        context.user_data["channel_admin_mode"] = "awaiting_custom"
        await query.edit_message_text(
            f"Canal : {CHANNEL_USERNAME}\n\n✍️ Envoie maintenant le texte (ou photo + légende) que tu veux publier dans le canal.\n\n/cancel pour annuler.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="admin_channel")]])
        )
        return

    if data == "admin_channel_program":
        await query.edit_message_text(
            "📅 Programmation bientôt.\nPour l'instant utilise Publier.\n",
            reply_markup=get_channel_keyboard()
        )
        return

    if data == "admin_channel_list":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT loan_request_id, message_id, status, created_at FROM channel_posts ORDER BY id DESC LIMIT 10")
            rows = cur.fetchall()
            conn.close()
            if not rows:
                txt = "📂 Aucune publication encore."
            else:
                txt = "📂 Dernières publications :\n\n" + "\n".join([f"• Prêt #{r[0]} | msg {r[1]} | {r[2]} | {r[3]}" for r in rows])
            await query.edit_message_text(txt, reply_markup=get_channel_keyboard())
        except Exception as e:
            await query.edit_message_text(f"Erreur: {e}", reply_markup=get_channel_keyboard())
        return

    if data == "admin_channel_stats":
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM channel_posts")
            total = cur.fetchone()[0]
            conn.close()
            txt = f"📊 Statistiques Canal {CHANNEL_USERNAME}\n\n• Total posts : {total}\n• Fuseau Railway/serveur : UTC.\n• Statut : ✅ Actif"
            await query.edit_message_text(txt, reply_markup=get_channel_keyboard())
        except Exception as e:
            await query.edit_message_text(f"Erreur stats: {e}", reply_markup=get_channel_keyboard())
        return

async def publish_loan_request(bot, request_id: int):
    # Appelé auto quand une demande est créée - version simple
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, amount, status FROM loan_requests WHERE id=?", (request_id,))
        row = cur.fetchone()
        if not row:
            return
        text = f"💰 Nouvelle demande #{row[0]}\nMontant : {row[1]}\nStatut : {row[2]}"
        msg = await bot.send_message(chat_id=CHANNEL_USERNAME, text=text)
        cur.execute("INSERT INTO channel_posts (loan_request_id, message_id, channel_id, status) VALUES (?,?,?,?)",
                    (request_id, msg.message_id, CHANNEL_USERNAME, row[2]))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"publish_loan_request fail: {e}")

async def update_loan_post(bot, request_id: int, new_status: str):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT message_id FROM channel_posts WHERE loan_request_id=? ORDER BY id DESC LIMIT 1", (request_id,))
        r = cur.fetchone()
        if r:
            await bot.edit_message_text(chat_id=CHANNEL_USERNAME, message_id=r[0], text=f"💰 Demande #{request_id}\nNouveau statut : {new_status}")
        conn.close()
    except Exception as e:
        logger.error(f"update_loan_post fail: {e}")

async def restore_scheduled_posts(bot):
    logger.info("Canal: restore_scheduled_posts OK (vide)")

