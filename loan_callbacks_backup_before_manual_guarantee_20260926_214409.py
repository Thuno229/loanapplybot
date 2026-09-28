import sqlite3
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

ADMIN_ID = 8266012108
async def loan_confirm_callback(update, context):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    amount = context.user_data.get("loan_amount")
    network = context.user_data.get("loan_network")
    wallet = context.user_data.get("wallet_address")
    duration = context.user_data.get("loan_duration")
    interest = context.user_data.get("interest")
    total_repayment = context.user_data.get("total_repayment")
    monthly_payment = context.user_data.get("monthly_payment")

    if not amount or not network or not wallet or not duration:
        await query.edit_message_text(
            "❌ Les informations de la demande sont incomplètes.\n\n"
            "Veuillez recommencer la demande."
        )
        return

    guarantee = amount * 0.15

    conn = sqlite3.connect("loan_bot.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO loan_requests
        (telegram_id, amount, guarantee, network, repayment_period,
         status, guarantee_status, wallet_address)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            amount,
            guarantee,
            network,
            f"{duration} mois",
            "pending",
            "not_paid",
            wallet
        )
    )

    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # =========================
    # NOTIFICATION AUTOMATIQUE ADMIN
    # =========================
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Approuver",
                callback_data=f"admin_loan_approve:{request_id}"
            ),
            InlineKeyboardButton(
                "❌ Rejeter",
                callback_data=f"admin_loan_reject:{request_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "📋 Voir le dossier",
                callback_data=f"admin_loan:{request_id}"
            )
        ]
    ])

    admin_message = (
        "🚨 NOUVELLE DEMANDE DE PRÊT\n\n"
        f"🆔 Demande : #{request_id}\n"
        f"👤 Telegram ID : {user_id}\n"
        f"💰 Montant : {amount:g} USDT\n"
        f"📅 Durée : {duration} mois\n"
        "📈 Intérêt : 1 % / mois\n"
        f"💵 Intérêts totaux : {interest:g} USDT\n"
        f"💳 Total à rembourser : {total_repayment:g} USDT\n"
        f"🧮 Mensualité : {monthly_payment:.2f} USDT\n"
        f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
        f"🌐 Réseau : {network}\n"
        f"📍 Adresse : {wallet}\n\n"
        "⏳ Statut : EN ATTENTE\n\n"
        "⚠️ Vérification manuelle requise.\n"
        "Choisissez une action ci-dessous."
    )

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            reply_markup=admin_keyboard
        )
    except Exception as e:
        print(f"❌ Impossible d'envoyer la notification admin : {e}")

    context.user_data.pop("loan_amount", None)
    context.user_data.pop("loan_network", None)
    context.user_data.pop("wallet_address", None)
    context.user_data.pop("loan_duration", None)
    context.user_data.pop("interest", None)
    context.user_data.pop("total_repayment", None)
    context.user_data.pop("monthly_payment", None)
    context.user_data.pop("awaiting_loan_duration", None)
    context.user_data.pop("awaiting_loan_amount", None)
    context.user_data.pop("awaiting_wallet_address", None)

    await query.edit_message_text(
        "✅ Demande enregistrée avec succès.\n\n"
        f"🆔 Demande : #{request_id}\n"
        f"💰 Montant : {amount:g} USDT\n"
        f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
        f"🌐 Réseau : {network}\n"
        f"📍 Adresse : {wallet}\n\n"
        "⏳ Statut : en attente de vérification manuelle.\n\n"
        "⚠️ Aucune validation automatique du paiement n'est effectuée."
    )


async def loan_cancel_callback(update, context):
    query = update.callback_query
    await query.answer()

    context.user_data.pop("loan_amount", None)
    context.user_data.pop("loan_network", None)
    context.user_data.pop("wallet_address", None)
    context.user_data.pop("loan_duration", None)
    context.user_data.pop("interest", None)
    context.user_data.pop("total_repayment", None)
    context.user_data.pop("monthly_payment", None)
    context.user_data.pop("awaiting_loan_duration", None)
    context.user_data.pop("awaiting_loan_amount", None)
    context.user_data.pop("awaiting_wallet_address", None)

    await query.edit_message_text(
        "❌ Demande annulée.\n\n"
        "Aucune demande n'a été enregistrée."
    )
