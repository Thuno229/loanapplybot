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
    txid = context.user_data.get("loan_txid")
    guarantee_address = context.user_data.get("guarantee_address")

    if not amount or not network or not wallet or not duration or not txid or not guarantee_address:
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
         status, guarantee_status, wallet_address, guarantee_address, txid)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            amount,
            guarantee,
            network,
            f"{duration} mois",
            "pending",
            "not_paid",
            wallet,
            guarantee_address,
            txid
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
        f"📍 Adresse : {wallet}\n"
        f"📍 Adresse de garantie ({network}) : {guarantee_address}\n"
        f"📄 TXID : {txid}\n\n"
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
    context.user_data.pop("loan_txid", None)
    context.user_data.pop("guarantee_address", None)
    context.user_data.pop("awaiting_loan_txid", None)

    await query.edit_message_text(
        "✅ Demande enregistrée avec succès.\n\n"
        f"🆔 Demande : #{request_id}\n"
        f"💰 Montant : {amount:g} USDT\n"
        f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
        f"🌐 Réseau : {network}\n"
        f"📍 Adresse : {wallet}\n"
        f"📄 TXID : {txid}\n\n"
        "⏳ Statut : en attente de vérification manuelle.\n\n"
        "⚠️ Aucune validation automatique du paiement n'est effectuée."
    )


async def loan_conditions_accept_callback(update, context):
    query = update.callback_query
    await query.answer()

    amount = context.user_data.get("loan_amount")
    network = context.user_data.get("loan_network")
    wallet = context.user_data.get("wallet_address")
    duration = context.user_data.get("loan_duration")
    interest = context.user_data.get("interest", 0)
    total_repayment = context.user_data.get("total_repayment", 0)
    monthly_payment = context.user_data.get("monthly_payment", 0)

    if not amount or not network or not wallet or not duration:
        await query.edit_message_text(
            "❌ Les informations de votre demande sont incomplètes.\n\n"
            "Veuillez recommencer la demande."
        )
        return

    if network == "TRC20":
        guarantee_address = "TAju6xk1rm78Em64ABZJpqHiXoGqF62QBk"
    elif network == "BEP20":
        guarantee_address = "0x6632413e8ba2750d33dc1047a73d01268d345893"
    else:
        await query.edit_message_text(
            "❌ Réseau invalide. Veuillez recommencer."
        )
        return

    context.user_data["guarantee_address"] = guarantee_address
    guarantee = amount * 0.15

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📋 Copier l'adresse",
            callback_data="copy_guarantee_address"
        )],
        [InlineKeyboardButton(
            "🔍 Vérifier l'adresse",
            callback_data="verify_guarantee_address"
        )],
        [InlineKeyboardButton(
            "✅ Garantie envoyée",
            callback_data="loan_guarantee_sent"
        )],
        [InlineKeyboardButton(
            "❌ Annuler",
            callback_data="loan_cancel"
        )]
    ])

    await query.edit_message_text(
        "📋 CONDITIONS ACCEPTÉES\n\n"
        f"💰 Montant : {amount:g} USDT\n"
        f"📅 Durée : {duration} mois\n"
        "📈 Intérêt : 1 % / mois\n"
        f"💵 Intérêts totaux : {interest:g} USDT\n"
        f"💳 Total à rembourser : {total_repayment:g} USDT\n"
        f"🧮 Mensualité : {monthly_payment:.2f} USDT\n"
        f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
        f"🌐 Réseau : {network}\n\n"
        f"📍 Adresse de réception du service ({network}) :\n"
        f"{guarantee_address}\n\n"
        "⚠️ Cette adresse est affichée pour le suivi du dossier.\n"
        "Le bot ne vérifie aucun paiement automatiquement.\n\n"
        "Si une opération liée à ce dossier a déjà été effectuée, "
        "vous pouvez continuer et déclarer son TXID/hash pour vérification manuelle.",
        reply_markup=keyboard
    )

async def loan_guarantee_sent_callback(update, context):
    query = update.callback_query
    await query.answer()

    amount = context.user_data.get("loan_amount")
    network = context.user_data.get("loan_network")
    wallet = context.user_data.get("wallet_address")
    duration = context.user_data.get("loan_duration")

    if not amount or not network or not wallet or not duration:
        await query.edit_message_text(
            "❌ Les informations de votre demande sont incomplètes.\n\n"
            "Veuillez recommencer la demande."
        )
        return

    context.user_data["awaiting_loan_txid"] = True

    guarantee = amount * 0.15

    await query.edit_message_text(
        "📄 TXID / HASH DE TRANSACTION\n\n"
        f"💰 Montant du prêt : {amount:g} USDT\n"
        f"📊 Garantie indicative : {guarantee:g} USDT\n"
        f"🌐 Réseau : {network}\n\n"
        "Si une opération liée à ce dossier a déjà été effectuée, "
        "envoyez maintenant son TXID/hash.\n\n"
        "⚠️ Le TXID sera vérifié manuellement. "
        "Le bot ne valide aucun paiement automatiquement.\n\n"
        "Exemple : 0x... ou TXID..."
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
