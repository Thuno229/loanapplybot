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


def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Comptes", callback_data="admin_users")],
        [InlineKeyboardButton("🪪 KYC en attente", callback_data="admin_kyc")],
        [InlineKeyboardButton("💰 Demandes de prêt", callback_data="admin_loans")],
    ])


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Accès réservé à l'administrateur.")
        return

    await update.message.reply_text(
        "🔐 PANNEAU ADMINISTRATEUR\n\n"
        "Choisissez une section :",
        reply_markup=admin_menu(),
    )


async def show_users(query):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, first_name, last_name, country, kyc_status, blocked
        FROM users
        ORDER BY id DESC
    """)

    users = cur.fetchall()
    conn.close()

    if not users:
        await query.edit_message_text(
            "👥 COMPTES\n\nAucun compte enregistré.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Retour", callback_data="admin_back")]
            ]),
        )
        return

    buttons = []

    for telegram_id, first_name, last_name, country, kyc_status, blocked in users:
        name = f"{first_name or ''} {last_name or ''}".strip()
        name = name or "Sans nom"

        status = "🔒 Bloqué" if blocked else "🟢 Actif"

        buttons.append([
            InlineKeyboardButton(
                f"👤 {name} — {status}",
                callback_data=f"admin_user:{telegram_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton("↩️ Retour", callback_data="admin_back")
    ])

    await query.edit_message_text(
        f"👥 COMPTES ENREGISTRÉS : {len(users)}\n\n"
        "Sélectionnez un compte :",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def show_user(query, telegram_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, username, first_name, last_name,
               country, phone, email, profession,
               trc20_address, bep20_address,
               kyc_status, blocked, created_at
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,))

    user = cur.fetchone()
    conn.close()

    if not user:
        await query.edit_message_text(
            "❌ Compte introuvable.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Retour", callback_data="admin_users")]
            ]),
        )
        return

    (
        tg_id, username, first_name, last_name,
        country, phone, email, profession,
        trc20, bep20, kyc_status, blocked, created_at
    ) = user

    name = f"{first_name or ''} {last_name or ''}".strip() or "Sans nom"
    status = "🔒 BLOQUÉ" if blocked else "🟢 ACTIF"

    buttons = []

    if blocked:
        buttons.append([
            InlineKeyboardButton(
                "🟢 Débloquer",
                callback_data=f"admin_unblock:{tg_id}",
            )
        ])
    else:
        buttons.append([
            InlineKeyboardButton(
                "🔒 Bloquer",
                callback_data=f"admin_block:{tg_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🗑️ Supprimer",
            callback_data=f"admin_delete:{tg_id}",
        )
    ])

    buttons.append([
        InlineKeyboardButton("↩️ Retour", callback_data="admin_users")
    ])

    text = (
        "👤 DÉTAIL DU COMPTE\n\n"
        f"🆔 Telegram : {tg_id}\n"
        f"👤 Nom : {name}\n"
        f"🔗 Username : @{username or 'aucun'}\n"
        f"🌍 Pays : {country or '—'}\n"
        f"📞 Téléphone : {phone or '—'}\n"
        f"📧 Email : {email or '—'}\n"
        f"💼 Profession : {profession or '—'}\n\n"
        f"🪪 KYC : {kyc_status or 'not_submitted'}\n"
        f"📍 TRC20 : {trc20 or '—'}\n"
        f"📍 BEP20 : {bep20 or '—'}\n"
        f"📌 État : {status}\n"
        f"📅 Inscription : {created_at or '—'}"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def show_kyc(query):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT telegram_id, first_name, last_name, country
        FROM users
        WHERE kyc_status = 'pending'
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await query.edit_message_text(
            "🪪 KYC EN ATTENTE\n\n"
            "Aucune vérification KYC en attente.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Retour", callback_data="admin_back")]
            ]),
        )
        return

    buttons = []

    for tg_id, first_name, last_name, country in rows:
        name = f"{first_name or ''} {last_name or ''}".strip() or "Sans nom"

        buttons.append([
            InlineKeyboardButton(
                f"🪪 {name} — {country or '—'}",
                callback_data=f"admin_user:{tg_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton("↩️ Retour", callback_data="admin_back")
    ])

    await query.edit_message_text(
        f"🪪 KYC EN ATTENTE : {len(rows)}\n\n"
        "Sélectionnez un compte pour consulter ses informations.",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def show_loans(query):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, telegram_id, amount, network, status, created_at
        FROM loan_requests
        ORDER BY id DESC
    """)

    rows = cur.fetchall()
    conn.close()

    if not rows:
        await query.edit_message_text(
            "💰 DEMANDES DE PRÊT\n\n"
            "Aucune demande enregistrée.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Retour", callback_data="admin_back")]
            ]),
        )
        return

    buttons = []

    for request_id, tg_id, amount, network, status, created_at in rows:
        buttons.append([
            InlineKeyboardButton(
                f"💰 #{request_id} — {amount:g} USDT — {status}",
                callback_data=f"admin_loan:{request_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton("↩️ Retour", callback_data="admin_back")
    ])

    await query.edit_message_text(
        f"💰 DEMANDES DE PRÊT : {len(rows)}\n\n"
        "Sélectionnez une demande :",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def show_loan(query, request_id):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, telegram_id, amount, guarantee, network,
               repayment_period, status, guarantee_status,
               txid, wallet_address, created_at
        FROM loan_requests
        WHERE id = ?
    """, (request_id,))

    row = cur.fetchone()
    conn.close()

    if not row:
        await query.edit_message_text(
            "❌ Demande introuvable.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("↩️ Retour", callback_data="admin_loans")]
            ]),
        )
        return

    (
        rid, tg_id, amount, guarantee, network,
        repayment, status, guarantee_status,
        txid, wallet, created_at
    ) = row

    buttons = []

    if status == "pending":
        buttons.append([
            InlineKeyboardButton(
                "✅ Valider manuellement",
                callback_data=f"admin_loan_approve:{rid}",
            ),
            InlineKeyboardButton(
                "❌ Rejeter",
                callback_data=f"admin_loan_reject:{rid}",
            ),
        ])

    buttons.append([
        InlineKeyboardButton("↩️ Retour", callback_data="admin_loans")
    ])

    text = (
        f"💰 DEMANDE DE PRÊT #{rid}\n\n"
        f"🆔 Telegram : {tg_id}\n"
        f"💵 Montant : {amount:g} USDT\n"
        f"📊 Garantie indicative : {guarantee:g} USDT\n"
        f"🌐 Réseau : {network}\n"
        f"📅 Remboursement : {repayment or '—'}\n"
        f"📌 Statut : {status}\n"
        f"💳 Garantie : {guarantee_status or '—'}\n"
        f"📍 Wallet : {wallet or '—'}\n"
        f"🔗 TXID : {txid or '—'}\n"
        f"🕐 Créée : {created_at or '—'}"
    )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Accès refusé.", show_alert=True)
        return

    await query.answer()

    try:
        data = query.data or ""

        if data == "admin_users":
            await show_users(query)
            return

        if data == "admin_kyc":
            await show_kyc(query)
            return

        if data == "admin_loans":
            await show_loans(query)
            return

        if data == "admin_back":
            await query.edit_message_text(
                "🔐 PANNEAU ADMINISTRATEUR\n\n"
                "Choisissez une section :",
                reply_markup=admin_menu(),
            )
            return

        if data.startswith("admin_user:"):
            tg_id = int(data.split(":", 1)[1])
            await show_user(query, tg_id)
            return

        if data.startswith("admin_block:"):
            tg_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE users SET blocked = 1 WHERE telegram_id = ?",
                (tg_id,),
            )
            conn.commit()
            conn.close()

            await query.edit_message_text(
                "🔒 Compte bloqué avec succès.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "↩️ Retour au compte",
                        callback_data=f"admin_user:{tg_id}"
                    )],
                    [InlineKeyboardButton(
                        "👥 Tous les comptes",
                        callback_data="admin_users"
                    )],
                ]),
            )
            return

        if data.startswith("admin_unblock:"):
            tg_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE users SET blocked = 0 WHERE telegram_id = ?",
                (tg_id,),
            )
            conn.commit()
            conn.close()

            await query.edit_message_text(
                "🟢 Compte débloqué avec succès.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "↩️ Retour au compte",
                        callback_data=f"admin_user:{tg_id}"
                    )],
                    [InlineKeyboardButton(
                        "👥 Tous les comptes",
                        callback_data="admin_users"
                    )],
                ]),
            )
            return

        if data.startswith("admin_delete:"):
            tg_id = int(data.split(":", 1)[1])

            await query.edit_message_text(
                "⚠️ SUPPRESSION DU COMPTE\n\n"
                "Cette action supprimera le compte utilisateur.\n"
                "Voulez-vous vraiment continuer ?",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "⚠️ Oui, supprimer",
                        callback_data=f"admin_confirm_delete:{tg_id}"
                    )],
                    [InlineKeyboardButton(
                        "↩️ Annuler",
                        callback_data=f"admin_user:{tg_id}"
                    )],
                ]),
            )
            return

        if data.startswith("admin_confirm_delete:"):
            tg_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "DELETE FROM users WHERE telegram_id = ?",
                (tg_id,),
            )
            conn.commit()
            conn.close()

            await query.edit_message_text(
                "🗑️ Compte supprimé.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "👥 Voir les comptes",
                        callback_data="admin_users"
                    )],
                    [InlineKeyboardButton(
                        "↩️ Panneau admin",
                        callback_data="admin_back"
                    )],
                ]),
            )
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
                (request_id,),
            )
            conn.commit()
            conn.close()

            await query.edit_message_text(
                f"✅ Demande #{request_id} validée manuellement.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💰 Demandes de prêt",
                        callback_data="admin_loans"
                    )],
                    [InlineKeyboardButton(
                        "↩️ Panneau admin",
                        callback_data="admin_back"
                    )],
                ]),
            )
            return

        if data.startswith("admin_loan_reject:"):
            request_id = int(data.split(":", 1)[1])

            conn = db()
            conn.execute(
                "UPDATE loan_requests SET status = 'rejected' WHERE id = ?",
                (request_id,),
            )
            conn.commit()
            conn.close()

            await query.edit_message_text(
                f"❌ Demande #{request_id} rejetée.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "💰 Demandes de prêt",
                        callback_data="admin_loans"
                    )],
                    [InlineKeyboardButton(
                        "↩️ Panneau admin",
                        callback_data="admin_back"
                    )],
                ]),
            )
            return

        await query.edit_message_text(
            "❌ Action admin inconnue.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "↩️ Panneau admin",
                    callback_data="admin_back"
                )]
            ]),
        )

    except Exception as e:
        print(f"❌ Erreur admin_callback : {e}")

        try:
            await query.edit_message_text(
                "❌ Une erreur est survenue dans le panneau administrateur.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "↩️ Panneau admin",
                        callback_data="admin_back"
                    )]
                ]),
            )
        except Exception:
            pass
