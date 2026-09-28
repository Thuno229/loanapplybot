import os
import secrets
import sqlite3

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    CallbackQueryHandler,
)

from database import init_database


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN est manquant.")


# =========================
# LANGUES
# =========================

LANGUAGES = {
    "fr": "🇫🇷 Français",
    "en": "🇬🇧 English",
    "es": "🇪🇸 Español",
    "pt": "🇵🇹 Português",
}


TEXT = {
    "fr": {
        "welcome": "👋 Bienvenue sur Loan Request Assistant !\n\nChoisissez votre langue :",
        "registered": "✅ Votre compte existe déjà.",
        "dashboard": "🏠 Tableau de bord",
        "profile": "👤 Mon profil",
        "loan": "💰 Demander un prêt",
        "referral": "🎁 Parrainage",
        "history": "📋 Mes demandes",
        "support": "🆘 Support",
        "language": "🌐 Langue",
        "name": "Quel est votre prénom ?",
        "lastname": "Quel est votre nom de famille ?",
        "country": "Dans quel pays résidez-vous ?",
        "phone": "Veuillez partager votre numéro de téléphone.",
        "email": "Quelle est votre adresse e-mail ?",
        "profession": "Quelle est votre profession ?",
        "photo": "Envoyez maintenant une photo de profil.",
        "trc20": "Entrez votre adresse USDT TRC20.\n\nSi vous n'en avez pas, envoyez /skip.",
        "bep20": "Entrez votre adresse USDT BEP20.\n\nSi vous n'en avez pas, envoyez /skip.",
        "done": "✅ Inscription terminée !",
        "dashboard_menu": "Choisissez une option :",
        "referral_text": "🎁 Votre lien personnel de parrainage :\n\n{link}\n\nRécompense : 5 USDT lorsque les conditions du programme sont remplies.",
        "self_referral": "❌ Vous ne pouvez pas utiliser votre propre lien de parrainage.",
        "cancel": "❌ Inscription annulée.",
        "skip": "Passé.",
    },
    "en": {
        "welcome": "👋 Welcome to Loan Request Assistant!\n\nChoose your language:",
        "registered": "✅ Your account already exists.",
        "dashboard": "🏠 Dashboard",
        "profile": "👤 My profile",
        "loan": "💰 Apply for a loan",
        "referral": "🎁 Referral",
        "history": "📋 My applications",
        "support": "🆘 Support",
        "language": "🌐 Language",
        "name": "What is your first name?",
        "lastname": "What is your last name?",
        "country": "Which country do you live in?",
        "phone": "Please share your phone number.",
        "email": "What is your email address?",
        "profession": "What is your profession?",
        "photo": "Now send a profile photo.",
        "trc20": "Enter your USDT TRC20 address.\n\nIf you don't have one, send /skip.",
        "bep20": "Enter your USDT BEP20 address.\n\nIf you don't have one, send /skip.",
        "done": "✅ Registration completed!",
        "dashboard_menu": "Choose an option:",
        "referral_text": "🎁 Your personal referral link:\n\n{link}\n\nReward: 5 USDT when the program conditions are met.",
        "self_referral": "❌ You cannot use your own referral link.",
        "cancel": "❌ Registration cancelled.",
        "skip": "Skipped.",
    },
    "es": {
        "welcome": "👋 ¡Bienvenido a Loan Request Assistant!\n\nElige tu idioma:",
        "registered": "✅ Tu cuenta ya existe.",
        "dashboard": "🏠 Panel",
        "profile": "👤 Mi perfil",
        "loan": "💰 Solicitar préstamo",
        "referral": "🎁 Referidos",
        "history": "📋 Mis solicitudes",
        "support": "🆘 Soporte",
        "language": "🌐 Idioma",
        "name": "¿Cuál es tu nombre?",
        "lastname": "¿Cuál es tu apellido?",
        "country": "¿En qué país resides?",
        "phone": "Comparte tu número de teléfono.",
        "email": "¿Cuál es tu correo electrónico?",
        "profession": "¿Cuál es tu profesión?",
        "photo": "Ahora envía una foto de perfil.",
        "trc20": "Introduce tu dirección USDT TRC20.\n\nSi no tienes una, envía /skip.",
        "bep20": "Introduce tu dirección USDT BEP20.\n\nSi no tienes una, envía /skip.",
        "done": "✅ Registro completado!",
        "dashboard_menu": "Elige una opción:",
        "referral_text": "🎁 Tu enlace personal de referido:\n\n{link}\n\nRecompensa: 5 USDT cuando se cumplan las condiciones.",
        "self_referral": "❌ No puedes utilizar tu propio enlace.",
        "cancel": "❌ Registro cancelado.",
        "skip": "Omitido.",
    },
    "pt": {
        "welcome": "👋 Bem-vindo ao Loan Request Assistant!\n\nEscolha o seu idioma:",
        "registered": "✅ A sua conta já existe.",
        "dashboard": "🏠 Painel",
        "profile": "👤 Meu perfil",
        "loan": "💰 Solicitar empréstimo",
        "referral": "🎁 Indicações",
        "history": "📋 Minhas solicitações",
        "support": "🆘 Suporte",
        "language": "🌐 Idioma",
        "name": "Qual é o seu primeiro nome?",
        "lastname": "Qual é o seu sobrenome?",
        "country": "Em qual país você mora?",
        "phone": "Compartilhe seu número de telefone.",
        "email": "Qual é o seu e-mail?",
        "profession": "Qual é a sua profissão?",
        "photo": "Agora envie uma foto de perfil.",
        "trc20": "Digite seu endereço USDT TRC20.\n\nSe não tiver um, envie /skip.",
        "bep20": "Digite seu endereço USDT BEP20.\n\nSe não tiver um, envie /skip.",
        "done": "✅ Cadastro concluído!",
        "dashboard_menu": "Escolha uma opção:",
        "referral_text": "🎁 Seu link pessoal de indicação:\n\n{link}\n\nRecompensa: 5 USDT quando as condições forem cumpridas.",
        "self_referral": "❌ Você não pode usar seu próprio link.",
        "cancel": "❌ Cadastro cancelado.",
        "skip": "Ignorado.",
    },
}


