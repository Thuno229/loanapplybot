from loan_callbacks import loan_confirm_callback, loan_cancel_callback, loan_guarantee_sent_callback, loan_conditions_accept_callback
from kyc_flow import kyc_photo_handler, kyc_decision_callback
from admin_panel import admin_panel, admin_callback
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


ADMIN_ID = 8266012108

OFFICIAL_TRC20_ADDRESS = "TAju6xk1rm78Em64ABZJpqHiXoGqF62QBk"
OFFICIAL_BEP20_ADDRESS = "0x6632413e8ba2750d33dc1047a73d01268d345893"

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



# KYC — libellés multilingues
TEXT["fr"]["kyc"] = "🪪 Vérification KYC"
TEXT["en"]["kyc"] = "🪪 KYC Verification"
TEXT["es"]["kyc"] = "🪪 Verificación KYC"
TEXT["pt"]["kyc"] = "🪪 Verificação KYC"

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


def update_kyc_status(telegram_id, status):
    conn = db()
    cur = conn.cursor()
    cur.execute("UPDATE users SET kyc_status = ? WHERE telegram_id = ?", (status, telegram_id))
    conn.commit()
    conn.close()


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
            [t["kyc"], t["history"]],
            [t["referral"], t["support"]],
            [t["language"]],
        ],
        resize_keyboard=True,
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Récupération du lien de parrainage :
    # /start ref_<telegram_id>
    referral_code = None

    if context.args:
        arg = context.args[0].strip()

        if arg.startswith("ref_"):
            referral_code = arg[4:].strip().lstrip("@")

    if referral_code:
        context.user_data["referral_code"] = referral_code

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
    context.user_data["terms_accepted"] = False

    terms = {
        "fr": (
            "📘 À PROPOS & CONDITIONS D’UTILISATION\\n\\n"
            "🌍 Loan Request Assistant permet de soumettre "
            "et de suivre une demande de prêt en USDT.\\n\\n"
            "💰 CONDITIONS PRINCIPALES\\n"
            "• Montant : 500 à 50 000 USDT\\n"
            "• Durée : 6 à 44 mois\\n"
            "• Intérêt indiqué : 1 % par mois\\n"
            "• Garantie indicative : 15 % du montant demandé\\n\\n"
            "🛡️ GARANTIE\\n"
            "La garantie est un mécanisme de sécurité destiné "
            "notamment à limiter le risque de non-remboursement. "
            "Dans le cadre du programme, elle est prévue pour "
            "être restituée après le remboursement complet du prêt, "
            "conformément aux conditions du dossier.\\n\\n"
            "🔐 KYC\\n"
            "La vérification KYC est obligatoire avant toute "
            "demande de prêt. Les informations et documents "
            "fournis doivent être exacts et lisibles.\\n\\n"
            "⚠️ IMPORTANT\\n"
            "La soumission d'une demande ne garantit pas "
            "l'acceptation du prêt. Chaque dossier est soumis "
            "aux vérifications et conditions du programme.\\n\\n"
            "🔎 TRANSPARENCE\\n"
            "Ces informations sont présentées avant l'inscription "
            "afin que vous puissiez prendre connaissance des "
            "principales conditions avant de continuer.\\n\\n"
            "En cliquant sur « ✅ Je suis d’accord », vous "
            "confirmez avoir lu et compris ces informations."
        ),

        "en": (
            "📘 ABOUT & TERMS OF USE\\n\\n"
            "🌍 Loan Request Assistant allows you to submit "
            "and track a USDT loan request.\\n\\n"
            "💰 MAIN CONDITIONS\\n"
            "• Amount: 500 to 50,000 USDT\\n"
            "• Duration: 6 to 44 months\\n"
            "• Stated interest: 1% per month\\n"
            "• Indicative guarantee: 15% of the requested amount\\n\\n"
            "🛡️ GUARANTEE\\n"
            "The guarantee is a security mechanism intended, "
            "among other things, to limit the risk of non-repayment. "
            "Under the program, it is intended to be returned after "
            "the loan has been fully repaid, according to the terms "
            "of the loan file.\\n\\n"
            "🔐 KYC\\n"
            "KYC verification is mandatory before submitting a loan "
            "request. The information and documents provided must "
            "be accurate and readable.\\n\\n"
            "⚠️ IMPORTANT\\n"
            "Submitting a request does not guarantee loan approval. "
            "Each application is subject to the program's verification "
            "and conditions.\\n\\n"
            "🔎 TRANSPARENCY\\n"
            "This information is presented before registration so "
            "you can review the main conditions before continuing.\\n\\n"
            "By clicking « ✅ I agree », you confirm that you have "
            "read and understood this information."
        ),

        "es": (
            "📘 INFORMACIÓN Y CONDICIONES DE USO\\n\\n"
            "🌍 Loan Request Assistant permite enviar y seguir "
            "una solicitud de préstamo en USDT.\\n\\n"
            "💰 CONDICIONES PRINCIPALES\\n"
            "• Importe: 500 a 50.000 USDT\\n"
            "• Duración: 6 a 44 meses\\n"
            "• Interés indicado: 1 % mensual\\n"
            "• Garantía indicativa: 15 % del importe solicitado\\n\\n"
            "🛡️ GARANTÍA\\n"
            "La garantía es un mecanismo de seguridad destinado, "
            "entre otras cosas, a limitar el riesgo de impago. "
            "Según las condiciones del programa, está prevista "
            "su devolución después del reembolso completo del préstamo.\\n\\n"
            "🔐 KYC\\n"
            "La verificación KYC es obligatoria antes de solicitar "
            "un préstamo. La información y los documentos deben "
            "ser exactos y legibles.\\n\\n"
            "⚠️ IMPORTANTE\\n"
            "Enviar una solicitud no garantiza la aprobación del préstamo. "
            "Cada expediente está sujeto a las verificaciones y "
            "condiciones del programa.\\n\\n"
            "🔎 TRANSPARENCIA\\n"
            "Esta información se presenta antes del registro para "
            "que pueda conocer las principales condiciones antes de continuar.\\n\\n"
            "Al pulsar « ✅ Estoy de acuerdo », confirma que ha "
            "leído y comprendido esta información."
        ),

        "pt": (
            "📘 SOBRE E CONDIÇÕES DE UTILIZAÇÃO\\n\\n"
            "🌍 O Loan Request Assistant permite enviar e acompanhar "
            "um pedido de empréstimo em USDT.\\n\\n"
            "💰 CONDIÇÕES PRINCIPAIS\\n"
            "• Valor: 500 a 50.000 USDT\\n"
            "• Prazo: 6 a 44 meses\\n"
            "• Juros indicados: 1% por mês\\n"
            "• Garantia indicativa: 15% do valor solicitado\\n\\n"
            "🛡️ GARANTIA\\n"
            "A garantia é um mecanismo de segurança destinado, "
            "entre outras coisas, a limitar o risco de não pagamento. "
            "De acordo com as condições do programa, está prevista "
            "a sua devolução após o reembolso total do empréstimo.\\n\\n"
            "🔐 KYC\\n"
            "A verificação KYC é obrigatória antes de solicitar um "
            "empréstimo. As informações e documentos fornecidos "
            "devem ser corretos e legíveis.\\n\\n"
            "⚠️ IMPORTANTE\\n"
            "O envio de um pedido não garante a aprovação do empréstimo. "
            "Cada pedido está sujeito às verificações e condições do programa.\\n\\n"
            "🔎 TRANSPARÊNCIA\\n"
            "Estas informações são apresentadas antes do registo para "
            "que possa conhecer as principais condições antes de continuar.\\n\\n"
            "Ao clicar em « ✅ Concordo », confirma que leu e compreendeu "
            "estas informações."
        ),
    }

    buttons = {
        "fr": "✅ Je suis d’accord",
        "en": "✅ I agree",
        "es": "✅ Estoy de acuerdo",
        "pt": "✅ Concordo",
    }

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                buttons[lang],
                callback_data="terms_accept"
            )
        ]
    ])

    await update.message.reply_text(
        terms[lang],
        reply_markup=keyboard
    )

    return 1


