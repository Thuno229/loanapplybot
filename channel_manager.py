import json
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

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
    d=_load()
    # check fichier + user_data fallback
    return str(uid) in d

def set_awaiting(uid):
    d=_load(); d[str(uid)]="awaiting"; _save(d)

def clear_awaiting(uid):
    d=_load(); d.pop(str(uid),None); _save(d)

async def channel_admin_menu(update, context):
    from config import CHANNEL_ID, CHANNEL_LINK
    kb=[[InlineKeyboardButton("📢 Publier", callback_data="channel_publish")],
        [InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")]]
    txt=f"📢 GESTION CANAL\n\nCanal: {CHANNEL_LINK}\nID: {CHANNEL_ID}"
    if update.callback_query:
        await update.callback_query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(txt, reply_markup=InlineKeyboardMarkup(kb))

async def channel_callback(update, context):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id
    if q.data=="channel_publish":
        set_awaiting(uid)
        context.user_data["channel_admin_mode"]="awaiting_custom"
        await q.edit_message_text(f"✍️ Envoie maintenant le texte à publier dans @GLOBALUSDTFINANCE1\n\n/cancel pour annuler", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Annuler", callback_data="admin_channel")]]))
    else:
        clear_awaiting(uid)
        context.user_data.pop("channel_admin_mode",None)
        from admin_manager import admin_panel
        await admin_panel(update, context)

async def channel_admin_message(update, context):
    uid=update.effective_user.id
    if not is_awaiting(uid) and context.user_data.get("channel_admin_mode")!="awaiting_custom":
        return False
    txt=(update.message.text or "").strip()
    if not txt or txt.startswith("/cancel"):
        clear_awaiting(uid)
        context.user_data.pop("channel_admin_mode",None)
        await update.message.reply_text("❌ Annulé")
        return True
    try:
        from config import CHANNEL_ID, CHANNEL_LINK
        await context.bot.send_message(chat_id=CHANNEL_ID, text=txt)
        clear_awaiting(uid)
        context.user_data.pop("channel_admin_mode",None)
        await update.message.reply_text(f"✅ Publié dans {CHANNEL_LINK}")
    except Exception as e:
        clear_awaiting(uid)
        context.user_data.pop("channel_admin_mode",None)
        await update.message.reply_text(f"❌ Erreur: {e}")
    return True
