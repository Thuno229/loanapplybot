"""Gestion du canal Telegram pour Loan Request Assistant.

Ce module est volontairement séparé du parcours client. Il utilise les données
existantes de loan_requests/users et ne publie aucune donnée KYC, portefeuille,
TXID ou autre donnée privée dans le canal.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from storage import DB_PATH
from i18n import get_client_language

ADMIN_ID = 8266012108
CHANNEL_ID = os.getenv("CHANNEL_ID", "@GLOBALUSDTFINANCE1")
BOT_USERNAME = os.getenv("BOT_USERNAME", "LoanApply24Bot")

LANGS = ("fr", "en", "es", "pt")

STAGE_LABELS = {
    "fr": {
        "received": "📥 Demande reçue", "verification": "🔍 Vérification",
        "kyc_pending": "🪪 KYC en cours", "kyc_approved": "🟢 KYC validé",
        "kyc_rejected": "❌ KYC rejeté", "analysis": "📋 Analyse du dossier",
        "approved": "✅ Demande approuvée", "disbursement": "💸 Décaissement en cours",
        "disbursed": "💰 Décaissement effectué", "rejected": "❌ Demande rejetée",
        "completed": "🏁 Remboursement terminé",
    },
    "en": {
        "received": "📥 Application received", "verification": "🔍 Verification",
        "kyc_pending": "🪪 KYC pending", "kyc_approved": "🟢 KYC approved",
        "kyc_rejected": "❌ KYC rejected", "analysis": "📋 Application under review",
        "approved": "✅ Application approved", "disbursement": "💸 Disbursement in progress",
        "disbursed": "💰 Disbursement recorded", "rejected": "❌ Application rejected",
        "completed": "🏁 Repayment completed",
    },
    "es": {
        "received": "📥 Solicitud recibida", "verification": "🔍 Verificación",
        "kyc_pending": "🪪 KYC pendiente", "kyc_approved": "🟢 KYC aprobado",
        "kyc_rejected": "❌ KYC rechazado", "analysis": "📋 Solicitud en revisión",
        "approved": "✅ Solicitud aprobada", "disbursement": "💸 Desembolso en curso",
        "disbursed": "💰 Desembolso registrado", "rejected": "❌ Solicitud rechazada",
        "completed": "🏁 Reembolso terminado",
    },
    "pt": {
        "received": "📥 Solicitação recebida", "verification": "🔍 Verificação",
        "kyc_pending": "🪪 KYC pendente", "kyc_approved": "🟢 KYC aprovado",
        "kyc_rejected": "❌ KYC rejeitado", "analysis": "📋 Pedido em análise",
        "approved": "✅ Solicitação aprovada", "disbursement": "💸 Desembolso em andamento",
        "disbursed": "💰 Desembolso registrado", "rejected": "❌ Solicitação rejeitada",
        "completed": "🏁 Reembolso concluído",
    },
}

UI = {
    "fr": {"new": "📢 NOUVELLE DEMANDE", "status": "📌 Statut", "amount": "💰 Montant", "duration": "📅 Durée", "network": "🌐 Réseau", "apply": "💰 Demander un prêt", "check": "🔎 Vérifier ma demande", "support": "📞 Support", "admin": "📢 Gestion du canal", "publish": "📢 Publier", "schedule": "📅 Programmer", "recent": "🗂️ Publications", "stats": "📊 Statistiques", "back": "↩️ Retour", "cancel": "❌ Annuler", "preview": "👀 Aperçu", "publish_now": "📢 Publier maintenant", "edit": "✏️ Modifier", "delete": "🗑️ Supprimer", "pin": "📌 Épingler", "unpin": "📍 Désépingler"},
    "en": {"new": "📢 NEW LOAN APPLICATION", "status": "📌 Status", "amount": "💰 Amount", "duration": "📅 Duration", "network": "🌐 Network", "apply": "💰 Apply for a loan", "check": "🔎 Check my application", "support": "📞 Support", "admin": "📢 Channel management", "publish": "📢 Publish", "schedule": "📅 Schedule", "recent": "🗂️ Publications", "stats": "📊 Statistics", "back": "↩️ Back", "cancel": "❌ Cancel", "preview": "👀 Preview", "publish_now": "📢 Publish now", "edit": "✏️ Edit", "delete": "🗑️ Delete", "pin": "📌 Pin", "unpin": "📍 Unpin"},
    "es": {"new": "📢 NUEVA SOLICITUD DE PRÉSTAMO", "status": "📌 Estado", "amount": "💰 Importe", "duration": "📅 Duración", "network": "🌐 Red", "apply": "💰 Solicitar préstamo", "check": "🔎 Verificar mi solicitud", "support": "📞 Soporte", "admin": "📢 Gestión del canal", "publish": "📢 Publicar", "schedule": "📅 Programar", "recent": "🗂️ Publicaciones", "stats": "📊 Estadísticas", "back": "↩️ Volver", "cancel": "❌ Cancelar", "preview": "👀 Vista previa", "publish_now": "📢 Publicar ahora", "edit": "✏️ Editar", "delete": "🗑️ Eliminar", "pin": "📌 Fijar", "unpin": "📍 Desfijar"},
    "pt": {"new": "📢 NOVA SOLICITAÇÃO DE EMPRÉSTIMO", "status": "📌 Status", "amount": "💰 Valor", "duration": "📅 Duração", "network": "🌐 Rede", "apply": "💰 Solicitar empréstimo", "check": "🔎 Verificar minha solicitação", "support": "📞 Suporte", "admin": "📢 Gestão do canal", "publish": "📢 Publicar", "schedule": "📅 Programar", "recent": "🗂️ Publicações", "stats": "📊 Estatísticas", "back": "↩️ Voltar", "cancel": "❌ Cancelar", "preview": "👀 Pré-visualização", "publish_now": "📢 Publicar agora", "edit": "✏️ Editar", "delete": "🗑️ Excluir", "pin": "📌 Fixar", "unpin": "📍 Desafixar"},
}


def _conn():
    return sqlite3.connect(DB_PATH)


def ensure_channel_schema():
    conn = _conn()
    conn.execute("""CREATE TABLE IF NOT EXISTS channel_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER,
        channel_id TEXT NOT NULL,
        message_id INTEGER NOT NULL,
        language TEXT NOT NULL,
        post_type TEXT NOT NULL DEFAULT 'manual',
        status TEXT NOT NULL DEFAULT 'published',
        scheduled_at TEXT,
        text_content TEXT,
        media_file_id TEXT,
        payload_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_channel_posts_request ON channel_posts(request_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_channel_posts_scheduled ON channel_posts(status, scheduled_at)")
    conn.commit()
    conn.close()


def _t(lang, key):
    return UI.get(lang, UI["fr"]).get(key, UI["fr"].get(key, key))


def _loan_keyboard(lang):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(_t(lang, "apply"), url=f"https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton(_t(lang, "check"), url=f"https://t.me/{BOT_USERNAME}?start=tracking")],
        [InlineKeyboardButton(_t(lang, "support"), url=f"https://t.me/{BOT_USERNAME}")],
    ])


