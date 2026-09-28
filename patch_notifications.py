from pathlib import Path

p = Path("admin_panel.py")
s = p.read_text()

marker = 'async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):'

if marker not in s:
    raise SystemExit("ERREUR: admin_callback introuvable")

if "async def show_notification_users(" in s:
    raise SystemExit("ERREUR: fonction deja presente")

functions = '''
async def show_notification_users(query):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT telegram_id, first_name, last_name, language
        FROM users
        ORDER BY id DESC
    """)
    users = cur.fetchall()
    conn.close()

    buttons = []

    for telegram_id, first_name, last_name, language in users:
        name = "{} {}".format(first_name or "", last_name or "").strip()
        name = name or "Utilisateur"
        lang = language or "fr"

        buttons.append([
            InlineKeyboardButton(
                "👤 {} [{}]".format(name, lang),
                callback_data="admin_notify_user:{}".format(telegram_id)
            )
        ])

    await query.edit_message_text(
        "🔔 NOTIFICATIONS CLIENT\\n\\n"
        "Sélectionnez le client à notifier :",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def show_notification_options(query, telegram_id):
    conn = db()
    cur = conn.cursor()
    cur.execute("""
        SELECT first_name, last_name, language
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,))
    user = cur.fetchone()
    conn.close()

    if not user:
        await query.edit_message_text("❌ Client introuvable.")
        return

    first_name, last_name, language = user
    name = "{} {}".format(first_name or "", last_name or "").strip()
    name = name or "Utilisateur"
    language = language or "fr"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🪪 Notifier : compléter KYC",
            callback_data="admin_notify_kyc:{}".format(telegram_id)
        )],
        [InlineKeyboardButton(
            "💰 Notifier : dossier de prêt",
            callback_data="admin_notify_loan:{}".format(telegram_id)
        )],
        [InlineKeyboardButton(
            "📋 Notifier : garantie / dossier",
            callback_data="admin_notify_guarantee:{}".format(telegram_id)
        )],
        [InlineKeyboardButton(
            "🧾 Notifier : TXID manquant",
            callback_data="admin_notify_txid:{}".format(telegram_id)
        )],
        [InlineKeyboardButton(
            "↩️ Retour",
            callback_data="admin_notifications"
        )]
    ])

    await query.edit_message_text(
        "🔔 NOTIFICATION CLIENT\\n\\n"
        "👤 Client : {}\\n"
        "🌐 Langue : {}\\n"
        "🆔 Telegram : {}\\n\\n"
        "Choisissez la notification :".format(
            name, language, telegram_id
        ),
        reply_markup=keyboard
    )


'''

s = s.replace(marker, functions + marker, 1)

old = '''    if data == "admin_users":
        await show_users(query)
        return

'''

new = '''    if data == "admin_users":
        await show_users(query)
        return

    if data == "admin_notifications":
        await show_notification_users(query)
        return

    if data.startswith("admin_notify_user:"):
        telegram_id = int(data.split(":", 1)[1])
        await show_notification_options(query, telegram_id)
        return

'''

if s.count(old) != 1:
    raise SystemExit(
        "ERREUR: bloc admin_users trouve {} fois".format(s.count(old))
    )

s = s.replace(old, new, 1)

p.write_text(s)
print("OK: notifications client connectees")
