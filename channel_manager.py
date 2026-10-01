import logging
logger = logging.getLogger(__name__)

CHANNEL_USERNAME = "@GLOBALUSDTFINANCE1"
CHANNEL_ID = None

def ensure_channel_schema():
    try:
        from database import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS channel_config (id INTEGER PRIMARY KEY, channel_id TEXT, channel_username TEXT, enabled INTEGER DEFAULT 1)")
        cur.execute("CREATE TABLE IF NOT EXISTS channel_posts (id INTEGER PRIMARY KEY AUTOINCREMENT, loan_request_id INTEGER, message_id INTEGER, channel_id TEXT, status TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        cur.execute("SELECT id FROM channel_config LIMIT 1")
        if not cur.fetchone():
            cur.execute("INSERT INTO channel_config (channel_id, channel_username, enabled) VALUES (?,?,1)", (str(CHANNEL_ID or CHANNEL_USERNAME), CHANNEL_USERNAME))
        conn.commit()
        conn.close()
        logger.info("📢 Module Canal Telegram activé.")
    except Exception as e:
        logger.error(f"Canal schema skip: {e}")

# Fonctions vides qui ne plantent jamais au démarrage
async def publish_loan_request(bot, request_id: int):
    logger.info(f"[Canal] publish_loan_request {request_id} skipped (safe mode)")

async def update_loan_post(bot, request_id: int, new_status: str):
    pass

async def restore_scheduled_posts(bot=None):
    logger.info("Canal: restore OK")

async def channel_admin_message(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    text = update.message.text if update.message else ""
    mode = context.user_data.get("channel_admin_mode")
    if mode == "awaiting_custom":
        try:
            await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=f"📢 {text}")
            await update.message.reply_text(f"✅ Publié dans {CHANNEL_USERNAME}")
        except Exception as e:
            await update.message.reply_text(f"❌ Erreur: {e}\nVérifie que le bot est ADMIN dans {CHANNEL_USERNAME}")
        context.user_data["channel_admin_mode"] = None
    else:
        await update.message.reply_text("Utilise /admin > Gestion du canal")

def get_channel_keyboard():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Publier", callback_data="admin_channel_publish")],
        [InlineKeyboardButton("📅 Programmer", callback_data="admin_channel_program")],
        [InlineKeyboardButton("📂 Publications", callback_data="admin_channel_list")],
        [InlineKeyboardButton("📊 Statistiques", callback_data="admin_channel_stats")],
        [InlineKeyboardButton("↩️ Panneau admin", callback_data="admin_panel")],
    ])

async def channel_callback(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    query = update.callback_query
    await query.answer()
    data = query.data

    try:
        from config import ADMIN_IDS
        if update.effective_user.id not in ADMIN_IDS:
            await query.answer("Non autorisé", show_alert=True)
            return
    except:
        pass

    if data == "admin_channel":
        ensure_channel_schema()
        txt = f"📢 GESTION DU CANAL\n\nCanal : {CHANNEL_USERNAME}\nChoisissez une action :"
        try:
            await query.edit_message_text(txt, reply_markup=get_channel_keyboard())
        except:
            await query.message.reply_text(txt, reply_markup=get_channel_keyboard())
        return

    if data == "admin_channel_publish":
        context.user_data["channel_admin_mode"] = "awaiting_custom"
        await query.edit_message_text(
            f"Canal : {CHANNEL_USERNAME}\n\n✍️ Envoie maintenant le texte que tu veux publier.\n/cancel pour annuler.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="admin_channel")]])
        )
        return

    if data == "admin_channel_program":
        await query.edit_message_text("📅 Programmation bientôt.", reply_markup=get_channel_keyboard())
        return

    if data == "admin_channel_list":
        await query.edit_message_text("📂 Aucune publication (mode safe).", reply_markup=get_channel_keyboard())
        return

    if data == "admin_channel_stats":
        await query.edit_message_text(f"📊 Canal {CHANNEL_USERNAME}\n✅ Actif (mode safe)", reply_markup=get_channel_keyboard())
        return