def _stage_label(lang, stage, status=None):
    key = str(stage or status or "received").lower()
    return STAGE_LABELS.get(lang, STAGE_LABELS["fr"]).get(key, key)


def _request_row(request_id):
    conn = _conn()
    row = conn.execute("""SELECT r.id, r.telegram_id, r.amount, r.repayment_period,
        r.network, r.status, r.current_stage, r.created_at, u.language
        FROM loan_requests r LEFT JOIN users u ON u.telegram_id=r.telegram_id
        WHERE r.id=?""", (request_id,)).fetchone()
    conn.close()
    return row


def build_loan_post(row):
    request_id, telegram_id, amount, duration, network, status, stage, created_at, lang = row
    lang = lang if lang in LANGS else get_client_language(telegram_id)
    text = (
        f"{_t(lang, 'new')}\n\n"
        f"🆔 #{request_id}\n"
        f"{_t(lang, 'amount')}: {amount:g} USDT\n"
        f"{_t(lang, 'duration')}: {duration or '-'}\n"
        f"{_t(lang, 'network')}: {network or '-'}\n"
        f"{_t(lang, 'status')}: {_stage_label(lang, stage, status)}\n\n"
        "⚠️ La demande est soumise à vérification et validation manuelles."
        if lang == "fr" else
        "⚠️ The application is subject to manual review and approval."
        if lang == "en" else
        "⚠️ La solicitud está sujeta a revisión y aprobación manual."
        if lang == "es" else
        "⚠️ A solicitação está sujeita a análise e aprovação manual."
    )
    return lang, text, _loan_keyboard(lang)