async def terms_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    lang = context.user_data.get("language", "fr")

    if query.data != "terms_accept":
        return 1

    context.user_data["terms_accepted"] = True

    await query.edit_message_reply_markup(reply_markup=None)

    await query.message.reply_text(
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
        try:
            referrer_id = int(referral_code)
        except ValueError:
            referrer_id = None

        if referrer_id and referrer_id != user.id:
            conn = db()
            cur = conn.cursor()

            cur.execute(
                "SELECT telegram_id FROM users WHERE telegram_id = ?",
                (referrer_id,),
            )
            row = cur.fetchone()

            if row:
                referred_by = referrer_id

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

    # Enregistrer le parrainage une seule fois
    if referred_by:
        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT OR IGNORE INTO referrals
            (referrer_id, referred_id, reward, status)
            VALUES (?, ?, 5, 'pending')
            """,
            (referred_by, user.id),
        )

        conn.commit()
        conn.close()

        # Informer le parrain de la nouvelle inscription
        try:
            await context.bot.send_message(
                chat_id=referred_by,
                text=(
                    "🎉 NOUVEAU FILLEUL !\n\n"
                    f"👤 {user.first_name} vient de s'inscrire avec votre lien.\n\n"
                    "🎁 Parrainage enregistré avec succès.\n"
                    "💰 Récompense potentielle : 5 USDT\n"
                    "⏳ Statut : en attente des conditions du programme.\n\n"
                    "📊 Votre compteur a été mis à jour automatiquement."
                ),
            )
        except Exception:
            pass

    if referred_by:
        conn = db()
        cur = conn.cursor()
        cur.execute(
            "SELECT first_name, username FROM users WHERE telegram_id = ?",
            (referred_by,),
        )
        referrer = cur.fetchone()
        conn.close()

        if referrer:
            referrer_name = referrer[0] or "Votre parrain"
            referral_message = (
                f"\n\n🎁 PARRAINAGE ENREGISTRÉ !\n"
                f"👤 Votre parrain : {referrer_name}\n"
                f"✅ Votre inscription a bien été associée à son lien.\n"
                f"💰 Récompense potentielle du parrain : 5 USDT\n"
                f"⏳ Statut : en attente des conditions du programme."
            )
        else:
            referral_message = ""
    else:
        referral_message = ""

    await update.message.reply_text(
        TEXT[lang]["done"] + referral_message + "\n\n" +
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

    # RÉCEPTION DU TXID / HASH
    if context.user_data.get("awaiting_loan_txid"):
        txid = (text or "").strip()

        if (
            len(txid) < 8
            or len(txid) > 256
            or any(ch.isspace() for ch in txid)
        ):
            await update.message.reply_text(
                "❌ TXID invalide.\n\n"
                "Envoyez uniquement le TXID/hash de la transaction, "
                "sans espace."
            )
            return

        context.user_data["loan_txid"] = txid
        context.user_data["awaiting_loan_txid"] = False

        amount = context.user_data.get("loan_amount", 0)
        duration = context.user_data.get("loan_duration", 0)
        network = context.user_data.get("loan_network", "")
        wallet = context.user_data.get("wallet_address", "")
        interest = context.user_data.get("interest", 0)
        total_repayment = context.user_data.get("total_repayment", 0)
        monthly_payment = context.user_data.get("monthly_payment", 0)
        guarantee = amount * 0.15

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Confirmer la demande",
                    callback_data="loan_confirm"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Annuler",
                    callback_data="loan_cancel"
                )
            ]
        ])

        await update.message.reply_text(
            "📋 RÉCAPITULATIF FINAL\n\n"
            f"💰 Montant : {amount:g} USDT\n"
            f"📅 Durée : {duration} mois\n"
            "📈 Intérêt : 1 % / mois\n"
            f"💵 Intérêts totaux : {interest:g} USDT\n"
            f"💳 Total à rembourser : {total_repayment:g} USDT\n"
            f"🧮 Mensualité : {monthly_payment:.2f} USDT\n"
            f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
            f"🌐 Réseau : {network}\n"
            f"📍 Adresse de réception : {wallet}\n"
            f"📄 TXID : {txid}\n\n"
            "⚠️ Le TXID sera vérifié manuellement.\n"
            "⚠️ Aucune validation automatique du paiement n'est effectuée.\n\n"
            "Souhaitez-vous confirmer la demande ?",
            reply_markup=keyboard
        )
        return

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

        guarantee = context.user_data.get("loan_amount", 0) * 0.15

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ Garantie envoyée",
                    callback_data="loan_guarantee_sent"
                )
            ],
            [
                InlineKeyboardButton(
                    "❌ Annuler",
                    callback_data="loan_cancel"
                )
            ]
        ])

        await update.message.reply_text(
            "📋 RÉCAPITULATIF DE VOTRE DEMANDE\n\n"
            f"💰 Montant : {context.user_data.get('loan_amount', 0):g} USDT\n"
            f"📅 Durée : {context.user_data.get('loan_duration', 0)} mois\n"
            "📈 Intérêt : 1 % / mois\n"
            f"💵 Intérêts totaux : {context.user_data.get('interest', 0):g} USDT\n"
            f"💳 Total à rembourser : {context.user_data.get('total_repayment', 0):g} USDT\n"
            f"🧮 Mensualité : {context.user_data.get('monthly_payment', 0):.2f} USDT\n"
            f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
            f"🌐 Réseau : {network}\n"
            f"📍 Adresse : {address}\n\n"
            "⚠️ Vérifiez attentivement toutes les informations.\n"
            "La demande sera soumise à une vérification manuelle.\n\n"
            "Souhaitez-vous confirmer ?",
            reply_markup=keyboard
        )
        return

    # TRAITEMENT AUTOMATIQUE DU MONTANT DU PRET
    if context.user_data.get("awaiting_loan_duration"):
        try:
            months = int(text.strip())
        except ValueError:
            await update.message.reply_text("❌ Durée invalide.\n\nVeuillez entrer un nombre entier entre 6 et 44.\nExemple : 12")
            return

        if months < 6 or months > 44:
            await update.message.reply_text("❌ Durée invalide.\n\nLa durée doit être comprise entre 6 et 44 mois.")
            return

        amount = context.user_data.get("loan_amount", 0)
        interest = amount * 0.01 * months
        total_repayment = amount + interest
        monthly_payment = total_repayment / months
        guarantee = amount * 0.15

        context.user_data["loan_duration"] = months
        context.user_data["interest"] = interest
        context.user_data["total_repayment"] = total_repayment
        context.user_data["monthly_payment"] = monthly_payment
        context.user_data["awaiting_loan_duration"] = False

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔵 TRC20", callback_data="loan_network_trc20"),
                InlineKeyboardButton("🟡 BEP20", callback_data="loan_network_bep20")
            ]
        ])

        await update.message.reply_text(
            "📋 CONDITIONS DU PRÊT\n\n"
            f"💰 Montant : {amount:g} USDT\n"
            f"📅 Durée : {months} mois\n"
            "📈 Intérêt : 1 % / mois\n"
            f"💵 Intérêts totaux : {interest:g} USDT\n"
            f"💳 Total à rembourser : {total_repayment:g} USDT\n"
            f"🧮 Mensualité : {monthly_payment:.2f} USDT\n"
            f"📊 Garantie indicative (15%) : {guarantee:g} USDT\n\n"
            "🌐 Choisissez le réseau de réception :",
            reply_markup=keyboard
        )
        return

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
        context.user_data["awaiting_loan_duration"] = True

        await update.message.reply_text(f"✅ Montant accepté : {amount:g} USDT\n\n📅 CHOISISSEZ LA DURÉE DE REMBOURSEMENT\n\n📌 Minimum : 6 mois\n📌 Maximum : 44 mois\n\nEntrez un nombre entier entre 6 et 44.\nExemple : 12")
        return

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

        if user is None:
            await update.message.reply_text(
                "❌ Votre compte utilisateur est introuvable.\n\n"
                "Veuillez utiliser /start pour initialiser votre compte."
            )
            return

        link = (
            f"https://t.me/LoanApply24Bot?start=ref_{user_id}"
        )

        conn = db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT COUNT(*)
            FROM referrals
            WHERE referrer_id = ?
            """,
            (user_id,)
        )
        referral_count = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT COALESCE(SUM(reward), 0)
            FROM referrals
            WHERE referrer_id = ?
            """,
            (user_id,)
        )
        total_rewards = cur.fetchone()[0] or 0

        cur.execute(
            """
            SELECT COALESCE(SUM(reward), 0)
            FROM referrals
            WHERE referrer_id = ? AND status = 'completed'
            """,
            (user_id,)
        )
        earned_rewards = cur.fetchone()[0] or 0

        conn.close()

        await update.message.reply_text(
            "🎁 MON PARRAINAGE\n\n"
            f"👥 Filleuls inscrits : {referral_count}\n"
            f"💰 Récompenses potentielles : {total_rewards:g} USDT\n"
            f"✅ Récompenses validées : {earned_rewards:g} USDT\n\n"
            f"🔗 Votre lien personnel :\n{link}\n\n"
            "📌 Invitez vos amis avec ce lien.\n"
            "⏳ La récompense de 5 USDT est accordée lorsque "
            "les conditions du programme sont remplies.",
        )

    elif text == t["profile"]:

        user = get_user(user_id)

        if user is None:
            await update.message.reply_text(
                "❌ Votre compte utilisateur est introuvable.\n\n"
                "Veuillez utiliser /start pour créer votre compte."
            )
            return

        message = (
            f"👤 {user[4]} {user[5]}\n"
            f"🌍 {user[6]}\n"
            f"📱 {user[7]}\n"
            f"📧 {user[8]}\n"
            f"💼 {user[9]}\n\n"
            f"🪪 KYC : {user[13] or 'not_submitted'}"
        )

        await update.message.reply_text(message)

    elif text == t["kyc"]:
        user = get_user(user_id)

        if user is None:
            await update.message.reply_text(
                "❌ Votre compte utilisateur est introuvable.\n\n"
                "Veuillez utiliser /start pour créer votre compte."
            )
            return

        status = user[13] or "not_submitted"

        if status == "approved":
            await update.message.reply_text(
                "✅ Votre KYC est déjà validé.\n\n"
                "Vous pouvez utiliser les fonctionnalités disponibles."
            )

        elif status == "pending":
            await update.message.reply_text(
                "⏳ Votre KYC est actuellement en cours de vérification.\n\n"
                "Veuillez patienter jusqu'à la décision de l'administrateur."
            )

        else:
            context.user_data["awaiting_kyc_photo"] = True

            await update.message.reply_text(
                "🪪 VÉRIFICATION KYC\n\n"
                "Envoyez une photo claire et lisible de votre document d'identité.\n\n"
                "⚠️ Le document doit être lisible et correspondre aux informations "
                "de votre inscription.\n\n"
                "📸 Envoyez maintenant la photo."
            )

        return

    elif text == t["loan"]:
        user = get_user(user_id)

        if user is None:
            await update.message.reply_text(
                "❌ Votre compte utilisateur est introuvable.\n\n"
                "Veuillez utiliser /start pour créer votre compte."
            )
            return

        kyc_status = user[13] or "not_submitted"

        if kyc_status != "approved":
            if kyc_status == "pending":
                message = (
                    "⏳ Votre vérification KYC est en cours.\n\n"
                    "Vous devez attendre sa validation avant de demander un prêt."
                )
            elif kyc_status == "rejected":
                message = (
                    "❌ Votre vérification KYC a été rejetée.\n\n"
                    "Veuillez effectuer à nouveau votre KYC avant de demander un prêt."
                )
            else:
                message = (
                    "❌ Demande de prêt impossible.\n\n"
                    "🪪 Vous devez d'abord effectuer votre vérification KYC.\n\n"
                    "Appuyez sur « 🪪 Vérification KYC » dans le menu, "
                    "puis envoyez votre document d'identité."
                )

            await update.message.reply_text(message)
            return

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

    else:
        await update.message.reply_text(
            "Veuillez utiliser le menu ci-dessous pour naviguer dans le bot.",
            reply_markup=dashboard_keyboard(lang),
        )


# =========================
# MAIN
# =========================

async def loan_network_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    network = query.data.replace("loan_network_", "").upper()

    if network not in ("TRC20", "BEP20"):
        await query.edit_message_text(
            "❌ Réseau invalide. Veuillez recommencer."
        )
        return

    context.user_data["loan_network"] = network
    context.user_data["awaiting_wallet_address"] = True

    amount = context.user_data.get("loan_amount", 0)
    duration = context.user_data.get("loan_duration", 0)
    interest = context.user_data.get("interest", 0)
    total_repayment = context.user_data.get("total_repayment", 0)
    monthly_payment = context.user_data.get("monthly_payment", 0)

    await query.edit_message_text(
        f"✅ Réseau sélectionné : {network}\\n\\n"
        f"💰 Montant : {amount:g} USDT\\n"
        f"📅 Durée : {duration} mois\\n"
        "📈 Intérêt : 1 % / mois\\n"
        f"💵 Intérêts totaux : {interest:g} USDT\\n"
        f"💳 Total à rembourser : {total_repayment:g} USDT\\n"
        f"🧮 Mensualité : {monthly_payment:.2f} USDT\\n\\n"
        "📍 ADRESSE DE RÉCEPTION DU PRÊT\\n\\n"
        f"Envoyez votre adresse {network}, "
        "celle sur laquelle vous souhaitez recevoir les USDT "
        "si votre demande est approuvée.\\n\\n"
        "⚠️ Vérifiez attentivement l'adresse avant de l'envoyer."
    )


def main():

    init_database()

    application = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30).build()

    registration = ConversationHandler(
        entry_points=[
            CommandHandler("start", start)
        ],

        states={
            1: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    choose_language
                ),
                CallbackQueryHandler(
                    terms_accept,
                    pattern=r"^terms_accept$"
                ),
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

    application.add_handler(CommandHandler("admin", admin_panel))

    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^admin_"
        )
    )


    application.add_handler(registration)

    application.add_handler(
        MessageHandler(
            filters.PHOTO,
            kyc_photo_handler
        )
    )

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

    application.add_handler(CallbackQueryHandler(loan_confirm_callback, pattern=r"^loan_confirm$"))
    application.add_handler(CallbackQueryHandler(
        loan_conditions_accept_callback,
        pattern=r"^loan_conditions_accept$"
    ))
    application.add_handler(
        CallbackQueryHandler(
            loan_guarantee_sent_callback,
            pattern=r"^loan_guarantee_sent$"
        )
    )
    application.add_handler(CallbackQueryHandler(loan_cancel_callback, pattern=r"^loan_cancel$"))

    application.add_handler(
        CallbackQueryHandler(
            kyc_decision_callback,
            pattern=r"^kyc_(approve|reject):\d+$"
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()
