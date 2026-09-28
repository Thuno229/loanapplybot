from storage import DB_PATH
import sqlite3
from i18n import tr
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

ADMIN_ID = 8266012108



async def kyc_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enregistre la photo KYC et confirme toujours sa réception au client."""

    if not context.user_data.get("awaiting_kyc_photo"):
        return

    if not update.message or not update.message.photo:
        return

    user_id = update.effective_user.id
    file_id = update.message.photo[-1].file_id

    conn = sqlite3.connect(DB_PATH)

    try:
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE users
            SET kyc_photo_file_id = ?,
                kyc_status = 'pending'
            WHERE telegram_id = ?
            """,
            (file_id, user_id)
        )

        cur.execute(
            """
            SELECT first_name, last_name, country,
                   phone, email, profession
            FROM users
            WHERE telegram_id = ?
            """,
            (user_id,)
        )

        user = cur.fetchone()
        conn.commit()

    finally:
        conn.close()

    context.user_data["awaiting_kyc_photo"] = False

    if not user:
        await update.message.reply_text(
            tr(user_id, "profile_not_found")
        )
        return

    first_name, last_name, country, phone, email, profession = user

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Valider le KYC",
                callback_data=f"kyc_approve:{user_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Rejeter le KYC",
                callback_data=f"kyc_reject:{user_id}"
            )
        ]
    ])

    caption = (
        "🪪 NOUVELLE DEMANDE KYC\n\n"
        f"👤 Nom : {first_name} {last_name}\n"
        f"🌍 Pays : {country}\n"
        f"📞 Téléphone : {phone}\n"
        f"📧 Email : {email}\n"
        f"💼 Profession : {profession}\n"
        f"🆔 Telegram ID : {user_id}\n\n"
        "⚠️ Vérification manuelle requise."
    )

    try:
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=caption,
            reply_markup=keyboard
        )

        print(f"✅ KYC envoyé à l'administrateur : {user_id}")

    except Exception as e:
        print(
            f"❌ Envoi KYC admin impossible "
            f"pour {user_id}: {e}"
        )

    # Le client reçoit toujours une confirmation
    await update.message.reply_text(
        tr(user_id, "kyc_sent")
    )


async def kyc_decision_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "❌ Accès administrateur uniquement.",
            show_alert=True
        )
        return

    await query.answer()

    action, user_id_text = query.data.split(":", 1)
    user_id = int(user_id_text)

    status = "approved" if action == "kyc_approve" else "rejected"

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET kyc_status = ?
        WHERE telegram_id = ?
        """,
        (status, user_id)
    )

    conn.commit()
    conn.close()

    if status == "approved":
        admin_text = "✅ KYC VALIDÉ"
        client_text = tr(user_id, "kyc_approved")
    else:
        admin_text = "❌ KYC REJETÉ"
        client_text = tr(user_id, "kyc_rejected")

    await query.edit_message_caption(
        caption=admin_text
    )

    await context.bot.send_message(
        chat_id=user_id,
        text=client_text
    )