async def publish_loan_request(bot, request_id):
    """Publie une nouvelle demande une seule fois. Retourne le message_id ou None."""
    ensure_channel_schema()
    row = _request_row(request_id)
    if not row:
        return None
    conn = _conn()
    existing = conn.execute("SELECT message_id FROM channel_posts WHERE request_id=? AND post_type='loan' LIMIT 1", (request_id,)).fetchone()
    conn.close()
    if existing:
        return existing[0]
    try:
        lang, text, markup = build_loan_post(row)
        msg = await bot.send_message(chat_id=CHANNEL_ID, text=text, reply_markup=markup, disable_web_page_preview=True)
        conn = _conn()
        conn.execute("INSERT INTO channel_posts(request_id,channel_id,message_id,language,post_type,status,text_content,payload_json) VALUES(?,?,?,?,?,?,?,?)",
                     (request_id, CHANNEL_ID, msg.message_id, lang, "loan", "published", text, json.dumps({"request_id": request_id})))
        conn.commit(); conn.close()
        return msg.message_id
    except Exception as exc:
        print(f"⚠️ Publication canal impossible pour #{request_id}: {exc}")
        return None


async def update_loan_post(bot, request_id):
    ensure_channel_schema()
    row = _request_row(request_id)
    if not row:
        return False
    conn = _conn()
    post = conn.execute("SELECT id,message_id,language FROM channel_posts WHERE request_id=? AND post_type='loan' ORDER BY id DESC LIMIT 1", (request_id,)).fetchone()
    conn.close()
    if not post:
        return bool(await publish_loan_request(bot, request_id))
    _, message_id, _ = post
    lang, text, markup = build_loan_post(row)
    try:
        await bot.edit_message_text(chat_id=CHANNEL_ID, message_id=message_id, text=text, reply_markup=markup, disable_web_page_preview=True)
        conn = _conn(); conn.execute("UPDATE channel_posts SET language=?,text_content=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (lang,text,post[0])); conn.commit(); conn.close()
        return True
    except Exception as exc:
        print(f"⚠️ Mise à jour canal impossible pour #{request_id}: {exc}")
        return False


async def show_channel_admin(query):
    lang = "fr"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Publier", callback_data="admin_channel_publish")],
        [InlineKeyboardButton("📅 Programmer", callback_data="admin_channel_schedule")],
        [InlineKeyboardButton("🗂️ Publications", callback_data="admin_channel_posts")],
        [InlineKeyboardButton("📊 Statistiques", callback_data="admin_channel_stats")],
        [InlineKeyboardButton("↩️ Panneau admin", callback_data="admin_back")],
    ])
    await query.edit_message_text(
        "📢 GESTION DU CANAL\n\n"
        f"Canal : {CHANNEL_ID}\n\n"
        "Choisissez une action :",
        reply_markup=keyboard,
    )


