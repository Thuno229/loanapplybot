import sqlite3

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes


ADMIN_ID = 8266012108
DB = "loan_bot.db"


def db():
    return sqlite3.connect(DB)


def is_admin(update):
    return update.effective_user and update.effective_user.id == ADMIN_ID


def back_button():
    return InlineKeyboardButton("↩️ Panneau admin", callback_data="admin_back")


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
            u.kyc_status
        FROM loan_requests l
        LEFT JOIN users u ON u.telegram_id = l.telegram_id
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
        kyc_status
    ) = loan

    buttons = [
        [
            InlineKeyboardButton(
                "✅ Approuver",
                callback_data=f"admin_loan_approve:{rid}"
            ),
            InlineKeyboardButton(
                "❌ Rejeter",
                callback_data=f"admin_loan_reject:{rid}"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 Profil",
                callback_data=f"admin_user:{telegram_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "↩️ Demandes",
                callback_data="admin_loans"
            )
        ]
    ]

    await query.edit_message_text(
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
        f"📅 Créée : {created_at or '-'}\n\n"
        "⚠️ Le TXID affiché est celui enregistré dans la base. "
        "Toute vérification de paiement doit être effectuée manuellement.",
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
                    text="✅ Votre vérification KYC a été validée."
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
                    text="❌ Votre vérification KYC a été rejetée. "
                         "Veuillez soumettre un document lisible."
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

        if data.startswith("admin_loan_approve:"):
            request_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE loan_requests SET status = 'approved' WHERE id = ?",
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
                    await context.bot.send_message(
                        chat_id=row[0],
                        text=f"✅ Votre demande de prêt #{request_id} "
                             "a été approuvée par l'administrateur."
                    )
                except Exception:
                    pass

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
                    await context.bot.send_message(
                        chat_id=row[0],
                        text=f"❌ Votre demande de prêt #{request_id} "
                             "a été rejetée."
                    )
                except Exception:
                    pass

            await show_loan(query, request_id)
            return

        await query.edit_message_text(
            "❌ Action admin inconnue.",
            reply_markup=InlineKeyboardMarkup([[back_button()]])
        )

    except Exception as e:
        print(f"❌ Erreur admin_callback : {e}")

        try:
            await query.edit_message_text(
                "❌ Une erreur est survenue.",
                reply_markup=InlineKeyboardMarkup([[back_button()]])
            )
        except Exception:
            pass
