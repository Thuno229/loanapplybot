import json
from pathlib import Path
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
try:
    from config import CHANNEL_ID, CHANNEL_LINK
except:
    CHANNEL_ID = "@GLOBALUSDTFINANCE1"
    CHANNEL_LINK = "https://t.me/GLOBALUSDTFINANCE1"
FILE = Path("/tmp/channel_state.json")
def _l():
    try:
        if FILE.exists(): return json.loads(FILE.read_text())
    except: pass
    return {}
def _s(d):
    try: FILE.write_text(json.dumps(d))
    except: pass
def is_awaiting(uid): return str(uid) in _l()
def set_awaiting(uid):
    d=_l(); d[str(uid)]="1"; _s(d)
def clear_awaiting(uid):
    d=_l(); d.pop(str(uid),None); _s(d)

async def channel_admin_menu(update, context):
    kb=[[InlineKeyboardButton("📢 Publier", callback_data="channel_publish")],
        [InlineKeyboardButton("🔙 Retour Admin", callback_data="admin_back")]]
    await update.callback_query.edit_message_text(f"📢 CANAL {CHANNEL_LINK}", reply_markup=InlineKeyboardMarkup(kb))

async def channel_callback(update, context):
    q=update.callback_query; await q.answer()
    if q.data in ("admin_channel","channel_menu"): await channel_admin_menu(update, context)
    elif q.data=="channel_publish":
        set_awaiting(q.from_user.id); context.user_data["channel_admin_mode"]="awaiting_custom"
        await q.edit_message_text(f"✍️ Envoie le texte pour {CHANNEL_LINK}\n/cancel pour annuler")
    else:
        clear_awaiting(q.from_user.id); context.user_data.pop("channel_admin_mode",None)
        from bot import admin_panel
        await admin_panel(update, context)

async def channel_admin_message(update, context):
    uid=update.effective_user.id
    if not is_awaiting(uid): return False
    txt=(update.message.text or "").strip()
    if not txt or txt.startswith("/cancel"):
        clear_awaiting(uid); context.user_data.pop("channel_admin_mode",None)
        await update.message.reply_text("❌ Annulé"); return True
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=txt)
        clear_awaiting(uid); context.user_data.pop("channel_admin_mode",None)
        await update.message.reply_text(f"✅ Publié dans {CHANNEL_LINK}")
    except Exception as e:
        clear_awaiting(uid); context.user_data.pop("channel_admin_mode",None)
        await update.message.reply_text(f"❌ Erreur: {e}")
    return True
def ensure_channel_schema(): pass
async def publish_loan_request(bot, request_id, amount, duration, network):
    text = (
        "📢 NOUVELLE DEMANDE DE PRÊT\n\n"
        f"🆔 Demande : #{request_id}\n"
        f"💰 Montant demandé : {amount:g} USDT\n"
        f"📅 Durée : {duration} mois\n"
        f"🌐 Réseau : {network}\n"
        "📌 Statut : EN ATTENTE\n\n"
        "⚠️ Demande soumise à vérification et approbation manuelle."
    )
    await bot.send_message(chat_id=CHANNEL_ID, text=text)

async def update_loan_post(a,b,c): pass
async def restore_scheduled_posts(a=None): pass