def _posts_keyboard():
    conn = _conn()
    rows = conn.execute("SELECT id, request_id, message_id, post_type, status FROM channel_posts ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    buttons = []
    for pid, request_id, message_id, post_type, status in rows:
        label = f"#{request_id or 'PUB'} · msg {message_id} · {status}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"admin_channel_post:{pid}")])
    buttons.append([InlineKeyboardButton("↩️ Retour", callback_data="admin_channel")])
    return InlineKeyboardMarkup(buttons)


async def channel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or query.from_user.id != ADMIN_ID:
        if query: await query.answer("❌ Accès réservé à l'administrateur.", show_alert=True)
        return
    await query.answer()
    data = query.data

    if data == "admin_channel":
        await show_channel_admin(query); return
    if data == "admin_channel_publish":
        context.user_data["channel_admin_mode"] = "publish"
        await query.edit_message_text("📢 PUBLICATION\n\nEnvoyez maintenant le texte à publier.\nVous pouvez aussi envoyer une photo avec une légende.\n\n❌ /cancel pour annuler.")
        return
    if data == "admin_channel_schedule":
        context.user_data["channel_admin_mode"] = "schedule"
        await query.edit_message_text("📅 PROGRAMMATION\n\nEnvoyez d'abord le texte (ou photo + légende).\nEnsuite je demanderai la date/heure au format :\nYYYY-MM-DD HH:MM\n\nFuseau Railway/serveur : UTC.\n\n❌ /cancel pour annuler.")
        return
    if data == "admin_channel_preview":
        await _send_preview(query, context); return
    if data == "admin_channel_publish_now":
        await _publish_draft(query, context); return
    if data == "admin_channel_schedule_confirm":
        context.user_data["channel_admin_mode"] = "schedule_time"
        await query.edit_message_text("📅 Envoyez la date et l'heure UTC : YYYY-MM-DD HH:MM")
        return
    if data == "admin_channel_cancel":
        for k in ("channel_admin_mode","channel_admin_draft"):
            context.user_data.pop(k, None)
        await show_channel_admin(query); return
    if data == "admin_channel_posts":
        await query.edit_message_text("🗂️ PUBLICATIONS RÉCENTES", reply_markup=_posts_keyboard()); return
    if data == "admin_channel_stats":
        conn = _conn()
        total = conn.execute("SELECT COUNT(*) FROM channel_posts").fetchone()[0]
        loans = conn.execute("SELECT COUNT(*) FROM channel_posts WHERE post_type='loan'").fetchone()[0]
        manual = conn.execute("SELECT COUNT(*) FROM channel_posts WHERE post_type='manual'").fetchone()[0]
        scheduled = conn.execute("SELECT COUNT(*) FROM channel_posts WHERE status='scheduled'").fetchone()[0]
        conn.close()
        await query.edit_message_text(f"📊 STATISTIQUES DU CANAL\n\n📢 Publications : {total}\n💰 Demandes : {loans}\n✍️ Manuelles : {manual}\n📅 Programmées : {scheduled}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Retour", callback_data="admin_channel")]])); return
    if data.startswith("admin_channel_post:"):
        pid = int(data.split(":",1)[1])
        conn = _conn(); row = conn.execute("SELECT request_id,message_id,status,post_type,text_content FROM channel_posts WHERE id=?", (pid,)).fetchone(); conn.close()
        if not row:
            await query.answer("Publication introuvable.", show_alert=True); return
        request_id, message_id, status, post_type, text_content = row
        buttons = [
            [InlineKeyboardButton("✏️ Modifier", callback_data=f"admin_channel_edit:{pid}")],
            [InlineKeyboardButton("🗑️ Supprimer", callback_data=f"admin_channel_delete:{pid}"), InlineKeyboardButton("📌 Épingler", callback_data=f"admin_channel_pin:{pid}")],
            [InlineKeyboardButton("📍 Désépingler", callback_data=f"admin_channel_unpin:{pid}")],
            [InlineKeyboardButton("↩️ Retour", callback_data="admin_channel_posts")],
        ]
        await query.edit_message_text(f"🗂️ PUBLICATION #{pid}\n\n🆔 Demande : {request_id or '-'}\n💬 Message Telegram : {message_id}\n📌 État : {status}\n\n{text_content[:1500]}", reply_markup=InlineKeyboardMarkup(buttons)); return
    if data.startswith("admin_channel_delete:"):
        pid = int(data.split(":",1)[1]); conn = _conn(); row = conn.execute("SELECT message_id FROM channel_posts WHERE id=?", (pid,)).fetchone(); conn.close()
        if row:
            try: await context.bot.delete_message(CHANNEL_ID, row[0])
            except Exception as exc: print(f"⚠️ Suppression canal: {exc}")
            conn = _conn(); conn.execute("UPDATE channel_posts SET status='deleted',updated_at=CURRENT_TIMESTAMP WHERE id=?", (pid,)); conn.commit(); conn.close()
        await query.answer("✅ Publication supprimée.", show_alert=True); await show_channel_admin(query); return
    if data.startswith("admin_channel_pin:") or data.startswith("admin_channel_unpin:"):
        pid = int(data.split(":",1)[1]); conn = _conn(); row = conn.execute("SELECT message_id FROM channel_posts WHERE id=?", (pid,)).fetchone(); conn.close()
        if row:
            try:
                if data.startswith("admin_channel_pin:"): await context.bot.pin_chat_message(CHANNEL_ID, row[0], disable_notification=True)
                else: await context.bot.unpin_chat_message(CHANNEL_ID, row[0])
            except Exception as exc: print(f"⚠️ Gestion épingle: {exc}")
        await query.answer("✅ Action effectuée.", show_alert=True); return
    if data.startswith("admin_channel_edit:"):
        pid = int(data.split(":",1)[1]); context.user_data["channel_admin_mode"]="edit"; context.user_data["channel_admin_edit_id"]=pid
        await query.edit_message_text("✏️ Envoyez le nouveau texte de la publication.\n\n❌ /cancel pour annuler."); return


