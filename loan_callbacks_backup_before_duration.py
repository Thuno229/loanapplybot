import sqlite3
async def loan_confirm_callback(update, context):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    amount = context.user_data.get("loan_amount")
    network = context.user_data.get("loan_network")
    wallet = context.user_data.get("wallet_address")

    if not amount or not network or not wallet:
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
            "pending",
            "pending",
            "not_paid",
            wallet
        )
    )

    request_id = cursor.lastrowid
    conn.commit()
    conn.close()

    context.user_data.pop("loan_amount", None)
    context.user_data.pop("loan_network", None)
    context.user_data.pop("wallet_address", None)
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
    context.user_data.pop("awaiting_wallet_address", None)

    await query.edit_message_text(
        "❌ Demande annulée.\n\n"
        "Aucune demande n'a été enregistrée."
    )