# =========================
# BASE DE DONNÉES
# =========================

def db():
    return sqlite3.connect("loan_bot.db")


def get_user(telegram_id):
    conn = db()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    user = cur.fetchone()
    conn.close()
    return user


def create_referral_code():
    return secrets.token_hex(5)


def save_user(data):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (
            telegram_id,
            username,
            language,
            first_name,
            last_name,
            country,
            phone,
            email,
            profession,
            photo_file_id,
            trc20_address,
            bep20_address,
            referral_code,
            referred_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data["telegram_id"],
            data["username"],
            data["language"],
            data["first_name"],
            data["last_name"],
            data["country"],
            data["phone"],
            data["email"],
            data["profession"],
            data["photo_file_id"],
            data["trc20_address"],
            data["bep20_address"],
            data["referral_code"],
            data.get("referred_by"),
        ),
    )

    conn.commit()
    conn.close()


def get_language(user_id):
    user = get_user(user_id)

    if user and user[3]:
        return user[3]

    return "fr"


# =========================
# CLAVIER
# =========================

def dashboard_keyboard(lang):
    t = TEXT[lang]

    return ReplyKeyboardMarkup(
        [
            [t["profile"], t["loan"]],
            [t["referral"], t["history"]],
            [t["support"], t["language"]],
        ],
        resize_keyboard=True,
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    existing = get_user(user_id)

    if existing:
        lang = get_language(user_id)

        await update.message.reply_text(
            TEXT[lang]["registered"] + "\n\n" +
            TEXT[lang]["dashboard_menu"],
            reply_markup=dashboard_keyboard(lang),
        )

        return ConversationHandler.END

    keyboard = ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🇫🇷 Français"),
                KeyboardButton("🇬🇧 English"),
            ],
            [
                KeyboardButton("🇪🇸 Español"),
                KeyboardButton("🇵🇹 Português"),
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        TEXT["fr"]["welcome"],
        reply_markup=keyboard,
    )

    return 1


# =========================
# LANGUE
# =========================

async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    languages = {
        "🇫🇷 Français": "fr",
        "🇬🇧 English": "en",
        "🇪🇸 Español": "es",
        "🇵🇹 Português": "pt",
    }

    lang = languages.get(text)

    if not lang:
        return 1

    context.user_data["language"] = lang

    await update.message.reply_text(
        TEXT[lang]["name"]
    )

    return 2


async def first_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["first_name"] = update.message.text

    lang = context.user_data["language"]

    await update.message.reply_text(TEXT[lang]["lastname"])

    return 3