async def _send_preview(query, context):
    draft = context.user_data.get("channel_admin_draft")
    if not draft:
        await query.answer("Aucun brouillon.", show_alert=True); return
    markup = _loan_keyboard("fr")
    if draft.get("photo"):
        await context.bot.send_photo(chat_id=query.from_user.id, photo=draft["photo"], caption=draft["text"], reply_markup=markup)
    else:
        await context.bot.send_message(chat_id=query.from_user.id, text=draft["text"], reply_markup=markup)
    await query.edit_message_text("👀 Aperçu envoyé ci-dessus. Choisissez :", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Publier maintenant", callback_data="admin_channel_publish_now")],
        [InlineKeyboardButton("📅 Programmer", callback_data="admin_channel_schedule_confirm")],
        [InlineKeyboardButton("❌ Annuler", callback_data="admin_channel_cancel")],
    ]))


async def _publish_draft(query, context):
    draft = context.user_data.get("channel_admin_draft")
    if not draft: await query.answer("Aucun brouillon.", show_alert=True); return
    try:
        if draft.get("photo"):
            msg = await context.bot.send_photo(CHANNEL_ID, photo=draft["photo"], caption=draft["text"], reply_markup=_loan_keyboard("fr"))
            media = draft["photo"]
        else:
            msg = await context.bot.send_message(CHANNEL_ID, draft["text"], reply_markup=_loan_keyboard("fr"), disable_web_page_preview=True)
            media = None
        conn = _conn(); conn.execute("INSERT INTO channel_posts(channel_id,message_id,language,post_type,status,text_content,media_file_id) VALUES(?,?,?,?,?,?,?)", (CHANNEL_ID,msg.message_id,"fr","manual","published",draft["text"],media)); conn.commit(); conn.close()
        await query.answer("✅ Publication envoyée dans le canal.", show_alert=True)
    except Exception as exc:
        await query.answer("❌ Échec de publication. Vérifiez les droits du bot et CHANNEL_ID.", show_alert=True); print(f"❌ Publication manuelle: {exc}")
    context.user_data.pop("channel_admin_draft", None); context.user_data.pop("channel_admin_mode", None)
    await show_channel_admin(query)


