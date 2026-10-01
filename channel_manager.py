import json, os
from pathlib import Path
try:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
except:
    pass

STATE_FILE = Path("/tmp/channel_state.json")

def _load():
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
    except: pass
    return {}

def _save(d):
    try: STATE_FILE.write_text(json.dumps(d))
    except: pass

def is_awaiting(uid):
    return str(uid) in _load()

def set_awaiting(uid):
    d=_load(); d[str(uid)]="awaiting"; _save(d)

def clear_awaiting(uid):
    d=_load(); d.pop(str(uid),None); _save(d)

async def channel_admin_menu(update, context):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from config import CHANNEL_ID, CHANNEL_LINK
    kb=[[InlineKeyboardButton("📢 Publier", callback_data="channel_publish")],
        [InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")]]
    text=f"📢 Canal: {CHANNEL_LINK}\nID: {CHANNEL_ID}"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def channel_callback(update, context):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id
    if q.data=="channel_publish":
        set_awaiting(uid)
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        await q.edit_message_text("✍️ Envoie maintenant le texte à publier.\n/cancel pour annuler", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="admin_channel")]]))
    else:
        clear_awaiting(uid)
        from admin_manager import admin_panel
        await admin_panel(update, context)

async def channel_admin_message(update, context):
    uid=update.effective_user.id
    if not is_awaiting(uid):
        return False
    txt=(update.message.text or "").strip()
    if not txt or txt.startswith("/"):
        clear_awaiting(uid)
        await update.message.reply_text("❌ Annulé")
        return True
    try:
        from config import CHANNEL_ID, CHANNEL_LINK
        await context.bot.send_message(chat_id=CHANNEL_ID, text=txt)
        clear_awaiting(uid)
        await update.message.reply_text(f"✅ Publié dans {CHANNEL_LINK}")
    except Exception as e:
        clear_awaiting(uid)
        await update.message.reply_text(f"❌ Erreur: {e}\nVérifie que le bot est admin dans le canal.")
    return True