async def last_name(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["last_name"] = update.message.text

    lang = context.user_data["language"]

    await update.message.reply_text(TEXT[lang]["country"])

    return 4


async def country(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["country"] = update.message.text

    lang = context.user_data["language"]

    keyboard = ReplyKeyboardMarkup(
        [[KeyboardButton(
            "📱 Partager mon numéro",
            request_contact=True
        )]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await update.message.reply_text(
        TEXT[lang]["phone"],
        reply_markup=keyboard,
    )

    return 5


async def phone(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.contact:
        context.user_data["phone"] = update.message.contact.phone_number
    else:
        context.user_data["phone"] = update.message.text

    lang = context.user_data["language"]

    await update.message.reply_text(TEXT[lang]["email"])

    return 6


async def email(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["email"] = update.message.text

    lang = context.user_data["language"]

    await update.message.reply_text(TEXT[lang]["profession"])

    return 7


async def profession(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["profession"] = update.message.text

    lang = context.user_data["language"]

    await update.message.reply_text(TEXT[lang]["photo"])

    return 8


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lang = context.user_data["language"]

    if update.message.photo:
        context.user_data["photo_file_id"] = (
            update.message.photo[-1].file_id
        )
    else:
        context.user_data["photo_file_id"] = None

    await update.message.reply_text(TEXT[lang]["trc20"])

    return 9


async def trc20(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lang = context.user_data["language"]

    if update.message.text == "/skip":
        context.user_data["trc20_address"] = None
    else:
        context.user_data["trc20_address"] = update.message.text

    await update.message.reply_text(TEXT[lang]["bep20"])

    return 10


async def bep20(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lang = context.user_data["language"]

    if update.message.text == "/skip":
        context.user_data["bep20_address"] = None
    else:
        context.user_data["bep20_address"] = update.message.text

    user = update.effective_user

    referral_code = context.user_data.get("referral_code")

    referred_by = None

    if referral_code:
        conn = db()
        cur = conn.cursor()

        cur.execute(
            "SELECT telegram_id FROM users WHERE referral_code = ?",
            (referral_code,),
        )

        row = cur.fetchone()

        if row and row[0] != user.id:
            referred_by = row[0]

        conn.close()

    data = {
        "telegram_id": user.id,
        "username": user.username,
        "language": lang,
        "first_name": context.user_data["first_name"],
        "last_name": context.user_data["last_name"],
        "country": context.user_data["country"],
        "phone": context.user_data["phone"],
        "email": context.user_data["email"],
        "profession": context.user_data["profession"],
        "photo_file_id": context.user_data.get("photo_file_id"),
        "trc20_address": context.user_data.get("trc20_address"),
        "bep20_address": context.user_data.get("bep20_address"),
        "referral_code": create_referral_code(),
        "referred_by": referred_by,
    }

    save_user(data)

    await update.message.reply_text(
        TEXT[lang]["done"] + "\n\n" +
        TEXT[lang]["dashboard_menu"],
        reply_markup=dashboard_keyboard(lang),
    )

    context.user_data.clear()

    return ConversationHandler.END


# =========================
# ANNULATION
# =========================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    lang = context.user_data.get("language", "fr")

    await update.message.reply_text(
        TEXT[lang]["cancel"]
    )

    context.user_data.clear()

    return ConversationHandler.END


# =========================
# TABLEAU DE BORD
# =========================

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    lang = get_language(user_id)

    text = update.message.text
    t = TEXT[lang]

    # VALIDATION DE L'ADRESSE SELON LE RESEAU
    if context.user_data.get("awaiting_wallet_address"):
        address = (text or "").strip()
        network = context.user_data.get("loan_network")

        if network == "TRC20":
            valid = (
                len(address) == 34
                and address.startswith("T")
                and all(c.isalnum() for c in address)
            )
        elif network == "BEP20":
            valid = (
                len(address) == 42
                and address.startswith(("0x", "0X"))
                and all(c in "0123456789abcdefABCDEF" for c in address[2:])
            )
        else:
            valid = False

        if not valid:
            example = (
                "T... (34 caractères)"
                if network == "TRC20"
                else "0x... (42 caractères)"
            )

            await update.message.reply_text(
                f"❌ Adresse {network} invalide.\n\n"
                f"Veuillez entrer une adresse {network} valide.\n"
                f"Exemple de format : {example}"
            )
            return

        context.user_data["wallet_address"] = address
        context.user_data["awaiting_wallet_address"] = False

        await update.message.reply_text(
            f"✅ Adresse {network} acceptée.\n\n"
            f"📍 Adresse : {address}\n\n"
            "Votre adresse a été enregistrée pour la suite de la demande."
        )
        return

    # TRAITEMENT AUTOMATIQUE DU MONTANT DU PRET
    if context.user_data.get("awaiting_loan_amount"):
        try:
            amount = float(text.replace(",", ".").replace(" ", ""))
        except ValueError:
            await update.message.reply_text(
                "❌ Veuillez entrer uniquement un montant en USDT.\n\n"
                "Exemple : 500"
            )
            return

        if amount < 500:
            await update.message.reply_text(
                "❌ Demande refusée.\n\n"
                "Le montant minimum est de 500 USDT."
            )
            return

        if amount > 50000:
            await update.message.reply_text(
                "❌ Demande refusée.\n\n"
                "Le montant maximum est de 50 000 USDT."
            )
            return

        context.user_data["loan_amount"] = amount
        context.user_data["awaiting_loan_amount"] = False

        guarantee = amount * 0.15

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔵 TRC20", callback_data="loan_network_trc20"),
                InlineKeyboardButton("🟡 BEP20", callback_data="loan_network_bep20")
            ]
        ])

        await update.message.reply_text(
            f"✅ Montant accepté : {amount:g} USDT\n\n"
            f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n\n"
            "🌐 Choisissez le réseau de réception :",
            reply_markup=keyboard
        )
        return


    if text == t["referral"]:
        user = get_user(user_id)

        referral_code = user[13]

        bot_username = (await context.bot.get_me()).username

        link = (
            f"https://t.me/{bot_username}?start=ref_{referral_code}"
        )

        await update.message.reply_text(
            t["referral_text"].format(link=link)
        )

    elif text == t["profile"]:

        user = get_user(user_id)

        message = (
            f"👤 {user[4]} {user[5]}\n"
            f"🌍 {user[6]}\n"
            f"📱 {user[7]}\n"
            f"📧 {user[8]}\n"
            f"💼 {user[9]}\n\n"
            f"🪪 KYC : {user[14] or 'not_submitted'}"
        )

        await update.message.reply_text(message)

    elif text == t["loan"]:

        context.user_data["awaiting_loan_amount"] = True

        await update.message.reply_text(
            "💰 Entrez le montant du prêt souhaité en USDT.\n\n"
            "📌 Minimum : 500 USDT\n"
            "📌 Maximum : 50 000 USDT\n\n"
            "Exemple : 500"
        )
        return

    elif text == t["history"]:

        await update.message.reply_text(
            "📋 Vous n'avez pas encore de demande de prêt."
        )

    elif text == t["support"]:

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💬 Support Telegram",
                        url="https://t.me/globalusdtfinance"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📧 globalusdtfinance@gmail.com",
                        url="https://mail.google.com/mail/?view=cm&to=Globalusdtfinance@gmail.com"
                    )
                ]
            ])

            await update.message.reply_text(
                "🆘 Support\n\n"
                "Choisissez votre moyen de contact :",
                reply_markup=keyboard
            )
    elif text == t["language"]:

        await update.message.reply_text(
            "🌐 Pour changer de langue, utilisez /start."
        )


# =========================
# MAIN
# =========================

async def loan_network_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    network = query.data.replace("loan_network_", "").upper()
    context.user_data["loan_network"] = network

    amount = context.user_data.get("loan_amount", 0)

    await query.edit_message_text(
        f"✅ Réseau sélectionné : {network}\n\n"
        f"💰 Montant : {amount:g} USDT\n\n"
        "Votre choix a été enregistré."
    )


def main():

    init_database()

    application = Application.builder().token(TOKEN).build()

    registration = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],

        states={
            1: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    choose_language
                )
            ],

            2: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    first_name
                )
            ],

            3: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    last_name
                )
            ],

            4: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    country
                )
            ],

            5: [
                MessageHandler(
                    filters.CONTACT | (filters.TEXT & ~filters.COMMAND),
                    phone
                )
            ],

            6: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    email
                )
            ],

            7: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    profession
                )
            ],

            8: [
                MessageHandler(
                    filters.PHOTO,
                    photo
                )
            ],

            9: [
                MessageHandler(
                    filters.TEXT,
                    trc20
                )
            ],

            10: [
                MessageHandler(
                    filters.TEXT,
                    bep20
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
    )

    application.add_handler(registration)

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            dashboard
        )
    )

    print("🤖 Loan Request Assistant est démarré...")

    application.add_handler(
        CallbackQueryHandler(
            loan_network_callback,
            pattern=r"^loan_network_(trc20|bep20)$"
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