async def channel_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id != ADMIN_ID:
        return
    mode = context.user_data.get("channel_admin_mode")
    if not mode:
        return
    if update.message.text and update.message.text.startswith("/cancel"):
        context.user_data.pop("channel_admin_mode", None); context.user_data.pop("channel_admin_draft", None); context.user_data.pop("channel_admin_edit_id", None)
        await update.message.reply_text("❌ Annulé."); return
    if mode in ("publish", "schedule"):
        text = update.message.caption if update.message.photo else update.message.text
        if not text:
            await update.message.reply_text("❌ Envoyez du texte ou une photo avec une légende."); return
        draft = {"text": text[:4096]}
        if update.message.photo: draft["photo"] = update.message.photo[-1].file_id
        context.user_data["channel_admin_draft"] = draft
        context.user_data["channel_admin_mode"] = "draft_ready"
        await update.message.reply_text("👀 Brouillon prêt. Choisissez une action :", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Publier maintenant", callback_data="admin_channel_publish_now")],
            [InlineKeyboardButton("📅 Programmer", callback_data="admin_channel_schedule_confirm")],
            [InlineKeyboardButton("❌ Annuler", callback_data="admin_channel_cancel")],
        ])); return
    if mode == "schedule_time":
        raw = (update.message.text or "").strip()
        try:
            dt = datetime.strptime(raw, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            await update.message.reply_text("❌ Format incorrect. Exemple : 2026-10-01 18:30"); return
        if dt <= datetime.now(timezone.utc):
            await update.message.reply_text("❌ La date doit être dans le futur."); return
        draft = context.user_data.get("channel_admin_draft")
        if not draft:
            await update.message.reply_text("❌ Aucun brouillon."); return
        conn = _conn(); cur = conn.cursor(); cur.execute("INSERT INTO channel_posts(channel_id,message_id,language,post_type,status,scheduled_at,text_content,media_file_id,payload_json) VALUES(?,?,?,?,?,?,?,?,?)", (CHANNEL_ID,0,"fr","manual","scheduled",dt.isoformat(),draft["text"],draft.get("photo"),json.dumps(draft))); pid=cur.lastrowid; conn.commit(); conn.close()
        if context.job_queue:
            context.job_queue.run_once(publish_scheduled_post, when=dt, data={"post_id": pid}, name=f"channel_post_{pid}")
        context.user_data.pop("channel_admin_mode", None); context.user_data.pop("channel_admin_draft", None)
        await update.message.reply_text(f"✅ Publication programmée pour {dt.strftime('%Y-%m-%d %H:%M')} UTC."); return
    if mode == "edit":
        pid = context.user_data.get("channel_admin_edit_id")
        text = update.message.caption if update.message.photo else update.message.text
        if not pid or not text:
            await update.message.reply_text("❌ Texte invalide."); return
        conn=_conn(); row=conn.execute("SELECT message_id FROM channel_posts WHERE id=?",(pid,)).fetchone(); conn.close()
        if not row: await update.message.reply_text("❌ Publication introuvable."); return
        try:
            await context.bot.edit_message_text(CHANNEL_ID,row[0],text=text,reply_markup=_loan_keyboard("fr"),disable_web_page_preview=True)
            conn=_conn(); conn.execute("UPDATE channel_posts SET text_content=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(text,pid)); conn.commit(); conn.close()
            await update.message.reply_text("✅ Publication modifiée.")
        except Exception as exc: await update.message.reply_text("❌ Modification impossible."); print(exc)
        context.user_data.pop("channel_admin_mode",None); context.user_data.pop("channel_admin_edit_id",None)


async def publish_scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    pid = context.job.data["post_id"]
    conn=_conn(); row=conn.execute("SELECT text_content,media_file_id FROM channel_posts WHERE id=? AND status='scheduled'",(pid,)).fetchone(); conn.close()
    if not row: return
    try:
        if row[1]: msg=await context.bot.send_photo(CHANNEL_ID,photo=row[1],caption=row[0],reply_markup=_loan_keyboard("fr"))
        else: msg=await context.bot.send_message(CHANNEL_ID,row[0],reply_markup=_loan_keyboard("fr"),disable_web_page_preview=True)
        conn=_conn(); conn.execute("UPDATE channel_posts SET message_id=?,status='published',updated_at=CURRENT_TIMESTAMP WHERE id=?",(msg.message_id,pid)); conn.commit(); conn.close()
    except Exception as exc: print(f"❌ Publication programmée {pid}: {exc}")


async def restore_scheduled_posts(application):
    ensure_channel_schema()
    conn=_conn(); rows=conn.execute("SELECT id,scheduled_at FROM channel_posts WHERE status='scheduled' AND scheduled_at IS NOT NULL").fetchall(); conn.close()
    if not application.job_queue: return
    now=datetime.now(timezone.utc)
    for pid, raw in rows:
        try: dt=datetime.fromisoformat(raw)
        except Exception: continue
        if dt <= now: dt=now
        application.job_queue.run_once(publish_scheduled_post, when=dt, data={"post_id":pid}, name=f"channel_post_{pid}")
