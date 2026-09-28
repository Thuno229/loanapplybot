from storage import DB_PATH
import sqlite3
from telegram.error import BadRequest

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import ContextTypes
from notifications import send_admin_notification
from notifications import send_notification_once
from i18n import tr


ADMIN_ID = 8266012108
DB = DB_PATH


def db():
    return sqlite3.connect(DB)


def is_admin(update):
    return update.effective_user and update.effective_user.id == ADMIN_ID


def back_button():
    return InlineKeyboardButton("↩️ Panneau admin", callback_data="admin_back")


def log_admin_action(admin_id, action, target_type=None, target_id=None, details=None):
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO admin_actions
        (admin_id, action, target_type, target_id, details)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            admin_id,
            action,
            target_type,
            target_id,
            details
        )
    )

    conn.commit()
    conn.close()


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Accès réservé à l'administrateur.")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Comptes", callback_data="admin_users")],
        [InlineKeyboardButton("🪪 KYC en attente", callback_data="admin_kyc")],
        [InlineKeyboardButton("💰 Demandes de prêt", callback_data="admin_loans")],
    ])

    await update.message.reply_text(
        "🔐 PANNEAU ADMINISTRATEUR\n\n"
        "Choisissez une section :",
        reply_markup=keyboard
    )


async def show_users(query):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, first_name, last_name, blocked
        FROM users
        ORDER BY id DESC
    """)
    users = cur.fetchall()
    conn.close()

    buttons = []

    for telegram_id, first_name, last_name, blocked in users:
        name = f"{first_name or ''} {last_name or ''}".strip()
        name = name or "Utilisateur"

        status = "🔒 Bloqué" if blocked else "🟢 Actif"

        buttons.append([
            InlineKeyboardButton(
                f"👤 {name} — {status}",
                callback_data=f"admin_user:{telegram_id}"
            )
        ])

    buttons.append([back_button()])

    await query.edit_message_text(
        f"👥 COMPTES ENREGISTRÉS : {len(users)}\n\n"
        "Sélectionnez un compte :",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_user(query, telegram_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            telegram_id,
            username,
            first_name,
            last_name,
            country,
            phone,
            email,
            profession,
            trc20_address,
            bep20_address,
            kyc_status,
            blocked,
            created_at
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,))

    user = cur.fetchone()
    conn.close()

    if not user:
        await query.edit_message_text(
            "❌ Compte introuvable.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )
        return

    (
        tg_id,
        username,
        first_name,
        last_name,
        country,
        phone,
        email,
        profession,
        trc20,
        bep20,
        kyc_status,
        blocked,
        created_at
    ) = user

    status = "🔒 BLOQUÉ" if blocked else "🟢 ACTIF"

    buttons = []

    if blocked:
        buttons.append([
            InlineKeyboardButton(
                "🟢 Débloquer",
                callback_data=f"admin_unblock:{tg_id}"
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                "🔒 Bloquer",
                callback_data=f"admin_block:{tg_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🗑️ Supprimer le compte",
            callback_data=f"admin_delete:{tg_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "💰 Voir ses demandes",
            callback_data=f"admin_userloans:{tg_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "🪪 Notifier : compléter KYC",
            callback_data=f"admin_notify_kyc:{tg_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "💰 Notifier : dossier de prêt",
            callback_data=f"admin_notify_loan:{tg_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "📋 Notifier : garantie / dossier",
            callback_data=f"admin_notify_guarantee:{tg_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "🧾 Notifier : TXID manquant",
            callback_data=f"admin_notify_txid:{tg_id}"
        )
    ])


    buttons.append([InlineKeyboardButton(
        "↩️ Comptes",
        callback_data="admin_users"
    )])

    await query.edit_message_text(
        "👤 PROFIL DU COMPTE\n\n"
        f"🆔 Telegram : {tg_id}\n"
        f"👤 Nom : {first_name or '-'} {last_name or '-'}\n"
        f"🔗 Username : @{username or '-'}\n"
        f"🌍 Pays : {country or '-'}\n"
        f"📞 Téléphone : {phone or '-'}\n"
        f"📧 Email : {email or '-'}\n"
        f"💼 Profession : {profession or '-'}\n\n"
        f"🪪 KYC : {kyc_status or 'not_submitted'}\n"
        f"🌐 TRC20 : {trc20 or '-'}\n"
        f"🌐 BEP20 : {bep20 or '-'}\n"
        f"📌 Statut : {status}\n"
        f"📅 Inscription : {created_at or '-'}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_kyc(query):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, first_name, last_name, country, email
        FROM users
        WHERE kyc_status = 'pending'
        ORDER BY id DESC
    """)

    users = cur.fetchall()
    conn.close()

    buttons = []

    for telegram_id, first_name, last_name, country, email in users:
        name = f"{first_name or ''} {last_name or ''}".strip()

        buttons.append([
            InlineKeyboardButton(
                f"🪪 {name or 'Utilisateur'}",
                callback_data=f"admin_kyc_user:{telegram_id}"
            )
        ])

    buttons.append([back_button()])

    await query.edit_message_text(
        f"🪪 KYC EN ATTENTE : {len(users)}\n\n"
        "Sélectionnez un dossier :",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_kyc_user(query, telegram_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            telegram_id,
            first_name,
            last_name,
            country,
            phone,
            email,
            profession,
            kyc_status,
            kyc_photo_file_id
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,))

    user = cur.fetchone()
    conn.close()

    if not user:
        await query.edit_message_text(
            "❌ Dossier KYC introuvable.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )
        return

    (
        tg_id,
        first_name,
        last_name,
        country,
        phone,
        email,
        profession,
        kyc_status,
        photo_id
    ) = user

    buttons = [
        [
            InlineKeyboardButton(
                "✅ Valider KYC",
                callback_data=f"admin_kyc_approve:{tg_id}"
            ),
            InlineKeyboardButton(
                "❌ Rejeter KYC",
                callback_data=f"admin_kyc_reject:{tg_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ KYC en attente",
                callback_data="admin_kyc"
            )
        ]
    ]

    await query.edit_message_text(
        "🪪 DOSSIER KYC\n\n"
        f"🆔 Telegram : {tg_id}\n"
        f"👤 Nom : {first_name or '-'} {last_name or '-'}\n"
        f"🌍 Pays : {country or '-'}\n"
        f"📞 Téléphone : {phone or '-'}\n"
        f"📧 Email : {email or '-'}\n"
        f"💼 Profession : {profession or '-'}\n"
        f"📌 Statut : {kyc_status or '-'}\n"
        f"📷 Document reçu : {'Oui' if photo_id else 'Non'}\n\n"
        "⚠️ La validation doit être effectuée manuellement.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_loans(query, telegram_id=None):
    conn = db()
    cur = conn.cursor()

    if telegram_id:
        cur.execute("""
            SELECT id, amount, network, status
            FROM loan_requests
            WHERE telegram_id = ?
            ORDER BY id DESC
        """, (telegram_id,))
    else:
        cur.execute("""
            SELECT id, amount, network, status
            FROM loan_requests
            ORDER BY id DESC
        """)

    loans = cur.fetchall()
    conn.close()

    buttons = []

    for request_id, amount, network, status in loans:
        buttons.append([
            InlineKeyboardButton(
                f"💰 #{request_id} — {amount:g} USDT — {status}",
                callback_data=f"admin_loan:{request_id}"
            )
        ])

    buttons.append([back_button()])

    title = "DEMANDES DU COMPTE" if telegram_id else "DEMANDES DE PRÊT"

    await query.edit_message_text(
        f"💰 {title} : {len(loans)}\n\n"
        "Sélectionnez une demande :",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_loan(query, request_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            l.id,
            l.telegram_id,
            l.amount,
            l.guarantee,
            l.network,
            l.repayment_period,
            l.status,
            l.guarantee_status,
            l.txid,
            l.wallet_address,
            l.created_at,
            u.first_name,
            u.last_name,
            u.country,
            u.phone,
            u.email,
            u.profession,
            u.kyc_status,
            ln.id,
            ln.status,
            ln.disbursement_status,
            ln.disbursement_network,
            ln.disbursement_amount,
            ln.disbursement_recipient,
            ln.disbursement_txid,
            ln.disbursement_date
        FROM loan_requests l
        LEFT JOIN users u
            ON u.telegram_id = l.telegram_id
        LEFT JOIN loans ln
            ON ln.loan_request_id = l.id
        WHERE l.id = ?
    """, (request_id,))

    loan = cur.fetchone()
    conn.close()

    if not loan:
        await query.edit_message_text(
            "❌ Demande introuvable.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )
        return

    (
        rid,
        telegram_id,
        amount,
        guarantee,
        network,
        repayment,
        status,
        guarantee_status,
        txid,
        wallet,
        created_at,
        first_name,
        last_name,
        country,
        phone,
        email,
        profession,
        kyc_status,
        loan_id,
        loan_status,
        disbursement_status,
        disbursement_network,
        disbursement_amount,
        disbursement_recipient,
        disbursement_txid,
        disbursement_date,
    ) = loan

    buttons = []

    if not loan_id:
        buttons.append([
            InlineKeyboardButton(
                "✅ Approuver",
                callback_data=f"admin_loan_approve:{rid}"
            ),
            InlineKeyboardButton(
                "❌ Rejeter",
                callback_data=f"admin_loan_reject:{rid}"
            )
        ])
    else:
        normalized_disbursement = str(
            disbursement_status or ""
        ).lower()

        if normalized_disbursement not in (
            "disbursed",
            "sent",
            "completed",
        ) and not disbursement_txid:
            buttons.append([
                InlineKeyboardButton(
                    "📤 Enregistrer le décaissement",
                    callback_data=f"admin_loan_disburse:{loan_id}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(
            "👤 Profil",
            callback_data=f"admin_user:{telegram_id}"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "↩️ Demandes",
            callback_data="admin_loans"
        )
    ])

    text = (
        f"💰 DEMANDE #{rid}\n\n"
        f"👤 {first_name or '-'} {last_name or '-'}\n"
        f"🆔 Telegram : {telegram_id}\n"
        f"🌍 Pays : {country or '-'}\n"
        f"📞 Téléphone : {phone or '-'}\n"
        f"📧 Email : {email or '-'}\n"
        f"💼 Profession : {profession or '-'}\n"
        f"🪪 KYC : {kyc_status or '-'}\n\n"
        f"💰 Montant : {amount:g} USDT\n"
        f"📊 Garantie indicative 15 % : {guarantee:g} USDT\n"
        f"🌐 Réseau : {network or '-'}\n"
        f"📍 Adresse : {wallet or '-'}\n"
        f"📅 Remboursement : {repayment or '-'}\n\n"
        f"💳 Statut garantie : {guarantee_status or '-'}\n"
        f"🧾 TXID déclaré : {txid or 'Non renseigné'}\n"
        f"📌 Statut demande : {status or '-'}\n"
        f"📅 Créée : {created_at or '-'}\n"
    )

    if loan_id:
        text += (
            "\n━━━━━━━━━━━━━━━━━━\n"
            f"💳 PRÊT #{loan_id}\n"
            f"📌 Statut du prêt : {loan_status or '-'}\n"
            f"📤 Décaissement : "
            f"{disbursement_status or 'awaiting'}\n"
        )

        if disbursement_network:
            text += (
                f"🌐 Réseau décaissement : "
                f"{disbursement_network}\n"
            )

        if disbursement_amount is not None:
            text += (
                f"💸 Montant enregistré : "
                f"{disbursement_amount:g} USDT\n"
            )

        if disbursement_recipient:
            text += (
                f"📍 Destinataire : "
                f"{disbursement_recipient}\n"
            )

        if disbursement_txid:
            text += (
                f"🧾 TXID décaissement : "
                f"{disbursement_txid}\n"
            )

        if disbursement_date:
            text += (
                f"🕐 Date : "
                f"{disbursement_date}\n"
            )

    text += (
        "\n⚠️ Le TXID affiché est celui enregistré dans la base. "
        "Toute vérification de paiement doit être effectuée "
        "manuellement."
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if not is_admin(update):
        await query.edit_message_text("❌ Accès réservé à l'administrateur.")
        return

    data = query.data

    try:
        if data == "admin_back":
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👥 Comptes", callback_data="admin_users")],
                [InlineKeyboardButton("🪪 KYC en attente", callback_data="admin_kyc")],
                [InlineKeyboardButton("💰 Demandes de prêt", callback_data="admin_loans")],
            ])

            await query.edit_message_text(
                "🔐 PANNEAU ADMINISTRATEUR\n\n"
                "Choisissez une section :",
                reply_markup=keyboard
            )
            return

        if data == "admin_users":
            await show_users(query)
            return

        if data.startswith("admin_user:"):
            telegram_id = int(data.split(":", 1)[1])
            await show_user(query, telegram_id)
            return

        if data.startswith("admin_block:"):
            telegram_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE users SET blocked = 1 WHERE telegram_id = ?",
                (telegram_id,)
            )
            conn.commit()
            conn.close()

            await show_user(query, telegram_id)
            return

        if data.startswith("admin_unblock:"):
            telegram_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE users SET blocked = 0 WHERE telegram_id = ?",
                (telegram_id,)
            )
            conn.commit()
            conn.close()

            await show_user(query, telegram_id)
            return

        if data.startswith("admin_delete:"):
            telegram_id = int(data.split(":", 1)[1])

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "⚠️ CONFIRMER SUPPRESSION",
                        callback_data=f"admin_confirm_delete:{telegram_id}"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "↩️ Annuler",
                        callback_data=f"admin_user:{telegram_id}"
                    )
                ]
            ])

            await query.edit_message_text(
                "⚠️ SUPPRESSION DU COMPTE\n\n"
                "Cette action supprimera le compte utilisateur.\n"
                "Confirmez-vous ?",
                reply_markup=keyboard
            )
            return

        if data.startswith("admin_confirm_delete:"):
            telegram_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "DELETE FROM users WHERE telegram_id = ?",
                (telegram_id,)
            )
            conn.commit()
            conn.close()

            await show_users(query)
            return

        # =================================================
        # NOTIFICATIONS ADMIN → CLIENT
        # =================================================

        if data.startswith("admin_notify_kyc:"):
            telegram_id = int(data.split(":", 1)[1])

            try:
                sent = await send_admin_notification(
                    context.bot,
                    telegram_id,
                    "kyc",
                )

                if sent:
                    await query.answer(
                        "✅ Notification KYC envoyée au client.",
                        show_alert=True
                    )
                else:
                    await query.answer(
                        "ℹ️ Notification non envoyée.",
                        show_alert=True
                    )

            except Exception as e:
                print(f"❌ Notification KYC impossible : {e}")
                await query.answer(
                    "❌ Erreur lors de l'envoi.",
                    show_alert=True
                )

            await show_user(query, telegram_id)
            return

        if data.startswith("admin_notify_loan:"):
            telegram_id = int(data.split(":", 1)[1])

            try:
                sent = await send_admin_notification(
                    context.bot,
                    telegram_id,
                    "loan",
                )

                if sent:
                    await query.answer(
                        "✅ Notification prêt envoyée au client.",
                        show_alert=True
                    )
                else:
                    await query.answer(
                        "ℹ️ Notification non envoyée.",
                        show_alert=True
                    )

            except Exception as e:
                print(f"❌ Notification prêt impossible : {e}")
                await query.answer(
                    "❌ Erreur lors de l'envoi.",
                    show_alert=True
                )

            await show_user(query, telegram_id)
            return

        if data.startswith("admin_notify_guarantee:"):
            telegram_id = int(data.split(":", 1)[1])

            try:
                sent = await send_admin_notification(
                    context.bot,
                    telegram_id,
                    "guarantee",
                )

                if sent:
                    await query.answer(
                        "✅ Notification garantie envoyée au client.",
                        show_alert=True
                    )
                else:
                    await query.answer(
                        "ℹ️ Notification non envoyée.",
                        show_alert=True
                    )

            except Exception as e:
                print(f"❌ Notification garantie impossible : {e}")
                await query.answer(
                    "❌ Erreur lors de l'envoi.",
                    show_alert=True
                )

            await show_user(query, telegram_id)
            return

        if data.startswith("admin_notify_txid:"):
            telegram_id = int(data.split(":", 1)[1])

            try:
                sent = await send_admin_notification(
                    context.bot,
                    telegram_id,
                    "txid",
                )

                if sent:
                    await query.answer(
                        "✅ Notification TXID envoyée au client.",
                        show_alert=True
                    )
                else:
                    await query.answer(
                        "ℹ️ Notification non envoyée.",
                        show_alert=True
                    )

            except Exception as e:
                print(f"❌ Notification TXID impossible : {e}")
                await query.answer(
                    "❌ Erreur lors de l'envoi.",
                    show_alert=True
                )

            await show_user(query, telegram_id)
            return


        if data.startswith("admin_userloans:"):
            telegram_id = int(data.split(":", 1)[1])
            await show_loans(query, telegram_id)
            return

        if data == "admin_kyc":
            await show_kyc(query)
            return

        if data.startswith("admin_kyc_user:"):
            telegram_id = int(data.split(":", 1)[1])
            await show_kyc_user(query, telegram_id)
            return

        if data.startswith("admin_kyc_approve:"):
            telegram_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE users SET kyc_status = 'approved' WHERE telegram_id = ?",
                (telegram_id,)
            )
            conn.commit()
            conn.close()

            try:
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=tr(telegram_id, "kyc_approved")
                )
            except Exception:
                pass

            await show_kyc(query)
            return

        if data.startswith("admin_kyc_reject:"):
            telegram_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE users SET kyc_status = 'rejected' WHERE telegram_id = ?",
                (telegram_id,)
            )
            conn.commit()
            conn.close()

            try:
                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=tr(telegram_id, "kyc_rejected")
                )
            except Exception:
                pass

            await show_kyc(query)
            return

        if data == "admin_loans":
            await show_loans(query)
            return

        if data.startswith("admin_loan:"):
            request_id = int(data.split(":", 1)[1])
            await show_loan(query, request_id)
            return


        # ============================================================
        # DÉCAISSEMENT MANUEL
        # ============================================================

        if data.startswith("admin_loan_disburse:"):
            loan_id = int(data.split(":", 1)[1])
            await admin_disbursement_start(query, context, loan_id)
            return

        if data.startswith("admin_disbursement_network:"):
            await query.answer(
                "ℹ️ Le réseau et l'adresse sont définis automatiquement depuis la demande.",
                show_alert=True
            )
            return

            if network not in ("TRC20", "BEP20"):
                await query.answer(
                    "❌ Réseau invalide.",
                    show_alert=True
                )
                return

            state = context.user_data.get("admin_disbursement")

            if not state:
                await query.answer(
                    "❌ Aucune opération de décaissement en cours.",
                    show_alert=True
                )
                return

            state["network"] = network
            state["step"] = "recipient"

            await query.edit_message_text(
                "📤 DÉCAISSEMENT — ADRESSE DESTINATAIRE\n\n"
                f"🌐 Réseau : {network}\n\n"
                "✏️ Envoyez maintenant l'adresse du portefeuille "
                "destinataire.\n\n"
                "⚠️ Vérifiez attentivement l'adresse avant "
                "de l'enregistrer.",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "❌ Annuler",
                            callback_data="admin_disbursement_cancel"
                        )
                    ]
                ])
            )
            return

        if data == "admin_disbursement_confirm":
            state = context.user_data.get("admin_disbursement")

            if not state:
                await query.answer(
                    "❌ Aucune opération en cours.",
                    show_alert=True
                )
                return

            required = (
                "loan_id",
                "request_id",
                "telegram_id",
                "amount",
                "network",
                "recipient",
                "txid",
            )

            if any(state.get(key) in (None, "") for key in required):
                await query.answer(
                    "❌ Informations de décaissement incomplètes.",
                    show_alert=True
                )
                return

            conn = db()
            cur = conn.cursor()

            cur.execute(
                """
                SELECT
                    id,
                    loan_request_id,
                    telegram_id,
                    amount,
                    disbursement_status,
                    disbursement_txid
                FROM loans
                WHERE id = ?
                """,
                (state["loan_id"],)
            )

            loan = cur.fetchone()

            if not loan:
                conn.close()
                context.user_data.pop("admin_disbursement", None)
                await query.answer(
                    "❌ Prêt introuvable.",
                    show_alert=True
                )
                return

            (
                loan_id,
                request_id,
                telegram_id,
                approved_amount,
                current_status,
                current_txid,
            ) = loan

            if current_txid or str(current_status).lower() in (
                "disbursed",
                "sent",
                "completed",
            ):
                conn.close()
                context.user_data.pop("admin_disbursement", None)
                await query.answer(
                    "⚠️ Ce décaissement est déjà enregistré.",
                    show_alert=True
                )
                return

            cur.execute(
                """
                UPDATE loans
                SET
                    disbursement_status = 'disbursed',
                    disbursement_network = ?,
                    disbursement_amount = ?,
                    disbursement_recipient = ?,
                    disbursement_txid = ?,
                    disbursement_date = CURRENT_TIMESTAMP,
                    status = 'active'
                WHERE id = ?
                """,
                (
                    state["network"],
                    state["amount"],
                    state["recipient"],
                    state["txid"],
                    loan_id,
                )
            )

            conn.commit()
            conn.close()

            log_admin_action(
                ADMIN_ID,
                "record_disbursement",
                "loan",
                loan_id,
                (
                    f"request_id={request_id}; "
                    f"amount={state['amount']}; "
                    f"network={state['network']}; "
                    f"recipient={state['recipient']}; "
                    f"txid={state['txid']}"
                )
            )

            try:
                await send_notification_once(
                    bot=context.bot,
                    telegram_id=telegram_id,
                    notification_type="disbursement_recorded",
                    reference_id=str(loan_id),
                    text=(
                        "📤 DÉCAISSEMENT ENREGISTRÉ\n\n"
                        f"🆔 Prêt : #{loan_id}\n"
                        f"💰 Montant enregistré : "
                        f"{state['amount']:g} USDT\n"
                        f"🌐 Réseau : {state['network']}\n"
                        f"📍 Adresse destinataire : "
                        f"{state['recipient']}\n"
                        f"🧾 TXID / Hash : {state['txid']}\n\n"
                        "📌 Le prêt est maintenant enregistré "
                        "comme décaissé dans le système.\n\n"
                        "⚠️ Le bot n'effectue aucun transfert "
                        "crypto et ne vérifie pas automatiquement "
                        "la blockchain. Les informations ci-dessus "
                        "correspondent à l'enregistrement administratif."
                    ),
                )
            except Exception as e:
                print(
                    f"⚠️ Notification de décaissement impossible : {e}"
                )

            request_id = state["request_id"]
            context.user_data.pop("admin_disbursement", None)

            await show_loan(query, request_id)
            return

        if data == "admin_disbursement_cancel":
            state = context.user_data.pop(
                "admin_disbursement",
                None
            )

            if state and state.get("request_id"):
                await show_loan(
                    query,
                    state["request_id"]
                )
            else:
                await show_loans(query)

            return

        if data.startswith("admin_loan_approve:"):
            request_id = int(data.split(":", 1)[1])

            from datetime import date
            import re

            conn = db()
            cur = conn.cursor()

            try:
                cur.execute(
                    """
                    SELECT telegram_id, amount, repayment_period
                    FROM loan_requests
                    WHERE id = ?
                    """,
                    (request_id,)
                )
                request = cur.fetchone()

                if not request:
                    await query.answer(
                        "❌ Demande introuvable.",
                        show_alert=True
                    )
                    conn.close()
                    return

                telegram_id, amount, repayment_period = request

                match = re.search(r"(\d+)", repayment_period or "")
                if not match:
                    await query.answer(
                        "❌ Durée du prêt introuvable.",
                        show_alert=True
                    )
                    conn.close()
                    return

                duration_months = int(match.group(1))

                if duration_months <= 0 or duration_months > 120:
                    await query.answer(
                        "❌ Durée du prêt invalide.",
                        show_alert=True
                    )
                    conn.close()
                    return

                # Le bot utilise actuellement 1 % d'intérêt par mois.
                interest_rate = 1.0
                interest = amount * interest_rate / 100 * duration_months
                total_repayment = amount + interest
                monthly_payment = total_repayment / duration_months

                # Vérifier si le prêt existe déjà pour éviter les doublons.
                cur.execute(
                    """
                    SELECT id
                    FROM loans
                    WHERE loan_request_id = ?
                    """,
                    (request_id,)
                )
                existing_loan = cur.fetchone()

                if existing_loan:
                    loan_id = existing_loan[0]
                else:
                    cur.execute(
                        """
                        INSERT INTO loans (
                            loan_request_id,
                            telegram_id,
                            amount,
                            interest_rate,
                            total_repayment,
                            monthly_payment,
                            duration_months,
                            status,
                            disbursement_status
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            request_id,
                            telegram_id,
                            amount,
                            interest_rate,
                            total_repayment,
                            monthly_payment,
                            duration_months,
                            "approved",
                            "awaiting"
                        )
                    )

                    loan_id = cur.lastrowid

                    # Première échéance : un mois après l'approbation.
                    def add_months(d, months):
                        month = d.month - 1 + months
                        year = d.year + month // 12
                        month = month % 12 + 1

                        import calendar
                        day = min(
                            d.day,
                            calendar.monthrange(year, month)[1]
                        )

                        return d.replace(
                            year=year,
                            month=month,
                            day=day
                        )

                    approval_date = date.today()

                    for installment_number in range(
                        1,
                        duration_months + 1
                    ):
                        due_date = add_months(
                            approval_date,
                            installment_number
                        )

                        if installment_number == duration_months:
                            installment_amount = round(
                                total_repayment
                                - round(monthly_payment, 2)
                                * (duration_months - 1),
                                2
                            )
                        else:
                            installment_amount = round(
                                monthly_payment,
                                2
                            )

                        cur.execute(
                            """
                            INSERT INTO loan_installments (
                                loan_id,
                                installment_number,
                                due_date,
                                amount,
                                status
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                loan_id,
                                installment_number,
                                due_date.isoformat(),
                                installment_amount,
                                "pending"
                            )
                        )

                    first_due_date = add_months(
                        approval_date,
                        1
                    ).isoformat()

                    cur.execute(
                        """
                        UPDATE loans
                        SET next_due_date = ?
                        WHERE id = ?
                        """,
                        (first_due_date, loan_id)
                    )

                cur.execute(
                    """
                    UPDATE loan_requests
                    SET status = 'approved'
                    WHERE id = ?
                    """,
                    (request_id,)
                )

                conn.commit()

                log_admin_action(
                    ADMIN_ID,
                    "approve_loan",
                    "loan_request",
                    request_id,
                    f"loan_id={loan_id}; amount={amount}; "
                    f"duration={duration_months}; "
                    f"interest_rate={interest_rate}"
                )

            except Exception:
                conn.rollback()
                conn.close()
                raise

            conn.close()

            try:
                await send_notification_once(
                    bot=context.bot,
                    telegram_id=telegram_id,
                    notification_type="loan_approved",
                    reference_id=str(request_id),
                    text=(
                        tr(
                            telegram_id, "loan_approved", request_id=request_id,
                            amount=amount, interest_rate=interest_rate,
                            total_repayment=total_repayment,
                            monthly_payment=monthly_payment, duration_months=duration_months,
                        )
                    ),
                    reply_markup=ReplyKeyboardMarkup(
                        [["💳 Mon prêt en cours"]],
                        resize_keyboard=True,
                    ),
                )
            except Exception as e:
                print(
                    f"⚠️ Notification client impossible : {e}"
                )


            await show_loan(query, request_id)
            return

        if data.startswith("admin_loan_reject:"):
            request_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE loan_requests SET status = 'rejected' WHERE id = ?",
                (request_id,)
            )
            conn.commit()

            cur = conn.cursor()
            cur.execute(
                "SELECT telegram_id FROM loan_requests WHERE id = ?",
                (request_id,)
            )
            row = cur.fetchone()
            conn.close()

            if row:
                try:
                    await send_notification_once(
                        bot=context.bot,
                        telegram_id=row[0],
                        notification_type="loan_rejected",
                        reference_id=str(request_id),
                        text=(
                            tr(row[0], "loan_rejected", request_id=request_id)
                        ),
                    )
                except Exception as e:
                    print(f"⚠️ Notification de refus impossible : {e}")

            await show_loan(query, request_id)
            return

        await query.edit_message_text(
            "❌ Action admin inconnue.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )

    except BadRequest as e:
        if "Message is not modified" in str(e):
            return

        print(f"❌ Erreur admin_callback : {e}")

        try:
            await query.edit_message_text(
                "❌ Une erreur est survenue.",
                reply_markup=InlineKeyboardMarkup([[back_button()]])
            )
        except Exception:
            pass

    except Exception as e:
        print(f"❌ Erreur admin_callback : {e}")

        try:
            await query.edit_message_text(
                "❌ Une erreur est survenue.",
                reply_markup=InlineKeyboardMarkup([[back_button()]])
            )
        except Exception:
            pass

async def admin_disbursement_start(query, context, loan_id):
    """Démarre l’enregistrement manuel d’un décaissement."""

    conn = db()
    cur = conn.cursor()

    cur.execute(
        "SELECT ln.id, ln.loan_request_id, ln.telegram_id, "
        "ln.amount, ln.status, ln.disbursement_status, "
        "ln.disbursement_txid, lr.network, lr.wallet_address "
        "FROM loans ln "
        "LEFT JOIN loan_requests lr ON lr.id = ln.loan_request_id "
        "WHERE ln.id = ?",
        (loan_id,)
    )

    loan = cur.fetchone()
    conn.close()

    if not loan:
        await query.edit_message_text(
            "❌ Prêt introuvable.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )
        return

    (
        loan_id,
        request_id,
        telegram_id,
        approved_amount,
        loan_status,
        disbursement_status,
        existing_txid,
        network,
        recipient,
    ) = loan

    network = str(network or "").strip().upper()
    recipient = str(recipient or "").strip()

    if network not in ("TRC20", "BEP20"):
        await query.edit_message_text(
            "❌ Impossible d’enregistrer le décaissement.\n\n"
            f"🆔 Demande : #{request_id}\n"
            "🌐 Le réseau de la demande est absent ou invalide.\n\n"
            "Veuillez vérifier la demande avant de continuer.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )
        return

    if not recipient:
        await query.edit_message_text(
            "❌ Impossible d’enregistrer le décaissement.\n\n"
            f"🆔 Demande : #{request_id}\n"
            f"🌐 Réseau : {network}\n"
            "📍 Aucune adresse de portefeuille n’est enregistrée "
            "pour cette demande.\n\n"
            "Le bot ne va pas inventer ou remplacer l’adresse.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )
        return

    if str(loan_status).lower() in ("rejected", "cancelled"):
        await query.answer(
            "❌ Ce prêt est rejeté ou annulé.",
            show_alert=True
        )
        return

    if existing_txid or str(disbursement_status).lower() in (
        "disbursed",
        "sent",
        "completed",
    ):
        await query.answer(
            "⚠️ Ce décaissement est déjà enregistré.",
            show_alert=True
        )
        return

    context.user_data["admin_disbursement"] = {
        "loan_id": loan_id,
        "request_id": request_id,
        "telegram_id": telegram_id,
        "approved_amount": float(approved_amount),
        "network": network,
        "recipient": recipient,
        "step": "amount",
    }

    await query.edit_message_text(
        "📤 ENREGISTREMENT DU DÉCAISSEMENT\n\n"
        f"🆔 Prêt : #{loan_id}\n"
        f"🆔 Demande : #{request_id}\n"
        f"💰 Montant approuvé : {approved_amount:g} USDT\n\n"
        f"🌐 Réseau automatique : {network}\n"
        f"📍 Adresse automatique :\n{recipient}\n\n"
        "✏️ Saisissez uniquement le montant réellement enregistré.\n\n"
        "⚠️ Le réseau et l’adresse proviennent de la demande de prêt.\n"
        "⚠️ Le bot n’effectue aucun transfert crypto.",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "❌ Annuler",
                    callback_data="admin_disbursement_cancel"
                )
            ]
        ])
    )


async def admin_disbursement_message(update, context):
    """Gère la saisie texte du décaissement par l'administrateur."""

    if not is_admin(update):
        return

    state = context.user_data.get("admin_disbursement")

    if not state:
        return

    message = update.message

    if not message or not message.text:
        return

    value = message.text.strip()
    step = state.get("step")

    # ==================================================
    # 1. MONTANT
    # ==================================================

    if step == "amount":
        raw = value.replace(",", ".")

        try:
            amount = float(raw)
        except ValueError:
            await message.reply_text(
                "❌ Montant invalide.\n\n"
                "Exemple : 500 ou 500.00"
            )
            return

        if amount <= 0:
            await message.reply_text(
                "❌ Le montant doit être supérieur à 0."
            )
            return

        approved_amount = float(
            state.get("approved_amount", 0)
        )

        if approved_amount > 0 and amount > approved_amount:
            await message.reply_text(
                f"❌ Le montant saisi ({amount:g} USDT) "
                f"dépasse le montant approuvé "
                f"({approved_amount:g} USDT).\n\n"
                "Veuillez saisir un montant valide."
            )
            return

        network = str(state.get("network") or "").strip().upper()
        recipient = str(state.get("recipient") or "").strip()

        if network not in ("TRC20", "BEP20"):
            await message.reply_text(
                "❌ Le réseau enregistré est invalide.\n\n"
                "Le décaissement ne peut pas continuer."
            )
            return

        if not recipient:
            await message.reply_text(
                "❌ Aucune adresse destinataire enregistrée.\n\n"
                "Le décaissement ne peut pas continuer."
            )
            return

        state["amount"] = amount
        state["step"] = "txid"

        await message.reply_text(
            "📤 DÉCAISSEMENT — DESTINATAIRE AUTOMATIQUE\n\n"
            f"💰 Montant : {amount:g} USDT\n"
            f"🌐 Réseau : {network}\n"
            f"📍 Adresse destinataire :\n{recipient}\n\n"
            "ℹ️ Le réseau et l’adresse proviennent automatiquement "
            "de la demande de prêt.\n\n"
            "🧾 Envoyez maintenant le TXID / hash de "
            "l’opération effectuée séparément.\n\n"
            "⚠️ Vérifiez attentivement le réseau, l’adresse et "
            "le TXID avant de confirmer.\n"
            "⚠️ Le bot n’effectue aucun transfert crypto et "
            "ne vérifie pas automatiquement la blockchain.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "❌ Annuler",
                        callback_data="admin_disbursement_cancel"
                    )
                ]
            ])
        )
        return

    # ============================================================
    # 2. ADRESSE DESTINATAIRE
    # ============================================================

    # ==================================================

    if step == "recipient":
        if len(value) < 10:
            await message.reply_text(
                "❌ Adresse trop courte ou invalide.\n\n"
                "Veuillez envoyer l'adresse complète du "
                "portefeuille destinataire."
            )
            return

        state["recipient"] = value
        state["step"] = "txid"

        await message.reply_text(
            "🧾 DÉCAISSEMENT — TXID / HASH\n\n"
            f"📍 Adresse enregistrée :\n{value}\n\n"
            "Envoyez maintenant le TXID / hash de "
            "l'opération effectuée séparément.\n\n"
            "⚠️ Le bot ne vérifie pas automatiquement "
            "la blockchain."
        )
        return

    # ==================================================
    # 3. TXID
    # ==================================================

    if step == "txid":
        if len(value) < 6:
            await message.reply_text(
                "❌ TXID / hash trop court.\n\n"
                "Veuillez envoyer le TXID complet."
            )
            return

        state["txid"] = value
        state["step"] = "confirm"

        await message.reply_text(
            "📋 VÉRIFICATION DU DÉCAISSEMENT\n\n"
            f"🆔 Prêt : #{state.get('loan_id')}\n"
            f"🆔 Demande : #{state.get('request_id')}\n"
            f"💰 Montant : {state.get('amount'):g} USDT\n"
            f"🌐 Réseau : {state.get('network')}\n"
            f"📍 Destinataire : {state.get('recipient')}\n"
            f"🧾 TXID / Hash : {state.get('txid')}\n\n"
            "Confirmez uniquement si ces informations "
            "correspondent à l'opération que vous avez "
            "effectuée séparément.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "✅ Confirmer l'enregistrement",
                        callback_data="admin_disbursement_confirm"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "❌ Annuler",
                        callback_data="admin_disbursement_cancel"
                    )
                ]
            ])
        )
        return

    # ==================================================
    # ÉTAT INCONNU
    # ==================================================

    await message.reply_text(
        "❌ État du décaissement inconnu.\n"
        "Veuillez annuler puis recommencer."
    )

