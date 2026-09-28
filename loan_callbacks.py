from storage import DB_PATH
import os
import sqlite3
from i18n import tr
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, CopyTextButton

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

    if context.user_data.get("loan_confirm_in_progress"):
        await query.answer(
            tr(user_id, "loan_processing"),
            show_alert=True
        )
        return

    if not amount or not network or not wallet or not duration or not txid or not guarantee_address:
        await query.edit_message_text(
            tr(user_id, "loan_request_incomplete")
        )
        return

    # Verrou immédiat : empêche deux confirmations simultanées.
    context.user_data["loan_confirm_in_progress"] = True

    guarantee = amount * 0.15

    conn = sqlite3.connect(os.path.join(os.getenv("BOT_DATA_DIR", "."), "loan_bot.db"))
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
    context.user_data.pop("awaiting_network", None)
    context.user_data.pop("awaiting_loan_txid", None)
    context.user_data.pop("loan_flow_active", None)
    context.user_data.pop("loan_confirm_in_progress", None)
    context.user_data.pop("awaiting_network", None)
    context.user_data.pop("awaiting_loan_txid", None)
    context.user_data.pop("loan_flow_active", None)
    context.user_data.pop("loan_confirm_in_progress", None)
    context.user_data.pop("loan_txid", None)
    context.user_data.pop("guarantee_address", None)
    context.user_data.pop("awaiting_loan_txid", None)
    context.user_data.pop("loan_flow_active", None)
    context.user_data.pop("loan_confirm_in_progress", None)

    await query.edit_message_text(
        tr(
            user_id,
            "loan_submitted",
            request_id=request_id,
            amount=amount,
            guarantee=guarantee,
            network=network,
            wallet=wallet,
            txid=txid,
        )
    )


async def loan_conditions_accept_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    amount = context.user_data.get("loan_amount")
    network = context.user_data.get("loan_network")
    wallet = context.user_data.get("wallet_address")
    duration = context.user_data.get("loan_duration")
    interest = context.user_data.get("interest", 0)
    total_repayment = context.user_data.get("total_repayment", 0)
    monthly_payment = context.user_data.get("monthly_payment", 0)

    if amount is None or not network or not wallet or duration is None:
        await query.edit_message_text(
            tr(user_id, "loan_request_incomplete")
        )
        return

    addresses = {
        "TRC20": "TAju6xk1rm78Em64ABZJpqHiXoGqF62QBk",
        "BEP20": "0x6632413e8ba2750d33dc1047a73d01268d345893",
    }

    guarantee_address = addresses.get(network)

    if not guarantee_address:
        await query.edit_message_text(tr(user_id, "network_not_found_callback"))
        return

    context.user_data["guarantee_address"] = guarantee_address

    guarantee = amount * 0.15

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                tr(user_id, "show_guarantee_address"),
                callback_data="verify_guarantee_address"
            )
        ],
        [
            InlineKeyboardButton(
                tr(user_id, "cancel_button"),
                callback_data="loan_cancel"
            )
        ]
    ])

    message = tr(
        user_id,
        "loan_conditions",
        amount=amount,
        duration=duration,
        interest=interest,
        total=total_repayment,
        monthly=monthly_payment,
        guarantee=guarantee,
        network=network,
        wallet=wallet,
    )

    await query.edit_message_text(
        message,
        reply_markup=keyboard
    )


async def verify_guarantee_address_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    network = context.user_data.get("loan_network")
    guarantee_address = context.user_data.get("guarantee_address")
    amount = context.user_data.get("loan_amount", 0)

    if not network or not guarantee_address:
        await query.answer(
            tr(user_id, "guarantee_address_unavailable"),
            show_alert=True
        )
        return

    guarantee = amount * 0.15

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                tr(user_id, "copy_address"),
                copy_text=CopyTextButton(text=guarantee_address)
            )
        ],
        [
            InlineKeyboardButton(
                tr(user_id, "continue_button"),
                callback_data="continue_after_verify"
            )
        ],
        [
            InlineKeyboardButton(
                tr(user_id, "cancel_button"),
                callback_data="loan_cancel"
            )
        ]
    ])

    message = tr(
        user_id,
        "guarantee_address_title",
        network=network,
        address=guarantee_address,
        guarantee=guarantee,
    )

    await query.edit_message_text(
        message,
        reply_markup=keyboard
    )


async def loan_guarantee_sent_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id

    amount = context.user_data.get("loan_amount")
    network = context.user_data.get("loan_network")
    wallet = context.user_data.get("wallet_address")
    duration = context.user_data.get("loan_duration")

    if not amount or not network or not wallet or not duration:
        await query.edit_message_text(
            tr(user_id, "guarantee_sent_missing")
        )
        return

    context.user_data["awaiting_loan_txid"] = True

    guarantee = amount * 0.15

    txid_message = tr(
        user_id,
        "txid",
        amount=amount,
        guarantee=guarantee,
        network=network,
    )

    try:
        await query.edit_message_text(txid_message)
    except Exception as exc:
        if "Message is not modified" not in str(exc):
            raise


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
    context.user_data.pop("awaiting_network", None)
    context.user_data.pop("awaiting_loan_txid", None)
    context.user_data.pop("loan_flow_active", None)
    context.user_data.pop("loan_confirm_in_progress", None)

    await query.edit_message_text(
        tr(update.effective_user.id, "loan_cancelled")
    )
async def back_to_loan_conditions_callback(update, context):
    await loan_conditions_accept_callback(update, context)

