import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes


ADMIN_ID = 8266012108


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text(
            "❌ Accès réservé à l'administrateur."
        )
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "👥 Comptes",
                callback_data="admin_users"
            )
        ],
        [
            InlineKeyboardButton(
                "🪪 KYC en attente",
                callback_data="admin_kyc"
            )
        ],
        [
            InlineKeyboardButton(
                "💰 Demandes de prêt",
                callback_data="admin_loans"
            )
        ],
    ])

    await update.message.reply_text(
        "🔐 PANNEAU ADMINISTRATEUR\n\n"
        "Choisissez une section :",
        reply_markup=keyboard
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != ADMIN_ID:
        await query.answer(
            "❌ Accès refusé.",
            show_alert=True
        )
        return

    data = query.data

    # =========================
    # LISTE DES COMPTES
    # =========================
    if data == "admin_users":
        conn = sqlite3.connect("loan_bot.db")
        cur = conn.cursor()

        cur.execute("""
            SELECT telegram_id, first_name, last_name,
                   country, email, kyc_status, blocked
            FROM users
            ORDER BY id DESC
        """)

        users = cur.fetchall()
        conn.close()

        if not users:
            await query.edit_message_text(
                "👥 COMPTES\n\n"
                "Aucun compte enregistré."
            )
            return

        buttons = []

        for user in users:
            telegram_id, first_name, last_name, country, email, kyc, blocked = user

            name = f"{first_name or ''} {last_name or ''}".strip()
            if not name:
                name = "Utilisateur"

            status = "🔒 Bloqué" if blocked else "🟢 Actif"

            buttons.append([
                InlineKeyboardButton(
                    f"👤 {name} — {status}",
                    callback_data=f"admin_user:{telegram_id}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "⬅️ Retour",
                callback_data="admin_back"
            )
        ])

        await query.edit_message_text(
            f"👥 COMPTES ENREGISTRÉS : {len(users)}\n\n"
            "Sélectionnez un compte :",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # =========================
    # DÉTAIL D'UN COMPTE
    # =========================
    if data.startswith("admin_user:"):
        telegram_id = int(data.split(":", 1)[1])

        conn = sqlite3.connect("loan_bot.db")
        cur = conn.cursor()

        cur.execute("""
            SELECT telegram_id, username, first_name, last_name,
                   country, phone, email, profession,
                   trc20_address, bep20_address,
                   kyc_status, blocked, created_at
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,))

        user = cur
