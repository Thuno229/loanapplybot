from storage import DB_PATH, PERSISTENCE_PATH
from dotenv import load_dotenv
load_dotenv()

from datetime import timezone, timedelta
import sqlite3
from loan_callbacks import loan_confirm_callback, loan_cancel_callback, loan_guarantee_sent_callback, loan_conditions_accept_callback, verify_guarantee_address_callback
from kyc_flow import kyc_photo_handler, kyc_decision_callback
from admin_panel import (
    admin_panel,
    admin_callback,
    admin_disbursement_message,
    ADMIN_ID,
)
import os
import re
from datetime import datetime

BOT_DATA_DIR = os.getenv("BOT_DATA_DIR", ".")
DB_PATH = os.path.join(BOT_DATA_DIR, "loan_bot.db")
PERSISTENCE_PATH = os.path.join(BOT_DATA_DIR, "loan_bot_persistence.pkl")
import secrets
from datetime import date as dt_date
from notifications import send_notification_once
from i18n import get_client_language as i18n_get_client_language, TEXT as I18N_TEXT, tr as i18n_tr

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
    CallbackQueryHandler,
    PicklePersistence,
)

from database import init_database, ensure_enterprise_schema
from enterprise_features import register_enterprise_handlers
from channel_manager import ensure_channel_schema, publish_loan_request, update_loan_post, channel_callback, channel_admin_message, restore_scheduled_posts


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
TEXT["fr"]["current_loan"] = "💳 Mon prêt en cours"
TEXT["en"]["current_loan"] = "💳 My active loan"
TEXT["es"]["current_loan"] = "💳 Mi préstamo activo"
TEXT["pt"]["current_loan"] = "💳 Meu empréstimo ativo"
TEXT["fr"]["tracking"] = "📊 Suivi du dossier"
TEXT["en"]["tracking"] = "📊 Application tracking"
TEXT["es"]["tracking"] = "📊 Seguimiento de la solicitud"
TEXT["pt"]["tracking"] = "📊 Acompanhamento do pedido"
TEXT["fr"]["about"] = "ℹ️ Conditions & À-propos"


TEXT["fr"]["loan_conditions_summary"] = (
    "📋 CONDITIONS DU PRÊT\n\n"
    "💰 Montant : {amount:g} USDT\n"
    "📅 Durée : {duration} mois\n"
    "📈 Intérêt : 1 % / mois\n"
    "💵 Intérêts totaux : {interest:g} USDT\n"
    "💳 Total à rembourser : {total:g} USDT\n"
    "📊 Mensualité : {monthly:.2f} USDT\n"
    "📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
    "🌐 Réseau : {network}\n\n"
    "📍 Votre adresse de réception :\n"
    "{address}\n\n"
    "⚠️ Cette adresse est votre adresse personnelle "
    "de réception du prêt.\n\n"
    "La demande reste soumise à une vérification "
    "et approbation manuelle.\n\n"
    "Cliquez sur « J'accepte les conditions » "
    "pour continuer."
)

TEXT["en"]["loan_conditions_summary"] = (
    "📋 LOAN TERMS\n\n"
    "💰 Amount: {amount:g} USDT\n"
    "📅 Duration: {duration} months\n"
    "📈 Interest: 1% / month\n"
    "💵 Total interest: {interest:g} USDT\n"
    "💳 Total repayment: {total:g} USDT\n"
    "📊 Monthly payment: {monthly:.2f} USDT\n"
    "📊 Indicative guarantee (15%): {guarantee:g} USDT\n"
    "🌐 Network: {network}\n\n"
    "📍 Your receiving address:\n"
    "{address}\n\n"
    "⚠️ This is your personal loan receiving address.\n\n"
    "The application remains subject to manual "
    "verification and approval.\n\n"
    "Click « I accept the terms » to continue."
)

TEXT["es"]["loan_conditions_summary"] = (
    "📋 CONDICIONES DEL PRÉSTAMO\n\n"
    "💰 Importe: {amount:g} USDT\n"
    "📅 Duración: {duration} meses\n"
    "📈 Interés: 1 % / mes\n"
    "💵 Intereses totales: {interest:g} USDT\n"
    "💳 Total a reembolsar: {total:g} USDT\n"
    "📊 Cuota mensual: {monthly:.2f} USDT\n"
    "📊 Garantía indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Red: {network}\n\n"
    "📍 Su dirección de recepción:\n"
    "{address}\n\n"
    "⚠️ Esta es su dirección personal de recepción del préstamo.\n\n"
    "La solicitud está sujeta a verificación "
    "y aprobación manual.\n\n"
    "Pulse « Acepto las condiciones » para continuar."
)

TEXT["pt"]["loan_conditions_summary"] = (
    "📋 CONDIÇÕES DO EMPRÉSTIMO\n\n"
    "💰 Valor: {amount:g} USDT\n"
    "📅 Duração: {duration} meses\n"
    "📈 Juros: 1% / mês\n"
    "💵 Juros totais: {interest:g} USDT\n"
    "💳 Total a reembolsar: {total:g} USDT\n"
    "📊 Parcela mensal: {monthly:.2f} USDT\n"
    "📊 Garantia indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Rede: {network}\n\n"
    "📍 Seu endereço de recebimento:\n"
    "{address}\n\n"
    "⚠️ Este é o seu endereço pessoal de recebimento do empréstimo.\n\n"
    "O pedido está sujeito a verificação "
    "e aprovação manual.\n\n"
    "Clique em « Aceito as condições » para continuar."
)

TEXT["fr"]["duration_invalid"] = (
    "❌ Durée invalide.\n\n"
    "Veuillez entrer un nombre entier entre 6 et 44.\n"
    "Exemple : 12"
)
TEXT["en"]["duration_invalid"] = (
    "❌ Invalid duration.\n\n"
    "Enter a whole number between 6 and 44.\n"
    "Example: 12"
)
TEXT["es"]["duration_invalid"] = (
    "❌ Duración no válida.\n\n"
    "Introduzca un número entero entre 6 y 44.\n"
    "Ejemplo: 12"
)
TEXT["pt"]["duration_invalid"] = (
    "❌ Duração inválida.\n\n"
    "Digite um número inteiro entre 6 e 44.\n"
    "Exemplo: 12"
)

TEXT["fr"]["duration_out_of_range"] = (
    "❌ Durée invalide.\n\n"
    "La durée doit être comprise entre 6 et 44 mois."
)
TEXT["en"]["duration_out_of_range"] = (
    "❌ Invalid duration.\n\n"
    "The duration must be between 6 and 44 months."
)
TEXT["es"]["duration_out_of_range"] = (
    "❌ Duración no válida.\n\n"
    "La duración debe estar entre 6 y 44 meses."
)
TEXT["pt"]["duration_out_of_range"] = (
    "❌ Duração inválida.\n\n"
    "A duração deve estar entre 6 e 44 meses."
)

TEXT["fr"]["menu_navigation"] = "Veuillez utiliser le menu ci-dessous pour naviguer dans le bot."

TEXT["fr"]["loan_conditions"] = (
    "📋 CONDITIONS DU PRÊT\n\n"
    "💰 Montant : {amount:g} USDT\n"
    "📅 Durée : {duration} mois\n"
    "📈 Intérêt : 1 % / mois\n"
    "💵 Intérêts totaux : {interest:g} USDT\n"
    "💳 Total à rembourser : {total:g} USDT\n"
    "🧮 Mensualité : {monthly:.2f} USDT\n"
    "📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
    "🌐 Réseau : {network}\n\n"
    "📍 Votre adresse de réception :\n{address}\n\n"
    "⚠️ Cette adresse est votre adresse personnelle de réception du prêt.\n\n"
    "La demande reste soumise à une vérification et approbation manuelle.\n\n"
    "Cliquez sur « J'accepte les conditions » pour continuer."
)

TEXT["en"]["loan_conditions"] = (
    "📋 LOAN TERMS\n\n"
    "💰 Amount: {amount:g} USDT\n"
    "📅 Duration: {duration} months\n"
    "📈 Interest: 1% / month\n"
    "💵 Total interest: {interest:g} USDT\n"
    "💳 Total repayment: {total:g} USDT\n"
    "🧮 Monthly payment: {monthly:.2f} USDT\n"
    "📊 Indicative guarantee (15%): {guarantee:g} USDT\n"
    "🌐 Network: {network}\n\n"
    "📍 Your receiving address:\n{address}\n\n"
    "⚠️ This is your personal receiving address for the loan.\n\n"
    "The request remains subject to manual review and approval.\n\n"
    "Click « I accept the terms » to continue."
)

TEXT["es"]["loan_conditions"] = (
    "📋 CONDICIONES DEL PRÉSTAMO\n\n"
    "💰 Importe: {amount:g} USDT\n"
    "📅 Duración: {duration} meses\n"
    "📈 Interés: 1 % / mes\n"
    "💵 Intereses totales: {interest:g} USDT\n"
    "💳 Total a devolver: {total:g} USDT\n"
    "🧮 Cuota mensual: {monthly:.2f} USDT\n"
    "📊 Garantía indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Red: {network}\n\n"
    "📍 Su dirección de recepción:\n{address}\n\n"
    "⚠️ Esta es su dirección personal de recepción del préstamo.\n\n"
    "La solicitud queda sujeta a revisión y aprobación manual.\n\n"
    "Pulse « Acepto las condiciones » para continuar."
)

TEXT["pt"]["loan_conditions"] = (
    "📋 CONDIÇÕES DO EMPRÉSTIMO\n\n"
    "💰 Valor: {amount:g} USDT\n"
    "📅 Duração: {duration} meses\n"
    "📈 Juros: 1% / mês\n"
    "💵 Juros totais: {interest:g} USDT\n"
    "💳 Total a reembolsar: {total:g} USDT\n"
    "🧮 Parcela mensal: {monthly:.2f} USDT\n"
    "📊 Garantia indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Rede: {network}\n\n"
    "📍 Seu endereço de recebimento:\n{address}\n\n"
    "⚠️ Este é o seu endereço pessoal para receber o empréstimo.\n\n"
    "O pedido está sujeito a análise e aprovação manual.\n\n"
    "Clique em « Aceito as condições » para continuar."
)

TEXT["fr"]["loan_network_selection"] = ("📋 CONDITIONS DU PRÊT\n\n💰 Montant : {amount:g} USDT\n📅 Durée : {duration} mois\n📈 Intérêt : 1 % / mois\n💵 Intérêts totaux : {interest:g} USDT\n💳 Total à rembourser : {total:g} USDT\n🧮 Mensualité : {monthly:.2f} USDT\n📊 Garantie indicative (15%) : {guarantee:g} USDT\n\n🌐 Choisissez le réseau de réception :")
TEXT["en"]["loan_network_selection"] = ("📋 LOAN TERMS\n\n💰 Amount: {amount:g} USDT\n📅 Duration: {duration} months\n📈 Interest: 1% / month\n💵 Total interest: {interest:g} USDT\n💳 Total repayment: {total:g} USDT\n🧮 Monthly payment: {monthly:.2f} USDT\n📊 Indicative guarantee (15%): {guarantee:g} USDT\n\n🌐 Choose the receiving network:")
TEXT["es"]["loan_network_selection"] = ("📋 CONDICIONES DEL PRÉSTAMO\n\n💰 Importe: {amount:g} USDT\n📅 Duración: {duration} meses\n📈 Interés: 1 % / mes\n💵 Intereses totales: {interest:g} USDT\n💳 Total a devolver: {total:g} USDT\n🧮 Cuota mensual: {monthly:.2f} USDT\n📊 Garantía indicativa (15%): {guarantee:g} USDT\n\n🌐 Elija la red de recepción:")
TEXT["pt"]["loan_network_selection"] = ("📋 CONDIÇÕES DO EMPRÉSTIMO\n\n💰 Valor: {amount:g} USDT\n📅 Duração: {duration} meses\n📈 Juros: 1% / mês\n💵 Juros totais: {interest:g} USDT\n💳 Total a reembolsar: {total:g} USDT\n🧮 Parcela mensal: {monthly:.2f} USDT\n📊 Garantia indicativa (15%): {guarantee:g} USDT\n\n🌐 Escolha a rede de recebimento:")

TEXT["fr"]["invalid_duration"] = "❌ Durée invalide.\n\nVeuillez entrer un nombre entier entre 6 et 44.\nExemple : 12"
TEXT["en"]["invalid_duration"] = "❌ Invalid duration.\n\nEnter a whole number between 6 and 44.\nExample: 12"
TEXT["es"]["invalid_duration"] = "❌ Duración no válida.\n\nIntroduzca un número entero entre 6 y 44.\nEjemplo: 12"
TEXT["pt"]["invalid_duration"] = "❌ Duração inválida.\n\nDigite um número inteiro entre 6 e 44.\nExemplo: 12"

TEXT["fr"]["duration_range"] = "❌ La durée doit être comprise entre 6 et 44 mois."
TEXT["en"]["duration_range"] = "❌ The duration must be between 6 and 44 months."
TEXT["es"]["duration_range"] = "❌ La duración debe estar entre 6 y 44 meses."
TEXT["pt"]["duration_range"] = "❌ A duração deve estar entre 6 e 44 meses."

TEXT["fr"]["invalid_network"] = "❌ Réseau invalide. Veuillez recommencer."

TEXT["fr"]["loan_confirm_button"] = "✅ Confirmer la demande"
TEXT["en"]["loan_confirm_button"] = "✅ Confirm loan request"
TEXT["es"]["loan_confirm_button"] = "✅ Confirmar solicitud"
TEXT["pt"]["loan_confirm_button"] = "✅ Confirmar pedido"

TEXT["fr"]["cancel_button"] = "❌ Annuler"

TEXT["fr"]["accept_conditions_button"] = "✅ J'accepte les conditions"
TEXT["en"]["accept_conditions_button"] = "✅ I accept the terms"
TEXT["es"]["accept_conditions_button"] = "✅ Acepto las condiciones"
TEXT["pt"]["accept_conditions_button"] = "✅ Aceito as condições"
TEXT["en"]["cancel_button"] = "❌ Cancel"
TEXT["es"]["cancel_button"] = "❌ Cancelar"
TEXT["pt"]["cancel_button"] = "❌ Cancelar"

TEXT["fr"]["loan_summary"] = (
    "📋 RÉCAPITULATIF FINAL\n\n"
    "💰 Montant : {amount:g} USDT\n"
    "📅 Durée : {duration} mois\n"
    "📈 Intérêt : 1 % / mois\n"
    "💵 Intérêts totaux : {interest:g} USDT\n"
    "💳 Total à rembourser : {total:g} USDT\n"
    "🧮 Mensualité : {monthly:.2f} USDT\n"
    "📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
    "🌐 Réseau : {network}\n\n"
    "📍 Adresse de réception :\n{address}"
)

TEXT["en"]["loan_summary"] = (
    "📋 FINAL SUMMARY\n\n"
    "💰 Amount: {amount:g} USDT\n"
    "📅 Duration: {duration} months\n"
    "📈 Interest: 1% / month\n"
    "💵 Total interest: {interest:g} USDT\n"
    "💳 Total repayment: {total:g} USDT\n"
    "🧮 Monthly payment: {monthly:.2f} USDT\n"
    "📊 Indicative guarantee (15%): {guarantee:g} USDT\n"
    "🌐 Network: {network}\n\n"
    "📍 Receiving address:\n{address}"
)

TEXT["es"]["loan_summary"] = (
    "📋 RESUMEN FINAL\n\n"
    "💰 Importe: {amount:g} USDT\n"
    "📅 Duración: {duration} meses\n"
    "📈 Interés: 1 % / mes\n"
    "💵 Intereses totales: {interest:g} USDT\n"
    "💳 Total a devolver: {total:g} USDT\n"
    "🧮 Cuota mensual: {monthly:.2f} USDT\n"
    "📊 Garantía indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Red: {network}\n\n"
    "📍 Dirección de recepción:\n{address}"
)

TEXT["pt"]["loan_summary"] = (
    "📋 RESUMO FINAL\n\n"
    "💰 Valor: {amount:g} USDT\n"
    "📅 Duração: {duration} meses\n"
    "📈 Juros: 1% / mês\n"
    "💵 Juros totais: {interest:g} USDT\n"
    "💳 Total a reembolsar: {total:g} USDT\n"
    "🧮 Parcela mensal: {monthly:.2f} USDT\n"
    "📊 Garantia indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Rede: {network}\n\n"
    "📍 Endereço de recebimento:\n{address}"
)
TEXT["en"]["invalid_network"] = "❌ Invalid network. Please try again."
TEXT["es"]["invalid_network"] = "❌ Red no válida. Inténtelo de nuevo."
TEXT["pt"]["invalid_network"] = "❌ Rede inválida. Tente novamente."

TEXT["fr"]["choose_network"] = "🌐 Choisissez le réseau de réception :"
TEXT["en"]["choose_network"] = "🌐 Choose the receiving network:"
TEXT["es"]["choose_network"] = "🌐 Elija la red de recepción:"
TEXT["pt"]["choose_network"] = "🌐 Escolha a rede de recebimento:"

TEXT["fr"]["selected_network"] = "✅ Réseau sélectionné : {network}"
TEXT["en"]["selected_network"] = "✅ Selected network: {network}"
TEXT["es"]["selected_network"] = "✅ Red seleccionada: {network}"
TEXT["pt"]["selected_network"] = "✅ Rede selecionada: {network}"

TEXT["fr"]["confirm_loan"] = "✅ Confirmer la demande"
TEXT["en"]["confirm_loan"] = "✅ Confirm loan request"
TEXT["es"]["confirm_loan"] = "✅ Confirmar solicitud"
TEXT["pt"]["confirm_loan"] = "✅ Confirmar pedido"

TEXT["fr"]["cancel"] = "❌ Annuler"
TEXT["en"]["cancel"] = "❌ Cancel"
TEXT["es"]["cancel"] = "❌ Cancelar"
TEXT["pt"]["cancel"] = "❌ Cancelar"

TEXT["fr"]["amount_accepted"] = "✅ Montant accepté : {amount:g} USDT\n\n📅 CHOISISSEZ LA DURÉE DE REMBOURSEMENT\n\n📌 Minimum : 6 mois\n📌 Maximum : 44 mois\n\nEntrez un nombre entier entre 6 et 44.\nExemple : 12"
TEXT["en"]["amount_accepted"] = "✅ Amount accepted: {amount:g} USDT\n\n📅 CHOOSE THE REPAYMENT DURATION\n\n📌 Minimum: 6 months\n📌 Maximum: 44 months\n\nEnter a whole number between 6 and 44.\nExample: 12"
TEXT["es"]["amount_accepted"] = "✅ Importe aceptado: {amount:g} USDT\n\n📅 ELIJA LA DURACIÓN DEL REEMBOLSO\n\n📌 Mínimo: 6 meses\n📌 Máximo: 44 meses\n\nIntroduzca un número entero entre 6 y 44.\nEjemplo: 12"
TEXT["pt"]["amount_accepted"] = "✅ Valor aceito: {amount:g} USDT\n\n📅 ESCOLHA A DURAÇÃO DO REEMBOLSO\n\n📌 Mínimo: 6 meses\n📌 Máximo: 44 meses\n\nDigite um número inteiro entre 6 e 44.\nExemplo: 12"
TEXT["en"]["menu_navigation"] = "Please use the menu below to navigate the bot."
TEXT["es"]["menu_navigation"] = "Utilice el menú de abajo para navegar por el bot."
TEXT["pt"]["menu_navigation"] = "Use o menu abaixo para navegar no bot."

TEXT["fr"]["support_message"] = (
    "🆘 Support\n\n"
    "Choisissez votre moyen de contact :"
)
TEXT["en"]["support_message"] = (
    "🆘 Support\n\n"
    "Choose your contact method:"
)
TEXT["es"]["support_message"] = (
    "🆘 Soporte\n\n"
    "Elija su medio de contacto:"
)
TEXT["pt"]["support_message"] = (
    "🆘 Suporte\n\n"
    "Escolha seu meio de contato:"
)

TEXT["fr"]["language_message"] = "🌐 Choisissez une langue ci-dessous pour changer la langue."
TEXT["en"]["language_message"] = "🌐 Choose a language below to change your language."
TEXT["es"]["language_message"] = "🌐 Elija un idioma abajo para cambiar el idioma."
TEXT["pt"]["language_message"] = "🌐 Escolha um idioma abaixo para alterar o idioma."
TEXT["en"]["about"] = "ℹ️ Terms & About"
TEXT["es"]["about"] = "ℹ️ Condiciones y Acerca de"
TEXT["pt"]["about"] = "ℹ️ Condições e Sobre"
TEXT["fr"]["loan_kyc_required"]="❌ Demande de prêt impossible.\n🪪 Vous devez d'abord effectuer votre vérification KYC.\nAppuyez sur « 🪪 Vérification KYC » dans le menu pour continuer."
TEXT["en"]["loan_kyc_required"]="❌ Loan request unavailable.\n🪪 You must complete KYC verification first.\nTap « 🪪 KYC Verification » in the menu to continue."
TEXT["es"]["loan_kyc_required"]="❌ Solicitud de préstamo no disponible.\n🪪 Primero debes completar la verificación KYC.\nPulsa « 🪪 Verificación KYC » en el menú para continuar."
TEXT["pt"]["loan_kyc_required"]="❌ Pedido de empréstimo indisponível.\n🪪 Primeiro conclua a verificação KYC.\nToque em « 🪪 Verificação KYC » no menu para continuar."

TEXT["fr"]["kyc"] = "🪪 Vérification KYC"
TEXT["en"]["kyc"] = "🪪 KYC Verification"
TEXT["es"]["kyc"] = "🪪 Verificación KYC"
TEXT["pt"]["kyc"] = "🪪 Verificação KYC"

TEXT["fr"]["kyc_pending"] = (
    "⏳ Votre vérification KYC est en cours.\n\n"
    "Veuillez patienter jusqu'à la décision de l'administrateur."
)
TEXT["en"]["kyc_pending"] = (
    "⏳ Your KYC verification is in progress.\n\n"
    "Please wait for the administrator's decision."
)
TEXT["es"]["kyc_pending"] = (
    "⏳ Su verificación KYC está en curso.\n\n"
    "Espere la decisión del administrador."
)
TEXT["pt"]["kyc_pending"] = (
    "⏳ Sua verificação KYC está em andamento.\n\n"
    "Aguarde a decisão do administrador."
)

TEXT["fr"]["kyc_photo_prompt"] = (
    "🪪 VÉRIFICATION KYC\n\n"
    "Envoyez une photo claire et lisible de votre document d'identité.\n\n"
    "⚠️ Le document doit être lisible et correspondre aux informations de votre inscription.\n\n"
    "📸 Envoyez maintenant la photo."
)
TEXT["en"]["kyc_photo_prompt"] = (
    "🪪 KYC VERIFICATION\n\n"
    "Send a clear and readable photo of your identity document.\n\n"
    "⚠️ The document must be readable and match your registration information.\n\n"
    "📸 Send the photo now."
)
TEXT["es"]["kyc_photo_prompt"] = (
    "🪪 VERIFICACIÓN KYC\n\n"
    "Envía una foto clara y legible de tu documento de identidad.\n\n"
    "⚠️ El documento debe ser legible y coincidir con la información de tu registro.\n\n"
    "📸 Envía ahora la foto."
)
TEXT["pt"]["kyc_photo_prompt"] = (
    "🪪 VERIFICAÇÃO KYC\n\n"
    "Envie uma foto clara e legível do seu documento de identidade.\n\n"
    "⚠️ O documento deve estar legível e corresponder às informações do seu cadastro.\n\n"
    "📸 Envie a foto agora."
)

TEXT["fr"]["loan_kyc_pending"] = (
    "⏳ Votre vérification KYC est en cours.\n\n"
    "Vous devez attendre sa validation avant de demander un prêt."
)
TEXT["en"]["loan_kyc_pending"] = (
    "⏳ Your KYC verification is in progress.\n\n"
    "You must wait for approval before requesting a loan."
)
TEXT["es"]["loan_kyc_pending"] = (
    "⏳ Su verificación KYC está en curso.\n\n"
    "Debe esperar su aprobación antes de solicitar un préstamo."
)
TEXT["pt"]["loan_kyc_pending"] = (
    "⏳ Sua verificação KYC está em andamento.\n\n"
    "Você deve aguardar a aprovação antes de solicitar um empréstimo."
)

TEXT["fr"]["loan_kyc_rejected"] = (
    "❌ Votre vérification KYC a été rejetée.\n\n"
    "Veuillez effectuer à nouveau votre KYC avant de demander un prêt."
)
TEXT["en"]["loan_kyc_rejected"] = (
    "❌ Your KYC verification was rejected.\n\n"
    "Please complete your KYC again before requesting a loan."
)
TEXT["es"]["loan_kyc_rejected"] = (
    "❌ Su verificación KYC fue rechazada.\n\n"
    "Complete nuevamente su KYC antes de solicitar un préstamo."
)
TEXT["pt"]["loan_kyc_rejected"] = (
    "❌ Sua verificação KYC foi rejeitada.\n\n"
    "Conclua novamente seu KYC antes de solicitar um empréstimo."
)

TEXT["fr"]["profile_missing"] = (
    "❌ Votre compte utilisateur est introuvable.\n\n"
    "Veuillez utiliser /start pour créer votre compte."
)
TEXT["en"]["profile_missing"] = (
    "❌ Your user account was not found.\n\n"
    "Please use /start to create your account."
)
TEXT["es"]["profile_missing"] = (
    "❌ No se encontró su cuenta de usuario.\n\n"
    "Utilice /start para crear su cuenta."
)
TEXT["pt"]["profile_missing"] = (
    "❌ Sua conta de usuário não foi encontrada.\n\n"
    "Use /start para criar sua conta."
)

    

TEXT["fr"]["loan_amount_prompt"] = (
    "💰 Entrez le montant du prêt souhaité en USDT.\n\n"
    "📌 Minimum : 500 USDT\n"
    "📌 Maximum : 50 000 USDT\n\n"
    "Exemple : 500"
)
TEXT["en"]["loan_amount_prompt"] = (
    "💰 Enter the desired loan amount in USDT.\n\n"
    "📌 Minimum: 500 USDT\n"
    "📌 Maximum: 50,000 USDT\n\n"
    "Example: 500"
)
TEXT["es"]["loan_amount_prompt"] = (
    "💰 Introduzca el importe del préstamo deseado en USDT.\n\n"
    "📌 Mínimo: 500 USDT\n"
    "📌 Máximo: 50.000 USDT\n\n"
    "Ejemplo: 500"
)
TEXT["pt"]["loan_amount_prompt"] = (
    "💰 Digite o valor do empréstimo desejado em USDT.\n\n"
    "📌 Mínimo: 500 USDT\n"
    "📌 Máximo: 50.000 USDT\n\n"
    "Exemplo: 500"
)

TEXT["fr"]["loan_amount_invalid"] = (
    "❌ Veuillez entrer uniquement un montant en USDT.\n\n"
    "Exemple : 500"
)
TEXT["en"]["loan_amount_invalid"] = (
    "❌ Please enter only a loan amount in USDT.\n\n"
    "Example: 500"
)
TEXT["es"]["loan_amount_invalid"] = (
    "❌ Introduzca únicamente un importe en USDT.\n\n"
    "Ejemplo: 500"
)
TEXT["pt"]["loan_amount_invalid"] = (
    "❌ Digite apenas um valor em USDT.\n\n"
    "Exemplo: 500"
)

TEXT["fr"]["loan_amount_min"] = (
    "❌ Demande refusée.\n\n"
    "Le montant minimum est de 500 USDT."
)
TEXT["en"]["loan_amount_min"] = (
    "❌ Request rejected.\n\n"
    "The minimum amount is 500 USDT."
)
TEXT["es"]["loan_amount_min"] = (
    "❌ Solicitud rechazada.\n\n"
    "El importe mínimo es de 500 USDT."
)
TEXT["pt"]["loan_amount_min"] = (
    "❌ Pedido recusado.\n\n"
    "O valor mínimo é de 500 USDT."
)

TEXT["fr"]["loan_amount_max"] = (
    "❌ Demande refusée.\n\n"
    "Le montant maximum est de 50 000 USDT."
)
TEXT["en"]["loan_amount_max"] = (
    "❌ Request rejected.\n\n"
    "The maximum amount is 50,000 USDT."
)
TEXT["es"]["loan_amount_max"] = (
    "❌ Solicitud rechazada.\n\n"
    "El importe máximo es de 50.000 USDT."
)
TEXT["pt"]["loan_amount_max"] = (
    "❌ Pedido recusado.\n\n"
    "O valor máximo é de 50.000 USDT."
)

TEXT["fr"]["loan_amount_accepted"] = (
    "✅ Montant accepté : {amount:g} USDT\n\n"
    "📅 CHOISISSEZ LA DURÉE DE REMBOURSEMENT\n\n"
    "📌 Minimum : 6 mois\n"
    "📌 Maximum : 44 mois\n\n"
    "Entrez un nombre entier entre 6 et 44.\n"
    "Exemple : 12"
)
TEXT["en"]["loan_amount_accepted"] = (
    "✅ Amount accepted: {amount:g} USDT\n\n"
    "📅 CHOOSE THE REPAYMENT PERIOD\n\n"
    "📌 Minimum: 6 months\n"
    "📌 Maximum: 44 months\n\n"
    "Enter a whole number between 6 and 44.\n"
    "Example: 12"
)
TEXT["es"]["loan_amount_accepted"] = (
    "✅ Importe aceptado: {amount:g} USDT\n\n"
    "📅 ELIJA EL PLAZO DE REEMBOLSO\n\n"
    "📌 Mínimo: 6 meses\n"
    "📌 Máximo: 44 meses\n\n"
    "Introduzca un número entero entre 6 y 44.\n"
    "Ejemplo: 12"
)
TEXT["pt"]["loan_amount_accepted"] = (
    "✅ Valor aceito: {amount:g} USDT\n\n"
    "📅 ESCOLHA O PRAZO DE REEMBOLSO\n\n"
    "📌 Mínimo: 6 meses\n"
    "📌 Máximo: 44 meses\n\n"
    "Digite um número inteiro entre 6 e 44.\n"
    "Exemplo: 12"
)


TEXT["fr"]["loan_network_prompt"] = (
    "✅ Montant accepté : {amount:g} USDT\n\n"
    "📊 Garantie indicative (15%) : {guarantee:g} USDT\n\n"
    "🌐 Choisissez le réseau de réception :"
)
TEXT["en"]["loan_network_prompt"] = (
    "✅ Amount accepted: {amount:g} USDT\n\n"
    "📊 Indicative guarantee (15%): {guarantee:g} USDT\n\n"
    "🌐 Choose the receiving network:"
)
TEXT["es"]["loan_network_prompt"] = (
    "✅ Importe aceptado: {amount:g} USDT\n\n"
    "📊 Garantía indicativa (15%): {guarantee:g} USDT\n\n"
    "🌐 Elija la red de recepción:"
)
TEXT["pt"]["loan_network_prompt"] = (
    "✅ Valor aceito: {amount:g} USDT\n\n"
    "📊 Garantia indicativa (15%): {guarantee:g} USDT\n\n"
    "🌐 Escolha a rede de recebimento:"
)


TEXT["fr"]["wallet_address_invalid"] = (
    "❌ Adresse {network} invalide.\n\n"
    "Veuillez entrer une adresse {network} valide.\n"
    "Exemple de format : {example}"
)
TEXT["en"]["wallet_address_invalid"] = (
    "❌ Invalid {network} address.\n\n"
    "Please enter a valid {network} address.\n"
    "Format example: {example}"
)
TEXT["es"]["wallet_address_invalid"] = (
    "❌ Dirección {network} no válida.\n\n"
    "Introduzca una dirección {network} válida.\n"
    "Ejemplo de formato: {example}"
)
TEXT["pt"]["wallet_address_invalid"] = (
    "❌ Endereço {network} inválido.\n\n"
    "Digite um endereço {network} válido.\n"
    "Exemplo de formato: {example}"
)


TEXT["fr"]["loan_final_summary"]=(
"📋 RÉCAPITULATIF FINAL\n\n"
"💰 Montant : {amount:g} USDT\n"
"📅 Durée : {duration} mois\n"
"📈 Intérêt : 1 % / mois\n"
"💵 Intérêts totaux : {interest:g} USDT\n"
"💳 Total à rembourser : {total:g} USDT\n"
"🧮 Mensualité : {monthly:.2f} USDT\n"
"📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
"🌐 Réseau : {network}\n"
"📍 Adresse de réception : {wallet}\n"
"📄 TXID : {txid}\n\n"
"⚠️ Le TXID sera vérifié manuellement.\n"
"⚠️ Aucune validation automatique du paiement n'est effectuée.\n\n"
"Souhaitez-vous confirmer la demande ?")
TEXT["en"]["loan_final_summary"]=(
"📋 FINAL SUMMARY\n\n"
"💰 Amount: {amount:g} USDT\n"
"📅 Duration: {duration} months\n"
"📈 Interest: 1% / month\n"
"💵 Total interest: {interest:g} USDT\n"
"💳 Total to repay: {total:g} USDT\n"
"🧮 Monthly payment: {monthly:.2f} USDT\n"
"📊 Indicative guarantee (15%): {guarantee:g} USDT\n"
"🌐 Network: {network}\n"
"📍 Receiving address: {wallet}\n"
"📄 TXID: {txid}\n\n"
"⚠️ The TXID will be checked manually.\n"
"⚠️ No automatic payment validation is performed.\n\n"
"Do you want to confirm the application?")
TEXT["es"]["loan_final_summary"]=(
"📋 RESUMEN FINAL\n\n"
"💰 Importe: {amount:g} USDT\n"
"📅 Duración: {duration} meses\n"
"📈 Interés: 1% / mes\n"
"💵 Intereses totales: {interest:g} USDT\n"
"💳 Total a reembolsar: {total:g} USDT\n"
"🧮 Pago mensual: {monthly:.2f} USDT\n"
"📊 Garantía indicativa (15%): {guarantee:g} USDT\n"
"🌐 Red: {network}\n"
"📍 Dirección de recepción: {wallet}\n"
"📄 TXID: {txid}\n\n"
"⚠️ El TXID será verificado manualmente.\n"
"⚠️ No se realiza ninguna validación automática del pago.\n\n"
"¿Desea confirmar la solicitud?")
TEXT["pt"]["loan_final_summary"]=(
"📋 RESUMO FINAL\n\n"
"💰 Valor: {amount:g} USDT\n"
"📅 Prazo: {duration} meses\n"
"📈 Juros: 1% / mês\n"
"💵 Juros totais: {interest:g} USDT\n"
"💳 Total a reembolsar: {total:g} USDT\n"
"🧮 Pagamento mensal: {monthly:.2f} USDT\n"
"📊 Garantia indicativa (15%): {guarantee:g} USDT\n"
"🌐 Rede: {network}\n"
"📍 Endereço de recebimento: {wallet}\n"
"📄 TXID: {txid}\n\n"
"⚠️ O TXID será verificado manualmente.\n"
"⚠️ Nenhuma validação automática do pagamento é realizada.\n\n"
"Deseja confirmar a solicitação?")


TEXT["fr"]["referral_message"] = (
    "🎁 MON PARRAINAGE\n\n"
    "👥 Filleuls inscrits : {count}\n"
    "💰 Récompenses potentielles : {total:g} USDT\n"
    "✅ Récompenses validées : {earned:g} USDT\n\n"
    "🔗 Votre lien personnel :\n{link}\n\n"
    "📌 Invitez vos amis avec ce lien.\n"
    "⏳ La récompense de 5 USDT est accordée lorsque "
    "les conditions du programme sont remplies."
)
TEXT["en"]["referral_message"] = (
    "🎁 MY REFERRALS\n\n"
    "👥 Registered referrals: {count}\n"
    "💰 Potential rewards: {total:g} USDT\n"
    "✅ Confirmed rewards: {earned:g} USDT\n\n"
    "🔗 Your personal link:\n{link}\n\n"
    "📌 Invite your friends using this link.\n"
    "⏳ The 5 USDT reward is granted when the program "
    "conditions are met."
)
TEXT["es"]["referral_message"] = (
    "🎁 MIS REFERIDOS\n\n"
    "👥 Referidos registrados: {count}\n"
    "💰 Recompensas potenciales: {total:g} USDT\n"
    "✅ Recompensas confirmadas: {earned:g} USDT\n\n"
    "🔗 Su enlace personal:\n{link}\n\n"
    "📌 Invite a sus amigos con este enlace.\n"
    "⏳ La recompensa de 5 USDT se concede cuando se cumplen "
    "las condiciones del programa."
)
TEXT["pt"]["referral_message"] = (
    "🎁 MINHAS INDICAÇÕES\n\n"
    "👥 Indicações registradas: {count}\n"
    "💰 Recompensas potenciais: {total:g} USDT\n"
    "✅ Recompensas confirmadas: {earned:g} USDT\n\n"
    "🔗 Seu link pessoal:\n{link}\n\n"
    "📌 Convide seus amigos usando este link.\n"
    "⏳ A recompensa de 5 USDT é concedida quando as condições "
    "do programa forem cumpridas."
)

TEXT["fr"]["history_empty"] = "📋 Vous n’avez encore aucune demande de prêt."
TEXT["en"]["history_empty"] = "📋 You do not have any loan application yet."
TEXT["es"]["history_empty"] = "📋 Aún no tiene ninguna solicitud de préstamo."
TEXT["pt"]["history_empty"] = "📋 Você ainda não tem nenhuma solicitação de empréstimo."

TEXT["fr"]["kyc_already_valid"] = (
    "✅ Votre KYC est déjà validé.\n\n"
    "Vous pouvez utiliser les fonctionnalités disponibles."
)
TEXT["en"]["kyc_already_valid"] = (
    "✅ Your KYC has already been approved.\n\n"
    "You can use the available features."
)
TEXT["es"]["kyc_already_valid"] = (
    "✅ Su KYC ya ha sido aprobado.\n\n"
    "Puede utilizar las funciones disponibles."
)
TEXT["pt"]["kyc_already_valid"] = (
    "✅ Seu KYC já foi aprovado.\n\n"
    "Você pode usar os recursos disponíveis."
)

TEXT["fr"]["existing_loan_message"] = (
    "⚠️ Vous avez déjà un prêt en cours.\n\n"
    "🆔 Prêt : #{loan_id}\n"
    "💰 Montant : {amount:g} USDT\n"
    "📌 Statut : {status}\n\n"
    "Vous ne pouvez pas demander un nouveau prêt "
    "tant que celui-ci n'est pas terminé.\n\n"
    "💳 Utilisez « Mon prêt en cours » pour consulter "
    "les informations de votre prêt."
)
TEXT["en"]["existing_loan_message"] = (
    "⚠️ You already have an active loan.\n\n"
    "🆔 Loan: #{loan_id}\n"
    "💰 Amount: {amount:g} USDT\n"
    "📌 Status: {status}\n\n"
    "You cannot request a new loan until this one is completed.\n\n"
    "💳 Use « My active loan » to view your loan information."
)
TEXT["es"]["existing_loan_message"] = (
    "⚠️ Ya tiene un préstamo activo.\n\n"
    "🆔 Préstamo: #{loan_id}\n"
    "💰 Importe: {amount:g} USDT\n"
    "📌 Estado: {status}\n\n"
    "No puede solicitar un nuevo préstamo hasta que este haya terminado.\n\n"
    "💳 Use « Mi préstamo activo » para consultar la información."
)
TEXT["pt"]["existing_loan_message"] = (
    "⚠️ Você já tem um empréstimo ativo.\n\n"
    "🆔 Empréstimo: #{loan_id}\n"
    "💰 Valor: {amount:g} USDT\n"
    "📌 Status: {status}\n\n"
    "Você não pode solicitar um novo empréstimo até que este seja concluído.\n\n"
    "💳 Use « Meu empréstimo ativo » para consultar as informações."
)

TEXT["fr"]["loan_already_in_progress"] = (
    "⚠️ Une demande de prêt est déjà en cours.\n\n"
    "Veuillez terminer la demande actuelle ou appuyer sur "
    "« ❌ Annuler » avant d'en commencer une nouvelle."
)
TEXT["en"]["loan_already_in_progress"] = (
    "⚠️ A loan application is already in progress.\n\n"
    "Please complete the current application or press "
    "« ❌ Cancel » before starting a new one."
)
TEXT["es"]["loan_already_in_progress"] = (
    "⚠️ Ya hay una solicitud de préstamo en curso.\n\n"
    "Complete la solicitud actual o pulse "
    "« ❌ Cancelar » antes de iniciar otra."
)
TEXT["pt"]["loan_already_in_progress"] = (
    "⚠️ Já existe uma solicitação de empréstimo em andamento.\n\n"
    "Conclua a solicitação atual ou pressione "
    "« ❌ Cancelar » antes de iniciar outra."
)

    
def _client_lang(update):
    try:
        return i18n_get_client_language(update.effective_user.id)
    except Exception:
        return "fr"

def _bt(update, key, **kwargs):
    lang = _client_lang(update)
    text = TEXT.get(lang, {}).get(key)
    if text is None:
        text = I18N_TEXT.get(lang, {}).get(key)
    if text is None:
        text = I18N_TEXT.get(lang, {}).get("generic_error")
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text



async def change_existing_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Change the saved language for an already registered client."""
    # --- CANAL PRIORITAIRE ---
    if context.user_data.get("channel_admin_mode"):
        from channel_manager import channel_admin_message
        await channel_admin_message(update, context)
        return
    user_id = update.effective_user.id
    mapping = {
        "🇫🇷 Français": "fr",
        "🇬🇧 English": "en",
        "🇪🇸 Español": "es",
        "🇵🇹 Português": "pt",
    }
    lang = mapping.get((update.message.text or "").strip())
    if not lang:
        await update.message.reply_text(i18n_tr(user_id, "language_invalid"), reply_markup=_registration_language_keyboard())
        return

    conn = db()
    try:
        conn.execute("UPDATE users SET language = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?", (lang, user_id))
        conn.commit()
    finally:
        conn.close()

    context.user_data["language"] = lang
    await update.message.reply_text(
        i18n_tr(user_id, "language_changed") + "\n\n" + TEXT[lang]["dashboard_menu"],
        reply_markup=dashboard_keyboard(lang, user_id),
    )

# =========================
# BASE DE DONNÉES
# =========================

def db():
    return sqlite3.connect(DB_PATH)


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


async def send_notification_once(
    bot,
    telegram_id,
    notification_type,
    reference_id,
    text,
):
    """
    Envoie une notification une seule fois pour une référence donnée.

    La table notification_log empêche les doublons.
    Si l'envoi Telegram échoue, l'entrée est supprimée afin
    que le bot puisse réessayer plus tard.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT OR IGNORE INTO notification_log
            (telegram_id, notification_type, reference_id)
            VALUES (?, ?, ?)
        """, (
            int(telegram_id),
            str(notification_type),
            str(reference_id),
        ))

        inserted = cur.rowcount
        conn.commit()

        # Notification déjà envoyée
        if inserted == 0:
            return False

        try:
            await bot.send_message(
                chat_id=int(telegram_id),
                text=text,
            )
            return True

        except Exception:
            # L'envoi a échoué : on autorise une nouvelle tentative.
            cur.execute("""
                DELETE FROM notification_log
                WHERE telegram_id = ?
                  AND notification_type = ?
                  AND reference_id = ?
            """, (
                int(telegram_id),
                str(notification_type),
                str(reference_id),
            ))
            conn.commit()
            raise

    finally:
        conn.close()



async def check_due_notifications(context):
    """
    Vérifie les échéances actives.
    Les notifications sont protégées par notification_log
    afin d'éviter les doublons.
    """

    try:
        now = __import__("datetime").datetime.now(
            timezone(timedelta(hours=1))
        )

        today = now.date()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
            SELECT
                li.id,
                li.loan_id,
                li.installment_number,
                li.due_date,
                li.amount,
                li.status,
                l.telegram_id,
                l.status
            FROM loan_installments li
            INNER JOIN loans l ON l.id = li.loan_id
            WHERE li.status = 'pending'
              AND l.status = 'active'
              AND li.due_date IS NOT NULL
        """)

        rows = cur.fetchall()
        conn.close()

        for row in rows:
            (
                installment_id,
                loan_id,
                installment_number,
                due_date_text,
                installment_amount,
                installment_status,
                telegram_id,
                loan_status,
            ) = row

            try:
                due_date = dt_date.fromisoformat(
                    str(due_date_text)[:10]
                )
            except Exception:
                print(
                    f"⚠️ Date d'échéance invalide "
                    f"pour l'échéance #{installment_id}"
                )
                continue

            days_until_due = (due_date - today).days

            notification_type = None
            message = None

            # Les rappels sont envoyés à partir de 09:00
            # afin d'éviter les messages nocturnes.
            if now.hour < 9:
                continue

            # =========================
            # 3 JOURS AVANT
            # =========================
            if days_until_due == 3:
                notification_type = "installment_due_3d"

                message = i18n_tr(
                    telegram_id, "due_3d", loan_id=loan_id,
                    installment_number=installment_number,
                    due_date=due_date.isoformat(),
                    amount=float(installment_amount),
                )

            # =========================
            # JOUR DE L'ÉCHÉANCE
            # =========================
            elif days_until_due == 0:
                notification_type = "installment_due_today"

                message = i18n_tr(
                    telegram_id, "due_today", loan_id=loan_id,
                    installment_number=installment_number,
                    amount=float(installment_amount),
                )

            # =========================
            # 1 JOUR DE RETARD
            # =========================
            elif days_until_due == -1:
                notification_type = "installment_overdue_1d"

                message = i18n_tr(
                    telegram_id, "due_overdue", loan_id=loan_id,
                    installment_number=installment_number,
                    due_date=due_date.isoformat(),
                    amount=float(installment_amount),
                )

            if not notification_type or not message:
                continue

            try:
                await send_notification_once(
                    bot=context.bot,
                    telegram_id=telegram_id,
                    notification_type=notification_type,
                    reference_id=str(installment_id),
                    text=message,
                )

            except Exception as e:
                print(
                    f"⚠️ Notification échéance impossible "
                    f"#{installment_id} : {e}"
                )

        print(
            f"🔔 Vérification des échéances terminée "
            f"({today.isoformat()})."
        )

    except Exception as e:
        print(f"❌ Erreur check_due_notifications : {e}")


def dashboard_keyboard(lang, user_id=None):
    t = TEXT[lang]

    rows = [
        [t["profile"], t["loan"]],
    ]

    # Afficher "Mon prêt en cours" dans la 2e ligne
    # uniquement lorsqu'un prêt approuvé/en cours existe.
    has_loan = False

    if user_id is not None:
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()

            cur.execute(
                """
                SELECT 1
                FROM loans
                WHERE telegram_id = ?
                  AND status NOT IN ('rejected', 'cancelled')
                ORDER BY id DESC
                LIMIT 1
                """,
                (user_id,)
            )

            has_loan = cur.fetchone() is not None
            conn.close()

        except Exception as e:
            print(f"⚠️ Vérification du prêt impossible : {e}")

    rows.append([t["tracking"]])

    if has_loan:
        rows.append([t["current_loan"], t["history"]])
    else:
        rows.append([t["history"]])

    rows.extend([
        [t["kyc"], t["referral"]],
        [t["support"], t["language"]],
    ])

    # Conditions & À-propos
    about_button = {
        "fr": t["about"],
        "en": "ℹ️ Terms & About",
        "es": "ℹ️ Condiciones y Acerca de",
        "pt": "ℹ️ Condições e Sobre",
    }.get(lang, t["about"])

    rows.append([about_button])

    if user_id == ADMIN_ID:
        rows.extend([["/enterprise", "/tickets"],["/ticket_close", "/repay"]])

    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
    )



# =========================
# INSCRIPTION — REPRISE AUTOMATIQUE
# =========================

def _registration_resume_state(context):
    d = context.user_data

    if not d.get("language"):
        return 1
    if not d.get("terms_accepted"):
        return 1
    if not d.get("first_name"):
        return 2
    if not d.get("last_name"):
        return 3
    if not d.get("country"):
        return 4
    if not d.get("phone"):
        return 5
    if not d.get("email"):
        return 6
    if not d.get("profession"):
        return 7
    if "photo_file_id" not in d:
        return 8
    if "trc20_address" not in d:
        return 9
    if "bep20_address" not in d:
        return 10

    return 10


def _registration_language_keyboard():
    return ReplyKeyboardMarkup(
        [
            [
                KeyboardButton("🇫🇷 Français"),
                KeyboardButton("🇬🇧 English")
            ],
            [
                KeyboardButton("🇪🇸 Español"),
                KeyboardButton("🇵🇹 Português")
            ],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


async def _registration_resume_prompt(update, context, state):

    message = update.effective_message
    lang = context.user_data.get("language", "fr")

    if state == 1:

        if not context.user_data.get("language"):

            await message.reply_text(
                "🌐 Veuillez choisir votre langue / Please choose your language :",
                reply_markup=_registration_language_keyboard(),
            )

        else:

            buttons = {
                "fr": "✅ Je suis d’accord",
                "en": "✅ I agree",
                "es": "✅ Estoy de acuerdo",
                "pt": "✅ Concordo",
            }

            reminder = {
                "fr": "📘 Vous avez commencé votre inscription. Cliquez sur le bouton ci-dessous pour accepter les conditions et continuer.",
                "en": "📘 You started your registration. Click the button below to accept the terms and continue.",
                "es": "📘 Ha comenzado su registro. Pulse el botón de abajo para aceptar las condiciones y continuar.",
                "pt": "📘 Você começou seu cadastro. Clique no botão abaixo para aceitar as condições e continuar.",
            }

            await message.reply_text(
                reminder.get(lang, reminder["fr"]),
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            buttons.get(lang, buttons["fr"]),
                            callback_data="terms_accept"
                        )
                    ]
                ]),
            )

    elif state == 2:
        await message.reply_text(TEXT[lang]["name"])

    elif state == 3:
        await message.reply_text(TEXT[lang]["lastname"])

    elif state == 4:
        await message.reply_text(TEXT[lang]["country"])

    elif state == 5:

        phone_labels = {
            "fr": "📱 Partager mon numéro",
            "en": "📱 Share my phone number",
            "es": "📱 Compartir mi número",
            "pt": "📱 Compartilhar meu número",
        }

        await message.reply_text(
            TEXT[lang]["phone"],
            reply_markup=ReplyKeyboardMarkup(
                [[
                    KeyboardButton(
                        phone_labels.get(
                            lang,
                            phone_labels["fr"]
                        ),
                        request_contact=True
                    )
                ]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )

    elif state == 6:
        await message.reply_text(TEXT[lang]["email"])

    elif state == 7:
        await message.reply_text(TEXT[lang]["profession"])

    elif state == 8:
        await message.reply_text(TEXT[lang]["photo"])

    elif state == 9:
        await message.reply_text(TEXT[lang]["trc20"])

    elif state == 10:
        await message.reply_text(TEXT[lang]["bep20"])


async def registration_invalid_input(update, context):

    state = _registration_resume_state(context)

    await _registration_resume_prompt(
        update,
        context,
        state
    )

    return state


async def registration_resume_entry(update, context):

    if update.callback_query:
        await update.callback_query.answer()

    return await start(update, context)

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    message = update.effective_message

    referral_code = None

    args = getattr(context, "args", None) or []

    if args:

        arg = args[0].strip()

        if arg.startswith("ref_"):
            referral_code = arg[4:].strip().lstrip("@")

    if referral_code:
        context.user_data["referral_code"] = referral_code

    existing = get_user(user_id)

    # =========================
    # COMPTE DÉJÀ TERMINÉ
    # =========================

    if existing:

        lang = get_language(user_id)

        await message.reply_text(
            TEXT[lang]["registered"]
            + "\n\n"
            + TEXT[lang]["dashboard_menu"],
            reply_markup=dashboard_keyboard(
                lang,
                update.effective_user.id
            ),
        )

        return ConversationHandler.END

    # =========================
    # INSCRIPTION INCOMPLÈTE
    # =========================

    if context.user_data and any(
        k in context.user_data
        for k in (
            "language",
            "terms_accepted",
            "first_name",
            "last_name",
            "country",
            "phone",
            "email",
            "profession",
            "photo_file_id",
            "trc20_address",
            "bep20_address",
            "referral_code",
        )
    ):

        state = _registration_resume_state(context)

        await _registration_resume_prompt(
            update,
            context,
            state
        )

        return state

    # =========================
    # NOUVELLE INSCRIPTION
    # =========================

    await message.reply_text(
        "👋 Welcome to Loan Request Assistant!\n\n"
        "🌍 Your multilingual assistant for USDT loan requests.\n\n"
        "💰 Submit your loan request\n"
        "🪪 Complete your verification\n"
        "📋 Track your applications\n"
        "🆘 Contact support when needed\n\n"
        "🌐 Please choose your language below to continue.",
        reply_markup=_registration_language_keyboard(),
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
        await update.message.reply_text(
            "🌐 Veuillez choisir une langue avec l’un des boutons ci-dessous.",
            reply_markup=_registration_language_keyboard(),
        )
        return 1

    context.user_data["language"] = lang
    context.user_data["terms_accepted"] = False

    terms = {
        "fr": (
            "📘 À PROPOS & CONDITIONS D’UTILISATION\n\n"
            "🌍 Loan Request Assistant permet de soumettre "
            "et de suivre une demande de prêt en USDT.\n\n"
            "💰 CONDITIONS PRINCIPALES\n"
            "• Montant : 500 à 50 000 USDT\n"
            "• Durée : 6 à 44 mois\n"
            "• Intérêt indiqué : 1 % par mois\n"
            "• Garantie indicative : 15 % du montant demandé\n\n"
            "🛡️ GARANTIE\n"
            "La garantie est un mécanisme de sécurité destiné "
            "notamment à limiter le risque de non-remboursement. "
            "Dans le cadre du programme, elle est prévue pour "
            "être restituée après le remboursement complet du prêt, "
            "conformément aux conditions du dossier.\n\n"
            "🔐 KYC\n"
            "La vérification KYC est obligatoire avant toute "
            "demande de prêt. Les informations et documents "
            "fournis doivent être exacts et lisibles.\n\n"
            "⚠️ IMPORTANT\n"
            "La soumission d'une demande ne garantit pas "
            "l'acceptation du prêt. Chaque dossier est soumis "
            "aux vérifications et conditions du programme.\n\n"
            "🔎 TRANSPARENCE\n"
            "Ces informations sont présentées avant l'inscription "
            "afin que vous puissiez prendre connaissance des "
            "principales conditions avant de continuer.\n\n"
            "En cliquant sur « ✅ Je suis d’accord », vous "
            "confirmez avoir lu et compris ces informations."
        ),

        "en": (
            "📘 ABOUT & TERMS OF USE\n\n"
            "🌍 Loan Request Assistant allows you to submit "
            "and track a USDT loan request.\n\n"
            "💰 MAIN CONDITIONS\n"
            "• Amount: 500 to 50,000 USDT\n"
            "• Duration: 6 to 44 months\n"
            "• Stated interest: 1% per month\n"
            "• Indicative guarantee: 15% of the requested amount\n\n"
            "🛡️ GUARANTEE\n"
            "The guarantee is a security mechanism intended, "
            "among other things, to limit the risk of non-repayment. "
            "Under the program, it is intended to be returned after "
            "the loan has been fully repaid, according to the terms "
            "of the loan file.\n\n"
            "🔐 KYC\n"
            "KYC verification is mandatory before submitting a loan "
            "request. The information and documents provided must "
            "be accurate and readable.\n\n"
            "⚠️ IMPORTANT\n"
            "Submitting a request does not guarantee loan approval. "
            "Each application is subject to the program's verification "
            "and conditions.\n\n"
            "🔎 TRANSPARENCY\n"
            "This information is presented before registration so "
            "you can review the main conditions before continuing.\n\n"
            "By clicking « ✅ I agree », you confirm that you have "
            "read and understood this information."
        ),

        "es": (
            "📘 INFORMACIÓN Y CONDICIONES DE USO\n\n"
            "🌍 Loan Request Assistant permite enviar y seguir "
            "una solicitud de préstamo en USDT.\n\n"
            "💰 CONDICIONES PRINCIPALES\n"
            "• Importe: 500 a 50.000 USDT\n"
            "• Duración: 6 a 44 meses\n"
            "• Interés indicado: 1 % mensual\n"
            "• Garantía indicativa: 15 % del importe solicitado\n\n"
            "🛡️ GARANTÍA\n"
            "La garantía es un mecanismo de seguridad destinado, "
            "entre otras cosas, a limitar el riesgo de impago. "
            "Según las condiciones del programa, está prevista "
            "su devolución después del reembolso completo del préstamo.\n\n"
            "🔐 KYC\n"
            "La verificación KYC es obligatoria antes de solicitar "
            "un préstamo. La información y los documentos deben "
            "ser exactos y legibles.\n\n"
            "⚠️ IMPORTANTE\n"
            "Enviar una solicitud no garantiza la aprobación del préstamo. "
            "Cada expediente está sujeto a las verificaciones y "
            "condiciones del programa.\n\n"
            "🔎 TRANSPARENCIA\n"
            "Esta información se presenta antes del registro para "
            "que pueda conocer las principales condiciones antes de continuar.\n\n"
            "Al pulsar « ✅ Estoy de acuerdo », confirma que ha "
            "leído y comprendido esta información."
        ),

        "pt": (
            "📘 SOBRE E CONDIÇÕES DE UTILIZAÇÃO\n\n"
            "🌍 O Loan Request Assistant permite enviar e acompanhar "
            "um pedido de empréstimo em USDT.\n\n"
            "💰 CONDIÇÕES PRINCIPAIS\n"
            "• Valor: 500 a 50.000 USDT\n"
            "• Prazo: 6 a 44 meses\n"
            "• Juros indicados: 1% por mês\n"
            "• Garantia indicativa: 15% do valor solicitado\n\n"
            "🛡️ GARANTIA\n"
            "A garantia é um mecanismo de segurança destinado, "
            "entre outras coisas, a limitar o risco de não pagamento. "
            "De acordo com as condições do programa, está prevista "
            "a sua devolução após o reembolso total do empréstimo.\n\n"
            "🔐 KYC\n"
            "A verificação KYC é obrigatória antes de solicitar um "
            "empréstimo. As informações e documentos fornecidos "
            "devem ser corretos e legíveis.\n\n"
            "⚠️ IMPORTANTE\n"
            "O envio de um pedido não garante a aprovação do empréstimo. "
            "Cada pedido está sujeito às verificações e condições do programa.\n\n"
            "🔎 TRANSPARÊNCIA\n"
            "Estas informações são apresentadas antes do registo para "
            "que possa conhecer as principais condições antes de continuar.\n\n"
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
            {
                "fr": "📱 Partager mon numéro",
                "en": "📱 Share my phone number",
                "es": "📱 Compartir mi número",
                "pt": "📱 Compartilhar meu número"
            }.get(get_language(update.effective_user.id), "📱 Partager mon numéro"),
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
                text=i18n_tr(
                    referred_by,
                    "referral_new_user",
                    name=user.first_name or "Client",
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
            referral_message = "\n\n" + i18n_tr(
                update.effective_user.id,
                "referral_linked",
                name=referrer_name,
            )
        else:
            referral_message = ""
    else:
        referral_message = ""

    await update.message.reply_text(
        TEXT[lang]["done"] + referral_message + "\n\n" +
        TEXT[lang]["dashboard_menu"],
        reply_markup=dashboard_keyboard(lang, update.effective_user.id),
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
# MON PRÊT EN COURS
# =========================

async def my_loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    lang = get_language(user_id)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            loan_request_id,
            amount,
            interest_rate,
            total_repayment,
            monthly_payment,
            duration_months,
            status,
            disbursement_status,
            disbursement_network,
            disbursement_amount,
            disbursement_txid,
            disbursement_date,
            amount_repaid,
            installments_paid,
            next_due_date
        FROM loans
        WHERE telegram_id = ?
          AND status NOT IN ('rejected', 'cancelled')
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )

    loan = cur.fetchone()
    conn.close()

    if not loan:
        await update.message.reply_text(
            _bt(update, "no_approved_loan"),
            reply_markup=dashboard_keyboard(lang, user_id),
        )
        return

    (
        loan_id,
        request_id,
        amount,
        interest_rate,
        total_repayment,
        monthly_payment,
        duration_months,
        status,
        disbursement_status,
        disbursement_network,
        disbursement_amount,
        disbursement_txid,
        disbursement_date,
        amount_repaid,
        installments_paid,
        next_due_date,
    ) = loan

    amount_repaid = amount_repaid or 0
    installments_paid = installments_paid or 0
    remaining = max(total_repayment - amount_repaid, 0)

    status_labels = {
        "fr": {
            "approved": "✅ Approuvé",
            "active": "🟢 Actif",
            "completed": "🏁 Terminé",
            "pending": "⏳ En attente",
            "rejected": "❌ Rejeté",
            "cancelled": "🚫 Annulé",
        },
        "en": {
            "approved": "✅ Approved",
            "active": "🟢 Active",
            "completed": "🏁 Completed",
            "pending": "⏳ Pending",
            "rejected": "❌ Rejected",
            "cancelled": "🚫 Cancelled",
        },
        "es": {
            "approved": "✅ Aprobado",
            "active": "🟢 Activo",
            "completed": "🏁 Completado",
            "pending": "⏳ Pendiente",
            "rejected": "❌ Rechazado",
            "cancelled": "🚫 Cancelado",
        },
        "pt": {
            "approved": "✅ Aprovado",
            "active": "🟢 Ativo",
            "completed": "🏁 Concluído",
            "pending": "⏳ Pendente",
            "rejected": "❌ Rejeitado",
            "cancelled": "🚫 Cancelado",
        },
    }

    status_labels = status_labels.get(lang, status_labels["fr"])

    loan_status = status_labels.get(
        str(status).lower(),
        str(status or "Inconnu")
    )

    if disbursement_txid or str(disbursement_status).lower() in (
        "disbursed",
        "sent",
        "completed",
    ):
        disbursement_labels = {
            "fr": "✅ Décaissement enregistré",
            "en": "✅ Disbursement recorded",
            "es": "✅ Desembolso registrado",
            "pt": "✅ Desembolso registrado",
        }
        disbursement_label = disbursement_labels.get(
            lang, disbursement_labels["fr"]
        )
    else:
        disbursement_labels = {
            "fr": "⏳ Décaissement en attente de confirmation administrative",
            "en": "⏳ Disbursement awaiting administrative confirmation",
            "es": "⏳ Desembolso pendiente de confirmación administrativa",
            "pt": "⏳ Desembolso aguardando confirmação administrativa",
        }
        disbursement_label = disbursement_labels.get(
            lang, disbursement_labels["fr"]
        )
    texts = {
        "fr": (
            "💳 MON PRÊT EN COURS\n\n"
            f"🆔 Demande : #{request_id}\n"
            f"💰 Montant du prêt : {amount:g} USDT\n"
            f"📈 Taux : {interest_rate:g} % / mois\n"
            f"💳 Total à rembourser : {total_repayment:.2f} USDT\n"
            f"🧮 Mensualité : {monthly_payment:.2f} USDT\n"
            f"📅 Durée : {duration_months} mois\n\n"
            f"💵 Déjà remboursé : {amount_repaid:.2f} USDT\n"
            f"💰 Reste à rembourser : {remaining:.2f} USDT\n"
            f"🔢 Échéances payées : {installments_paid}/{duration_months}\n"
            f"📅 Prochaine échéance : {next_due_date or 'Non définie'}\n\n"
            f"📌 Statut du prêt : {loan_status}\n"
            f"📤 Décaissement : {disbursement_label}\n"
        ),
        "en": (
            "💳 MY ACTIVE LOAN\n\n"
            f"🆔 Loan request: #{request_id}\n"
            f"💰 Loan amount: {amount:g} USDT\n"
            f"📈 Rate: {interest_rate:g}% / month\n"
            f"💳 Total to repay: {total_repayment:.2f} USDT\n"
            f"🧮 Monthly installment: {monthly_payment:.2f} USDT\n"
            f"📅 Duration: {duration_months} months\n\n"
            f"💵 Already repaid: {amount_repaid:.2f} USDT\n"
            f"💰 Remaining: {remaining:.2f} USDT\n"
            f"🔢 Installments paid: {installments_paid}/{duration_months}\n"
            f"📅 Next installment: {next_due_date or 'Not defined'}\n\n"
            f"📌 Loan status: {loan_status}\n"
            f"📤 Disbursement: {disbursement_label}\n"
        ),
        "es": (
            "💳 MI PRÉSTAMO ACTIVO\n\n"
            f"🆔 Solicitud: #{request_id}\n"
            f"💰 Importe del préstamo: {amount:g} USDT\n"
            f"📈 Tasa: {interest_rate:g}% / mes\n"
            f"💳 Total a reembolsar: {total_repayment:.2f} USDT\n"
            f"🧮 Pago mensual: {monthly_payment:.2f} USDT\n"
            f"📅 Duración: {duration_months} meses\n\n"
            f"💵 Ya reembolsado: {amount_repaid:.2f} USDT\n"
            f"💰 Restante por reembolsar: {remaining:.2f} USDT\n"
            f"🔢 Cuotas pagadas: {installments_paid}/{duration_months}\n"
            f"📅 Próxima cuota: {next_due_date or 'No definida'}\n\n"
            f"📌 Estado del préstamo: {loan_status}\n"
            f"📤 Desembolso: {disbursement_label}\n"
        ),
        "pt": (
            "💳 MEU EMPRÉSTIMO ATIVO\n\n"
            f"🆔 Solicitação: #{request_id}\n"
            f"💰 Valor do empréstimo: {amount:g} USDT\n"
            f"📈 Taxa: {interest_rate:g}% / mês\n"
            f"💳 Total a reembolsar: {total_repayment:.2f} USDT\n"
            f"🧮 Pagamento mensal: {monthly_payment:.2f} USDT\n"
            f"📅 Duração: {duration_months} meses\n\n"
            f"💵 Já reembolsado: {amount_repaid:.2f} USDT\n"
            f"💰 Restante a reembolsar: {remaining:.2f} USDT\n"
            f"🔢 Parcelas pagas: {installments_paid}/{duration_months}\n"
            f"📅 Próxima parcela: {next_due_date or 'Não definida'}\n\n"
            f"📌 Status do empréstimo: {loan_status}\n"
            f"📤 Desembolso: {disbursement_label}\n"
        )
    }

    text = texts.get(lang, texts["fr"])

    extra_texts = {
        "fr": {
            "network": "🌐 Réseau de décaissement",
            "recorded": "💸 Montant enregistré",
            "txid": "📄 TXID du décaissement",
            "date": "🕐 Date du décaissement",
            "warning": "⚠️ Le bot n'effectue aucun transfert automatiquement.",
            "confirmation": "Les informations de décaissement sont enregistrées après confirmation administrative.",
            "schedule": "📅 Voir l'échéancier",
        },
        "en": {
            "network": "🌐 Disbursement network",
            "recorded": "💸 Recorded amount",
            "txid": "📄 Disbursement TXID",
            "date": "🕐 Disbursement date",
            "warning": "⚠️ The bot does not perform automatic transfers.",
            "confirmation": "Disbursement information is recorded after administrative confirmation.",
            "schedule": "📅 View repayment schedule",
        },
        "es": {
            "network": "🌐 Red de desembolso",
            "recorded": "💸 Importe registrado",
            "txid": "📄 TXID del desembolso",
            "date": "🕐 Fecha del desembolso",
            "warning": "⚠️ El bot no realiza transferencias automáticamente.",
            "confirmation": "La información del desembolso se registra después de la confirmación administrativa.",
            "schedule": "📅 Ver calendario de pagos",
        },
        "pt": {
            "network": "🌐 Rede de desembolso",
            "recorded": "💸 Valor registrado",
            "txid": "📄 TXID do desembolso",
            "date": "🕐 Data do desembolso",
            "warning": "⚠️ O bot não realiza transferências automaticamente.",
            "confirmation": "As informações do desembolso são registradas após confirmação administrativa.",
            "schedule": "📅 Ver calendário de pagamentos",
        },
    }

    et = extra_texts.get(lang, extra_texts["fr"])

    if disbursement_network:
        text += f"{et['network']} : {disbursement_network}\n"

    if disbursement_amount is not None:
        text += f"{et['recorded']} : {disbursement_amount:g} USDT\n"

    if disbursement_txid:
        text += f"{et['txid']} : {disbursement_txid}\n"

    if disbursement_date:
        text += f"{et['date']} : {disbursement_date}\n"

    text += (
        f"\n{et['warning']}\n"
        f"{et['confirmation']}"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                et["schedule"],
                callback_data=f"loan_schedule:{loan_id}:0"
            )
        ]
    ])

    await update.message.reply_text(
        text,
        reply_markup=keyboard
    )


async def loan_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche l'étape actuelle et l'historique du dernier dossier du client."""
    user_id = update.effective_user.id
    lang = get_language(user_id)

    stage_labels = {
        "fr": {
            "received": "📥 Demande reçue",
            "verification": "🔍 Vérification du profil",
            "kyc_pending": "🪪 KYC en cours",
            "kyc_approved": "🟢 KYC validé",
            "kyc_rejected": "❌ KYC rejeté",
            "analysis": "📋 Analyse du dossier",
            "approved": "✅ Demande approuvée",
            "disbursement": "💸 Décaissement en cours",
            "disbursed": "💰 Décaissement effectué",
            "rejected": "❌ Demande rejetée",
            "completed": "🏁 Remboursement terminé",
        },
        "en": {
            "received": "📥 Application received",
            "verification": "🔍 Profile verification",
            "kyc_pending": "🪪 KYC in progress",
            "kyc_approved": "🟢 KYC approved",
            "analysis": "📋 Application under review",
            "approved": "✅ Application approved",
            "disbursement": "💸 Disbursement in progress",
            "disbursed": "💰 Disbursement completed",
            "rejected": "❌ Application rejected",
            "completed": "🏁 Repayment completed",
        },
        "es": {
            "received": "📥 Solicitud recibida",
            "verification": "🔍 Verificación del perfil",
            "kyc_pending": "🪪 KYC en curso",
            "kyc_approved": "🟢 KYC aprobado",
            "analysis": "📋 Solicitud en análisis",
            "approved": "✅ Solicitud aprobada",
            "disbursement": "💸 Desembolso en curso",
            "disbursed": "💰 Desembolso efectuado",
            "rejected": "❌ Solicitud rechazada",
            "completed": "🏁 Reembolso terminado",
        },
        "pt": {
            "received": "📥 Pedido recebido",
            "verification": "🔍 Verificação do perfil",
            "kyc_pending": "🪪 KYC em curso",
            "kyc_approved": "🟢 KYC aprovado",
            "analysis": "📋 Pedido em análise",
            "approved": "✅ Pedido aprovado",
            "disbursement": "💸 Desembolso em curso",
            "disbursed": "💰 Desembolso efetuado",
            "rejected": "❌ Pedido rejeitado",
            "completed": "🏁 Reembolso concluído",
        },
    }
    labels = stage_labels.get(lang, stage_labels["fr"])

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, amount, status, current_stage, stage_updated_at, created_at
        FROM loan_requests
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,),
    )
    request = cur.fetchone()

    if not request:
        conn.close()
        await update.message.reply_text(
            _bt(update, "no_requests"),
            reply_markup=dashboard_keyboard(lang, user_id),
        )
        return

    request_id, amount, request_status, current_stage, stage_updated_at, created_at = request
    current_stage = current_stage or "received"

    cur.execute(
        """
        SELECT stage, note, changed_by, created_at
        FROM loan_stage_history
        WHERE loan_request_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (request_id,),
    )
    history = cur.fetchall()
    conn.close()

    # Les étapes principales restent dans l'ordre demandé par le système.
    ordered = [
        "received",
        "verification",
        "kyc_pending",
        "kyc_approved",
        "analysis",
        "approved",
        "disbursement",
        "disbursed",
    ]

    if current_stage == "kyc_rejected":
        checklist = [
            "🟢 " + labels["received"],
            "🟢 " + labels["verification"],
            "❌ " + labels["kyc_rejected"],
        ]
    elif current_stage == "rejected":
        checklist = [
            "🟢 " + labels["received"],
            "🟢 " + labels["verification"],
            "🟢 " + labels["kyc_pending"],
            "🟢 " + labels["kyc_approved"],
            "🟢 " + labels["analysis"],
            "❌ " + labels["rejected"],
        ]
    elif current_stage == "completed":
        checklist = [
            "🟢 " + labels[stage] for stage in ordered
        ] + ["🟢 " + labels["completed"]]
    else:
        try:
            current_index = ordered.index(current_stage)
        except ValueError:
            current_index = 0

        checklist = []
        for index, stage in enumerate(ordered):
            if index < current_index:
                prefix = "🟢"
            elif index == current_index:
                prefix = "🟡"
            else:
                prefix = "⚪"
            checklist.append(f"{prefix} {labels[stage]}")

    status_label = labels.get(current_stage, str(request_status or current_stage))
    text = (
        "📊 ÉTAT DE MON DOSSIER\n\n"
        f"🆔 Demande : #{request_id}\n"
        f"💰 Montant : {float(amount):g} USDT\n\n"
        "📌 Étape actuelle :\n"
        + "\n".join(checklist)
        + "\n\n"
        f"📅 Dernière mise à jour :\n{stage_updated_at or created_at or '-'}\n\n"
        f"ℹ️ Statut : {status_label}"
    )

    if history:
        text += "\n\n🕘 HISTORIQUE\n"
        for stage, note, changed_by, created_at in reversed(history):
            label = labels.get(stage, stage)
            suffix = f" — {note}" if note else ""
            text += f"{created_at or '-'} — {label}{suffix}\n"

    await update.message.reply_text(
        text,
        reply_markup=dashboard_keyboard(lang, user_id),
    )


async def loan_schedule_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    parts = query.data.split(":")

    if len(parts) != 3:
        await query.answer("❌ Données invalides.", show_alert=True)
        return

    try:
        loan_id = int(parts[1])
        page = max(int(parts[2]), 0)
    except ValueError:
        await query.answer("❌ Données invalides.", show_alert=True)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, amount, duration_months
        FROM loans
        WHERE id = ?
          AND telegram_id = ?
        """,
        (loan_id, user_id)
    )

    loan = cur.fetchone()

    if not loan:
        conn.close()
        await query.edit_message_text(
            _bt(update, "loan_not_associated")
        )
        return

    cur.execute(
        """
        SELECT
            installment_number,
            due_date,
            amount,
            status,
            paid_at,
            payment_txid
        FROM loan_installments
        WHERE loan_id = ?
        ORDER BY installment_number ASC
        """,
        (loan_id,)
    )

    installments = cur.fetchall()
    conn.close()

    if not installments:
        await query.edit_message_text(
            "📅 ÉCHÉANCIER\n\n"
            "Aucune échéance n'est encore enregistrée.",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💳 Retour à mon prêt",
                        callback_data=f"loan_current:{loan_id}"
                    )
                ]
            ])
        )
        return

    per_page = 8
    total_pages = (len(installments) + per_page - 1) // per_page
    page = min(page, total_pages - 1)

    start = page * per_page
    end = min(start + per_page, len(installments))
    current = installments[start:end]

    text = (
        "📅 ÉCHÉANCIER DU PRÊT\n\n"
        f"💰 Montant initial : {loan[1]:g} USDT\n"
        f"📊 Échéances : {len(installments)}\n"
        f"📄 Page {page + 1}/{total_pages}\n\n"
    )

    for number, due_date, installment_amount, inst_status, paid_at, payment_txid in current:
        status_label = {
            "pending": "⏳ En attente",
            "paid": "✅ Payée",
            "late": "⚠️ En retard",
            "cancelled": "🚫 Annulée",
        }.get(
            str(inst_status).lower(),
            str(inst_status or "Inconnu")
        )

        text += (
            f"#{number} — {installment_amount:.2f} USDT\n"
            f"📆 Échéance : {due_date or 'Non définie'}\n"
            f"📌 Statut : {status_label}\n"
        )

        if paid_at:
            text += f"🕐 Payée le : {paid_at}\n"

        if payment_txid:
            text += f"📄 TXID : {payment_txid}\n"

        text += "\n"

    buttons = []

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Précédent",
                callback_data=f"loan_schedule:{loan_id}:{page - 1}"
            )
        )

    if page < total_pages - 1:
        navigation.append(
            InlineKeyboardButton(
                "Suivant ➡️",
                callback_data=f"loan_schedule:{loan_id}:{page + 1}"
            )
        )

    if navigation:
        buttons.append(navigation)

    buttons.append([
        InlineKeyboardButton(
            "💳 Retour à mon prêt",
            callback_data=f"loan_current:{loan_id}"
        )
    ])

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def loan_current_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    try:
        loan_id = int(query.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.answer("❌ Prêt invalide.", show_alert=True)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            loan_request_id,
            amount,
            interest_rate,
            total_repayment,
            monthly_payment,
            duration_months,
            status,
            disbursement_status,
            disbursement_network,
            disbursement_amount,
            disbursement_txid,
            disbursement_date,
            amount_repaid,
            installments_paid,
            next_due_date
        FROM loans
        WHERE id = ?
          AND telegram_id = ?
        """,
        (loan_id, user_id)
    )

    loan = cur.fetchone()
    conn.close()

    if not loan:
        await query.edit_message_text(
            _bt(update, "loan_not_associated")
        )
        return

    (
        loan_id,
        request_id,
        amount,
        interest_rate,
        total_repayment,
        monthly_payment,
        duration_months,
        status,
        disbursement_status,
        disbursement_network,
        disbursement_amount,
        disbursement_txid,
        disbursement_date,
        amount_repaid,
        installments_paid,
        next_due_date,
    ) = loan

    amount_repaid = amount_repaid or 0
    installments_paid = installments_paid or 0
    remaining = max(total_repayment - amount_repaid, 0)

    if disbursement_txid or str(disbursement_status).lower() in (
        "disbursed",
        "sent",
        "completed",
    ):
        disbursement_label = "✅ Décaissement enregistré"
    else:
        disbursement_label = "⏳ Décaissement en attente de confirmation administrative"

    status_label = {
        "approved": "✅ Approuvé",
        "active": "🟢 Actif",
        "completed": "🏁 Terminé",
        "pending": "⏳ En attente",
    }.get(
        str(status).lower(),
        str(status or "Inconnu")
    )

    text = (
        "💳 MON PRÊT EN COURS\n\n"
        f"🆔 Demande : #{request_id}\n"
        f"💰 Montant du prêt : {amount:g} USDT\n"
        f"📈 Taux : {interest_rate:g} % / mois\n"
        f"💳 Total à rembourser : {total_repayment:.2f} USDT\n"
        f"🧮 Mensualité : {monthly_payment:.2f} USDT\n"
        f"📅 Durée : {duration_months} mois\n\n"
        f"💵 Déjà remboursé : {amount_repaid:.2f} USDT\n"
        f"💰 Reste à rembourser : {remaining:.2f} USDT\n"
        f"🔢 Échéances payées : {installments_paid}/{duration_months}\n"
        f"📆 Prochaine échéance : {next_due_date or 'Non définie'}\n\n"
        f"📌 Statut : {status_label}\n"
        f"📤 Décaissement : {disbursement_label}\n"
    )

    if disbursement_network:
        text += f"🌐 Réseau : {disbursement_network}\n"

    if disbursement_amount is not None:
        text += f"💸 Montant enregistré : {disbursement_amount:g} USDT\n"

    if disbursement_txid:
        text += f"📄 TXID : {disbursement_txid}\n"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📅 Voir l'échéancier",
                callback_data=f"loan_schedule:{loan_id}:0"
            )
        ]
    ])

    await query.edit_message_text(
        text,
        reply_markup=keyboard
    )


# =========================
# TABLEAU DE BORD
# =========================

async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from channel_manager import is_awaiting, channel_admin_message
        if is_awaiting(update.effective_user.id):
            await channel_admin_message(update, context)
            return
    except: pass

    try:
        from channel_manager import is_awaiting, channel_admin_message
        if is_awaiting(update.effective_user.id):
            await channel_admin_message(update, context)
            return
    except Exception as e:
        print(f'[CANAL] {e}')

    if context.user_data.get("awaiting_network"):
        await update.message.reply_text(
            _bt(update, "network_select")
        )
        return


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
    {
        "fr": "✅ Confirmer la demande",
        "en": "✅ Confirm application",
        "es": "✅ Confirmar la solicitud",
        "pt": "✅ Confirmar a solicitação"
    }.get(get_language(update.effective_user.id), "fr"),
    callback_data="loan_confirm"
)
            ],
            [
                InlineKeyboardButton(
                    _bt(update, "cancel_button"),
                    callback_data="loan_cancel"
                )
            ]
        ])

        await update.message.reply_text(
                _bt(update,"loan_final_summary",
                    amount=amount,duration=duration,interest=interest,
                    total=total_repayment,monthly=monthly_payment,
                    guarantee=guarantee,network=network,wallet=wallet,txid=txid),
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
                _bt(
                    update,
                    "wallet_address_invalid",
                    network=network,
                    example=example,
                )
            )
            return

        context.user_data["wallet_address"] = address
        context.user_data["awaiting_wallet_address"] = False

        amount = context.user_data.get("loan_amount", 0)
        duration = context.user_data.get("loan_duration", 0)
        interest = context.user_data.get("interest", 0)
        total_repayment = context.user_data.get("total_repayment", 0)
        monthly_payment = context.user_data.get("monthly_payment", 0)
        guarantee = amount * 0.15

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                _bt(update, "accept_conditions_button"),
                callback_data="loan_conditions_accept"
            )
            ],
            [
                InlineKeyboardButton(
                    _bt(update, "cancel_button"),
                    callback_data="loan_cancel"
                )
            ]
        ])

        await update.message.reply_text(
                _bt(update, "loan_conditions").format(
                    amount=amount,
                    duration=duration,
                    interest=interest,
                    total=total_repayment,
                    monthly=monthly_payment,
                    guarantee=guarantee,
                    network=network,
                    address=address,
                ),
                reply_markup=keyboard
            )
        return

    # TRAITEMENT AUTOMATIQUE DU MONTANT DU PRET
    if context.user_data.get("awaiting_loan_duration"):
        try:
            months = int(text.strip())
        except ValueError:
            await update.message.reply_text(_bt(update, "duration_invalid"))
            return

        if months < 6 or months > 44:
            await update.message.reply_text(_bt(update, "duration_out_of_range"))
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
        context.user_data["awaiting_network"] = True

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔵 TRC20", callback_data="loan_network_trc20"),
                InlineKeyboardButton("🟡 BEP20", callback_data="loan_network_bep20")
            ]
        ])

        await update.message.reply_text(
            _bt(update, "loan_network_selection").format(
                amount=amount, duration=months, interest=interest,
                total=total_repayment, monthly=monthly_payment,
                guarantee=guarantee,
            ),
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
            await update.message.reply_text(_bt(update, "loan_amount_min"))
            return

        if amount > 50000:
            await update.message.reply_text(_bt(update, "loan_amount_max"))
            return

        context.user_data["loan_amount"] = amount
        context.user_data["awaiting_loan_amount"] = False
        context.user_data["awaiting_loan_duration"] = True

        await update.message.reply_text(
            _bt(update, "loan_amount_accepted", amount=amount)
        )
        return

        guarantee = amount * 0.15

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔵 TRC20", callback_data="loan_network_trc20"),
                InlineKeyboardButton("🟡 BEP20", callback_data="loan_network_bep20")
            ]
        ])

        await update.message.reply_text(
            _bt(update, "loan_network_prompt").format(
                amount=amount,
                guarantee=guarantee,
            ),
            reply_markup=keyboard
        )
        return


    if text == t["referral"]:
        user = get_user(user_id)

        if user is None:
            await update.message.reply_text(
                _bt(update, "profile_missing"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        {
                            "fr": "📝 Continuer mon inscription",
                            "en": "📝 Continue my registration",
                            "es": "📝 Continuar mi registro",
                            "pt": "📝 Continuar meu cadastro",
                        }.get(
                            lang,
                            "📝 Continuer mon inscription"
                        ),
                        callback_data="registration_resume",
                    )
                ]]),
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
            _bt(update, "referral_message").format(
                count=referral_count,
                total=total_rewards,
                earned=earned_rewards,
                link=link,
            )
        )

    elif text == t["profile"]:

        user = get_user(user_id)

        if user is None:
            await update.message.reply_text(
                _bt(update, "profile_missing"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        {
                            "fr": "📝 Continuer mon inscription",
                            "en": "📝 Continue my registration",
                            "es": "📝 Continuar mi registro",
                            "pt": "📝 Continuar meu cadastro",
                        }.get(
                            lang,
                            "📝 Continuer mon inscription"
                        ),
                        callback_data="registration_resume",
                    )
                ]]),
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
                _bt(update, "profile_missing"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        {
                            "fr": "📝 Continuer mon inscription",
                            "en": "📝 Continue my registration",
                            "es": "📝 Continuar mi registro",
                            "pt": "📝 Continuar meu cadastro",
                        }.get(
                            lang,
                            "📝 Continuer mon inscription"
                        ),
                        callback_data="registration_resume",
                    )
                ]]),
            )
            return

        status = user[13] or "not_submitted"

        if status == "approved":
            await update.message.reply_text(
                _bt(update, "kyc_already_valid")
            )

        elif status == "pending":
            await update.message.reply_text(
                _bt(update, "kyc_pending")
            )

        else:
            context.user_data["awaiting_kyc_photo"] = True

            await update.message.reply_text(
                _bt(update, "kyc_photo_prompt")
            )

        return

    elif text == t["loan"]:
        user = get_user(user_id)

        if user is None:
            await update.message.reply_text(
                _bt(update, "profile_missing"),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        {
                            "fr": "📝 Continuer mon inscription",
                            "en": "📝 Continue my registration",
                            "es": "📝 Continuar mi registro",
                            "pt": "📝 Continuar meu cadastro",
                        }.get(
                            lang,
                            "📝 Continuer mon inscription"
                        ),
                        callback_data="registration_resume",
                    )
                ]]),
            )
            return

        kyc_status = user[13] or "not_submitted"

        if kyc_status != "approved":
            if kyc_status == "pending":
                message = _bt(update, "loan_kyc_pending")
            elif kyc_status == "rejected":
                message = _bt(update, "loan_kyc_rejected")
            else:
                message = _bt(update, "loan_kyc_required")

            await update.message.reply_text(message)
            return

        # Vérifier si le client possède déjà un prêt approuvé ou actif.
        # Un prêt terminé n'empêche pas une nouvelle demande.
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, amount, status
            FROM loans
            WHERE telegram_id = ?
              AND status IN ('approved', 'active')
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id,)
        )

        existing_loan = cur.fetchone()
        conn.close()

        if existing_loan:
            existing_loan_id, existing_amount, existing_status = existing_loan

            status_label = (
                "✅ approuvé"
                if str(existing_status).lower() == "approved"
                else "🟢 actif"
            )

            await update.message.reply_text(
                _bt(
                    update,
                    "existing_loan_message",
                    loan_id=existing_loan_id,
                    amount=existing_amount,
                    status=status_label,
                )
            )
            return

        # Empêcher de démarrer une deuxième demande pendant qu'une demande est déjà en cours.
        active_loan_steps = (
            "awaiting_loan_amount",
            "awaiting_loan_duration",
            "awaiting_network",
            "awaiting_wallet_address",
            "awaiting_loan_txid",
        )

        if (context.user_data.get("loan_flow_active") or any(context.user_data.get(step) for step in active_loan_steps)):
            await update.message.reply_text(
                "⚠️ Une demande de prêt est déjà en cours.\n\n"
                "Veuillez terminer la demande actuelle ou appuyer sur "
                "« ❌ Annuler » avant d'en commencer une nouvelle."
            )
            return

        context.user_data["loan_flow_active"] = True
        context.user_data["awaiting_loan_amount"] = True

        await update.message.reply_text(_bt(update, "loan_amount_prompt"))
        return

    elif text == t["tracking"]:
        await loan_tracking(update, context)

    elif text == t["history"]:

        # L'historique détaillé des demandes sera affiché dans le suivi du dossier.
        await loan_tracking(update, context)


    # =====================================================
    # CONDITIONS & À-PROPOS
    # =====================================================

    about_button_text = {
        "fr": t["about"],
        "en": "ℹ️ Terms & About",
        "es": "ℹ️ Condiciones y Acerca de",
        "pt": "ℹ️ Condições e Sobre",
    }.get(lang, t["about"])

    if text == about_button_text:

        about_texts = {
            "fr": """🌍 GLOBAL USDT FINANCE

ℹ️ CONDITIONS & À-PROPOS

━━━━━━━━━━━━━━━━━━
🔹 1. À PROPOS
━━━━━━━━━━━━━━━━━━

Global USDT Finance est le nom utilisé par ce service pour la gestion des demandes de financement en USDT.

Cette section présente le fonctionnement du service, les règles de sécurité et les informations importantes à connaître avant toute opération.

━━━━━━━━━━━━━━━━━━
🔹 2. COMMENT ÇA FONCTIONNE ?
━━━━━━━━━━━━━━━━━━

1️⃣ Créez votre profil dans le bot.

2️⃣ Complétez la vérification KYC lorsqu'elle est demandée.

3️⃣ Soumettez votre demande de financement.

4️⃣ Votre demande est examinée.

5️⃣ Si elle est approuvée, les informations du prêt sont enregistrées dans votre espace.

6️⃣ Le décaissement est effectué manuellement après les vérifications nécessaires.

7️⃣ Le prêt peut ensuite passer à l'état actif.

8️⃣ Les remboursements et l'échéancier sont enregistrés dans le dossier.

⚠️ Une demande ne constitue pas une garantie d'approbation.

━━━━━━━━━━━━━━━━━━
🔹 3. INFORMATIONS DU PRÊT
━━━━━━━━━━━━━━━━━━

Les informations applicables à votre dossier sont celles affichées dans le bot :

💰 Montant du prêt
📊 Taux d'intérêt
📅 Durée
💵 Montant total à rembourser
🧾 Mensualité
📆 Échéancier
📌 Solde restant

Vérifiez toujours les informations affichées avant de poursuivre.

━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━
🔹 4. GARANTIE DE 15 %
━━━━━━━━━━━━━━━━━━

Lorsqu'une garantie est applicable à un dossier, son montant correspond à 15 % du montant du prêt demandé, sauf indication contraire affichée dans le dossier.

🧮 Exemple :
💰 Prêt demandé : 1 000 USDT
📌 Garantie à 15 % : 150 USDT

⚠️ Le montant exact applicable à votre dossier doit toujours être vérifié dans les informations affichées avant toute opération.

⚠️ Une garantie ne constitue pas une approbation automatique du prêt. La demande reste soumise à l'examen et aux conditions applicables.

━━━━━━━━━━━━━━━━━━
🔹 5. PAIEMENTS ET SÉCURITÉ
━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━

🚨 IMPORTANT

Pour éviter les faux paiements et les arnaques :

• Ne payez jamais une personne qui vous contacte en privé et prétend représenter le support.

• Utilisez uniquement les coordonnées de support affichées dans le bot.

• Vérifiez toujours le réseau utilisé avant une transaction.

• Vérifiez l'adresse de réception caractère par caractère.

• Vérifiez le montant avant de confirmer une transaction.

• Conservez toujours le TXID/hash de votre transaction.

• Ne fournissez jamais votre mot de passe.

• Ne fournissez jamais votre code OTP.

• Ne fournissez jamais votre phrase de récupération.

• Ne fournissez jamais votre clé privée.

━━━━━━━━━━━━━━━━━━
🔹 5. FAUX TXID ET FAUSSES PREUVES
━━━━━━━━━━━━━━━━━━

❌ Ne fournissez jamais un faux TXID.

❌ Ne modifiez jamais une capture ou une preuve de paiement.

❌ Une capture d'écran seule ne constitue pas une confirmation blockchain.

Un paiement doit être vérifié avant d'être considéré comme reçu.

⚠️ Le bouton « Garantie envoyée » sert uniquement à déclarer qu'une opération a été effectuée. Il ne constitue pas une validation automatique du paiement.

━━━━━━━━━━━━━━━━━━
🔹 6. DÉCAISSEMENT DU PRÊT
━━━━━━━━━━━━━━━━━━

Le bot ne transfère pas automatiquement les cryptomonnaies.

Lorsqu'un prêt est approuvé, le décaissement est traité manuellement par l'administration.

Le transfert ne doit être présenté comme effectué qu'après confirmation administrative et enregistrement du TXID.

Le client peut ensuite consulter le statut du décaissement dans « 💳 Mon prêt en cours ».

━━━━━━━━━━━━━━━━━━
🔹 7. RÉSEAUX CRYPTO
━━━━━━━━━━━━━━━━━━

Les réseaux disponibles peuvent notamment être :

🔹 TRC20
🔹 BEP20

⚠️ Utilisez exactement le réseau indiqué dans votre dossier.

Une transaction blockchain confirmée peut être irréversible.

Une erreur de réseau ou d'adresse peut entraîner une perte de fonds.

━━━━━━━━━━━━━━━━━━
🔹 8. SUPPORT OFFICIEL DU SERVICE
━━━━━━━━━━━━━━━━━━

💬 Telegram :
@globalusdtfinance

📧 Email :
globalusdtfinance@gmail.com

⚠️ Méfiez-vous des comptes qui utilisent un autre nom ou une autre adresse et prétendent représenter Global USDT Finance.

━━━━━━━━━━━━━━━━━━
🔹 9. KYC ET DONNÉES
━━━━━━━━━━━━━━━━━━

Lorsque le KYC est demandé, envoyez uniquement les informations demandées dans le bot.

Ne partagez jamais :

🔐 Mot de passe
🔐 Code OTP
🔐 Phrase de récupération
🔐 Clé privée

━━━━━━━━━━━━━━━━━━
🔹 10. AVANT TOUTE OPÉRATION
━━━━━━━━━━━━━━━━━━

Avant de confirmer une opération, vérifiez :

☑️ Le montant
☑️ Le réseau
☑️ L'adresse
☑️ Le destinataire
☑️ Le TXID après transaction
☑️ Les conditions affichées dans votre dossier

En cas de doute, contactez le support indiqué dans le bot avant d'effectuer une opération.

━━━━━━━━━━━━━━━━━━
🌍 GLOBAL USDT FINANCE
━━━━━━━━━━━━━━━━━━

Informations, conditions et règles de sécurité du service.

⚠️ Lisez attentivement les informations de votre dossier avant toute opération.""",

            "en": """🌍 GLOBAL USDT FINANCE

ℹ️ TERMS & ABOUT

━━━━━━━━━━━━━━━━━━
🔹 1. ABOUT
━━━━━━━━━━━━━━━━━━

Global USDT Finance is the name used by this service to manage USDT financing requests.

This section explains how the service works, security rules and important information to know before any operation.

━━━━━━━━━━━━━━━━━━
🔹 2. HOW DOES IT WORK?
━━━━━━━━━━━━━━━━━━

1️⃣ Create your profile.

2️⃣ Complete KYC when requested.

3️⃣ Submit your financing request.

4️⃣ Your request is reviewed.

5️⃣ If approved, the loan information is recorded in your account.

6️⃣ Disbursement is handled manually after the necessary checks.

7️⃣ The loan may then become active.

8️⃣ Repayments and the schedule are recorded in your file.

⚠️ A request does not guarantee approval.

━━━━━━━━━━━━━━━━━━
🔹 3. LOAN INFORMATION
━━━━━━━━━━━━━━━━━━

Your applicable information is displayed in the bot:

💰 Loan amount
📊 Interest rate
📅 Duration
💵 Total repayment
🧾 Monthly payment
📆 Schedule
📌 Remaining balance

Always verify the displayed information.

━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━
🔹 4. 15% GUARANTEE
━━━━━━━━━━━━━━━━━━

When a guarantee applies to an application, its amount corresponds to 15% of the requested loan amount, unless otherwise stated in the application.

🧮 Example:
💰 Requested loan: 1,000 USDT
📌 15% guarantee: 150 USDT

⚠️ Always verify the exact amount applicable to your application before any operation.

⚠️ A guarantee does not automatically mean that the loan is approved. The application remains subject to review and applicable conditions.

━━━━━━━━━━━━━━━━━━
🔹 5. PAYMENTS & SECURITY
━━━━━━━━━━━━━━━━━━
━━━━━━━━━━━━━━━━━━

🚨 IMPORTANT

To avoid fake payments and scams:

• Never pay someone who contacts you privately claiming to be support.

• Use only the support contacts displayed in the bot.

• Always verify the network before a transaction.

• Verify the receiving address carefully.

• Verify the amount before confirming.

• Keep the TXID/hash of every transaction.

• Never provide your password.

• Never provide an OTP code.

• Never provide your recovery phrase.

• Never provide your private key.

━━━━━━━━━━━━━━━━━━
🔹 5. FAKE TXIDs & FAKE PROOF
━━━━━━━━━━━━━━━━━━

❌ Never provide a fake TXID.

❌ Never alter a payment screenshot or proof.

❌ A screenshot alone is not blockchain confirmation.

A payment must be verified before being considered received.

⚠️ The “Guarantee sent” button only declares that an operation was made. It is not automatic proof of payment.

━━━━━━━━━━━━━━━━━━
🔹 6. LOAN DISBURSEMENT
━━━━━━━━━━━━━━━━━━

The bot does not automatically transfer cryptocurrency.

After approval, disbursement is handled manually by the administration.

A transfer should only be presented as completed after administrative confirmation and TXID registration.

You can then check the status in “💳 My current loan”.

━━━━━━━━━━━━━━━━━━
🔹 7. CRYPTO NETWORKS
━━━━━━━━━━━━━━━━━━

Networks may include:

🔹 TRC20
🔹 BEP20

⚠️ Use exactly the network shown in your application.

A confirmed blockchain transaction may be irreversible.

━━━━━━━━━━━━━━━━━━
🔹 8. SERVICE SUPPORT
━━━━━━━━━━━━━━━━━━

💬 Telegram:
@globalusdtfinance

📧 Email:
globalusdtfinance@gmail.com

⚠️ Beware of accounts using another name or address claiming to represent Global USDT Finance.

━━━━━━━━━━━━━━━━━━
🔹 9. KYC & DATA
━━━━━━━━━━━━━━━━━━

When KYC is requested, provide only the information requested by the bot.

Never share:

🔐 Password
🔐 OTP code
🔐 Recovery phrase
🔐 Private key

━━━━━━━━━━━━━━━━━━
🔹 10. BEFORE ANY OPERATION
━━━━━━━━━━━━━━━━━━

Check:

☑️ Amount
☑️ Network
☑️ Address
☑️ Recipient
☑️ TXID after the transaction
☑️ Conditions displayed in your application

If in doubt, contact the support shown in the bot before making an operation.

━━━━━━━━━━━━━━━━━━
🌍 GLOBAL USDT FINANCE
━━━━━━━━━━━━━━━━━━

Service information, terms and security rules.""",

            "es": """🌍 GLOBAL USDT FINANCE

ℹ️ CONDICIONES Y ACERCA DE

━━━━━━━━━━━━━━━━━━
🔹 1. ACERCA DEL SERVICIO
━━━━━━━━━━━━━━━━━━

Global USDT Finance es el nombre utilizado por este servicio para gestionar solicitudes de financiación en USDT.

Esta sección explica el funcionamiento, las reglas de seguridad y la información importante.

━━━━━━━━━━━━━━━━━━
🔹 2. ¿CÓMO FUNCIONA?
━━━━━━━━━━━━━━━━━━

1️⃣ Cree su perfil.

2️⃣ Complete el KYC cuando sea solicitado.

3️⃣ Envíe su solicitud.

4️⃣ La solicitud será revisada.

5️⃣ Si es aprobada, la información del préstamo se registra en su cuenta.

6️⃣ El desembolso se gestiona manualmente después de las verificaciones necesarias.

7️⃣ El préstamo puede pasar a estado activo.

8️⃣ Los pagos y el calendario se registran en su expediente.

⚠️ Una solicitud no garantiza la aprobación.

━━━━━━━━━━━━━━━━━━
🔹 4. GARANTÍA DEL 15 %
━━━━━━━━━━━━━━━━━━

Cuando se aplica una garantía a una solicitud, su importe corresponde al 15 % del préstamo solicitado, salvo que se indique lo contrario en la solicitud.

🧮 Ejemplo:
💰 Préstamo solicitado: 1.000 USDT
📌 Garantía del 15 %: 150 USDT

⚠️ Verifique siempre el importe exacto aplicable a su solicitud antes de cualquier operación.

⚠️ Una garantía no significa que el préstamo esté aprobado automáticamente. La solicitud sigue sujeta a revisión y a las condiciones aplicables.

━━━━━━━━━━━━━━━━━━
🔹 5. SEGURIDAD Y PAGOS
━━━━━━━━━━━━━━━━━━

🚨 IMPORTANTE

Para evitar pagos falsos y estafas:

• Nunca pague a una persona que le contacte en privado diciendo ser soporte.

• Utilice únicamente los contactos mostrados en el bot.

• Verifique siempre la red y la dirección.

• Verifique el importe antes de confirmar.

• Conserve el TXID/hash.

• Nunca comparta su contraseña, código OTP, frase de recuperación o clave privada.

━━━━━━━━━━━━━━━━━━
🔹 4. TXID Y PRUEBAS
━━━━━━━━━━━━━━━━━━

❌ Nunca proporcione un TXID falso.

❌ Nunca modifique una prueba de pago.

❌ Una captura de pantalla no constituye una confirmación blockchain.

Los pagos deben verificarse antes de considerarse recibidos.

━━━━━━━━━━━━━━━━━━
🔹 5. DESEMBOLSO
━━━━━━━━━━━━━━━━━━

El bot no transfiere criptomonedas automáticamente.

El desembolso se registra manualmente después de la verificación administrativa.

El estado puede consultarse en «💳 Mi préstamo actual».

━━━━━━━━━━━━━━━━━━
🔹 6. REDES
━━━━━━━━━━━━━━━━━━

🔹 TRC20
🔹 BEP20

⚠️ Utilice exactamente la red indicada en su solicitud.

Una transacción confirmada puede ser irreversible.

━━━━━━━━━━━━━━━━━━
🔹 7. SOPORTE
━━━━━━━━━━━━━━━━━━

💬 Telegram:
@globalusdtfinance

📧 Email:
globalusdtfinance@gmail.com

⚠️ Tenga cuidado con cuentas diferentes que afirmen representar a Global USDT Finance.

━━━━━━━━━━━━━━━━━━
🔹 8. ANTES DE UNA OPERACIÓN
━━━━━━━━━━━━━━━━━━

☑️ Verifique el importe
☑️ Verifique la red
☑️ Verifique la dirección
☑️ Verifique el destinatario
☑️ Guarde el TXID
☑️ Revise las condiciones de su solicitud

En caso de duda, contacte con el soporte indicado en el bot.

🌍 GLOBAL USDT FINANCE
Información, condiciones y seguridad.""",

            "pt": """🌍 GLOBAL USDT FINANCE

ℹ️ CONDIÇÕES E SOBRE

━━━━━━━━━━━━━━━━━━
🔹 1. SOBRE O SERVIÇO
━━━━━━━━━━━━━━━━━━

Global USDT Finance é o nome utilizado por este serviço para gerir pedidos de financiamento em USDT.

Esta seção explica o funcionamento, as regras de segurança e as informações importantes.

━━━━━━━━━━━━━━━━━━
🔹 2. COMO FUNCIONA?
━━━━━━━━━━━━━━━━━━

1️⃣ Crie o seu perfil.

2️⃣ Complete o KYC quando solicitado.

3️⃣ Envie o seu pedido.

4️⃣ O pedido será analisado.

5️⃣ Se aprovado, as informações do empréstimo são registadas na sua conta.

6️⃣ O desembolso é processado manualmente após as verificações necessárias.

7️⃣ O empréstimo pode passar para o estado ativo.

8️⃣ Os pagamentos e o calendário são registados no seu processo.

⚠️ Um pedido não garante aprovação.

━━━━━━━━━━━━━━━━━━
🔹 4. GARANTIA DE 15 %
━━━━━━━━━━━━━━━━━━

Quando uma garantia se aplica a um pedido, o seu valor corresponde a 15 % do empréstimo solicitado, salvo indicação diferente no pedido.

🧮 Exemplo:
💰 Empréstimo solicitado: 1.000 USDT
📌 Garantia de 15 %: 150 USDT

⚠️ Verifique sempre o valor exato aplicável ao seu pedido antes de qualquer operação.

⚠️ Uma garantia não significa que o empréstimo foi automaticamente aprovado. O pedido continua sujeito à análise e às condições aplicáveis.

━━━━━━━━━━━━━━━━━━
🔹 5. PAGAMENTOS E SEGURANÇA
━━━━━━━━━━━━━━━━━━

🚨 IMPORTANTE

Para evitar pagamentos falsos e fraudes:

• Nunca pague alguém que o contacte em privado alegando ser o suporte.

• Utilize apenas os contactos apresentados no bot.

• Verifique sempre a rede e o endereço.

• Confirme o valor antes de realizar a operação.

• Guarde o TXID/hash.

• Nunca forneça a sua palavra-passe, código OTP, frase de recuperação ou chave privada.

━━━━━━━━━━━━━━━━━━
🔹 4. TXID E COMPROVATIVOS
━━━━━━━━━━━━━━━━━━

❌ Nunca forneça um TXID falso.

❌ Nunca altere um comprovativo de pagamento.

❌ Uma captura de ecrã não é uma confirmação blockchain.

Os pagamentos devem ser verificados antes de serem considerados recebidos.

━━━━━━━━━━━━━━━━━━
🔹 5. DESEMBOLSO
━━━━━━━━━━━━━━━━━━

O bot não transfere criptomoedas automaticamente.

O desembolso é registado manualmente após a verificação administrativa.

O estado pode ser consultado em «💳 Meu empréstimo atual».

━━━━━━━━━━━━━━━━━━
🔹 6. REDES
━━━━━━━━━━━━━━━━━━

🔹 TRC20
🔹 BEP20

⚠️ Utilize exatamente a rede indicada no seu pedido.

Uma transação confirmada pode ser irreversível.

━━━━━━━━━━━━━━━━━━
🔹 7. SUPORTE
━━━━━━━━━━━━━━━━━━

💬 Telegram:
@globalusdtfinance

📧 Email:
globalusdtfinance@gmail.com

⚠️ Tenha cuidado com contas diferentes que afirmem representar a Global USDT Finance.

━━━━━━━━━━━━━━━━━━
🔹 8. ANTES DE QUALQUER OPERAÇÃO
━━━━━━━━━━━━━━━━━━

☑️ Verifique o valor
☑️ Verifique a rede
☑️ Verifique o endereço
☑️ Verifique o destinatário
☑️ Guarde o TXID
☑️ Consulte as condições do seu pedido

Em caso de dúvida, contacte o suporte indicado no bot.

🌍 GLOBAL USDT FINANCE
Informações, condições e segurança."""
        }

        # Telegram limite la longueur d'un message.
        # La page Conditions & À-propos est donc envoyée en plusieurs parties.
        about_text = about_texts.get(lang, about_texts["fr"])

        max_length = 3800
        parts = []

        while len(about_text) > max_length:
            cut = about_text.rfind("\n", 0, max_length)
            if cut <= 0:
                cut = max_length

            parts.append(about_text[:cut])
            about_text = about_text[cut:].lstrip("\n")

        if about_text:
            parts.append(about_text)

        for part in parts:
            await update.message.reply_text(part)

        return

    elif text == t["support"]:

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "💬 Support Telegram",
                        url="tg://resolve?domain=globalusdtfinance"
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
                _bt(update, "support_message"),
                reply_markup=keyboard
            )
    elif text == t["language"]:

        await update.message.reply_text(
            i18n_tr(update.effective_user.id, "language_prompt"),
            reply_markup=_registration_language_keyboard(),
        )

    else:
        await update.message.reply_text(
            _bt(update, "menu_navigation"),
            reply_markup=dashboard_keyboard(lang, update.effective_user.id),
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
            _bt(update, "invalid_network")
        )
        return

    context.user_data["loan_network"] = network
    context.user_data["awaiting_network"] = False
    context.user_data["awaiting_wallet_address"] = True

    amount = context.user_data.get("loan_amount", 0)
    duration = context.user_data.get("loan_duration", 0)
    interest = context.user_data.get("interest", 0)
    total_repayment = context.user_data.get("total_repayment", 0)
    monthly_payment = context.user_data.get("monthly_payment", 0)

    lang = get_language(update.effective_user.id)
    NL = chr(10)

    messages = {
        "fr": (
            f"✅ Réseau sélectionné : {network}" + NL + NL
            + f"💰 Montant : {amount:g} USDT" + NL
            + f"📅 Durée : {duration} mois" + NL
            + "📈 Intérêt : 1 % / mois" + NL
            + f"💵 Intérêts totaux : {interest:g} USDT" + NL
            + f"💳 Total à rembourser : {total_repayment:g} USDT" + NL
            + f"🧮 Mensualité : {monthly_payment:.2f} USDT" + NL + NL
            + "📍 ADRESSE DE RÉCEPTION DU PRÊT" + NL + NL
            + f"Envoyez votre adresse {network}, celle sur laquelle vous souhaitez recevoir les USDT "
            + "si votre demande est approuvée." + NL + NL
            + "⚠️ Vérifiez attentivement l'adresse avant de l'envoyer."
        ),
        "en": (
            f"✅ Selected network: {network}" + NL + NL
            + f"💰 Amount: {amount:g} USDT" + NL
            + f"📅 Duration: {duration} months" + NL
            + "📈 Interest: 1% / month" + NL
            + f"💵 Total interest: {interest:g} USDT" + NL
            + f"💳 Total to repay: {total_repayment:g} USDT" + NL
            + f"🧮 Monthly payment: {monthly_payment:.2f} USDT" + NL + NL
            + "📍 LOAN RECEIVING ADDRESS" + NL + NL
            + f"Send your {network} address, the address where you want to receive the USDT "
            + "if your application is approved." + NL + NL
            + "⚠️ Carefully check the address before sending it."
        ),
        "es": (
            f"✅ Red seleccionada: {network}" + NL + NL
            + f"💰 Importe: {amount:g} USDT" + NL
            + f"📅 Duración: {duration} meses" + NL
            + "📈 Interés: 1% / mes" + NL
            + f"💵 Intereses totales: {interest:g} USDT" + NL
            + f"💳 Total a reembolsar: {total_repayment:g} USDT" + NL
            + f"🧮 Pago mensual: {monthly_payment:.2f} USDT" + NL + NL
            + "📍 DIRECCIÓN DE RECEPCIÓN DEL PRÉSTAMO" + NL + NL
            + f"Envíe su dirección {network}, la dirección donde desea recibir los USDT "
            + "si su solicitud es aprobada." + NL + NL
            + "⚠️ Verifique cuidadosamente la dirección antes de enviarla."
        ),
        "pt": (
            f"✅ Rede selecionada: {network}" + NL + NL
            + f"💰 Valor: {amount:g} USDT" + NL
            + f"📅 Prazo: {duration} meses" + NL
            + "📈 Juros: 1% / mês" + NL
            + f"💵 Juros totais: {interest:g} USDT" + NL
            + f"💳 Total a reembolsar: {total_repayment:g} USDT" + NL
            + f"🧮 Pagamento mensal: {monthly_payment:.2f} USDT" + NL + NL
            + "📍 ENDEREÇO DE RECEBIMENTO DO EMPRÉSTIMO" + NL + NL
            + f"Envie seu endereço {network}, o endereço onde deseja receber os USDT "
            + "se sua solicitação for aprovada." + NL + NL
            + "⚠️ Verifique cuidadosamente o endereço antes de enviá-lo."
        )
    }

    message = messages[lang]
    await query.edit_message_text(message)


async def admin_disbursement_router(update, context):
    """
    Route les messages texte de l'administrateur vers le
    processus d'enregistrement du décaissement lorsqu'il est actif.
    Sinon, le comportement normal du dashboard est conservé.
    """
    if update.effective_user and update.effective_user.id == ADMIN_ID:
        if context.user_data.get("channel_admin_mode"):
            await channel_admin_message(update, context)
            return

        if context.user_data.get("admin_disbursement"):
            await admin_disbursement_message(update, context)
            return

    await dashboard(update, context)



async def registration_photo_or_kyc(update, context):
    """
    Si une photo KYC est attendue, elle est envoyée au flux KYC.
    Sinon, elle continue normalement l'inscription.
    """
    if context.user_data.get("awaiting_kyc_photo"):
        await kyc_photo_handler(update, context)
        return ConversationHandler.END

    return await photo(update, context)



# =========================
# MODE GROUPE — LANGUES + AIDE + MODÉRATION
# =========================

def _group_language(user):
    """Return the user's saved language, then Telegram language, then French."""
    if not user:
        return "fr"

    try:
        saved = i18n_get_client_language(user.id)
        if saved in LANGUAGES:
            return saved
    except Exception:
        pass

    code = (getattr(user, "language_code", "") or "").lower().split("-")[0].split("_")[0]
    return code if code in LANGUAGES else "fr"


def _group_language_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇫🇷 Français", callback_data="group_lang_fr"),
            InlineKeyboardButton("🇬🇧 English", callback_data="group_lang_en"),
        ],
        [
            InlineKeyboardButton("🇪🇸 Español", callback_data="group_lang_es"),
            InlineKeyboardButton("🇵🇹 Português", callback_data="group_lang_pt"),
        ],
    ])


GROUP_TERMS = {
    "fr": (
        "📘 <b>À PROPOS & CONDITIONS</b>\n\n"
        "🌍 Loan Request Assistant permet de soumettre et de suivre une demande de prêt en USDT.\n\n"
        "💰 <b>CONDITIONS PRINCIPALES</b>\n"
        "• Montant : 500 à 50 000 USDT\n"
        "• Durée : 6 à 44 mois\n"
        "• Intérêt indiqué : 1 % par mois\n"
        "• Garantie indicative : 15 % du montant demandé\n\n"
        "🛡️ <b>GARANTIE</b>\n"
        "La garantie est un mécanisme de sécurité destiné notamment à limiter le risque de non-remboursement. Elle est prévue pour être restituée après le remboursement complet du prêt, conformément aux conditions du dossier.\n\n"
        "🔐 <b>KYC</b>\n"
        "La vérification KYC est obligatoire avant toute demande de prêt. Les informations et documents fournis doivent être exacts et lisibles.\n\n"
        "⚠️ <b>IMPORTANT</b>\n"
        "La soumission d'une demande ne garantit pas l'acceptation du prêt. Chaque dossier est soumis aux vérifications et conditions du programme.\n\n"
        "En cliquant sur « ✅ Je suis d’accord », vous confirmez avoir lu et compris ces informations."
    ),
    "en": (
        "📘 <b>ABOUT & TERMS</b>\n\n"
        "🌍 Loan Request Assistant allows you to submit and track a USDT loan request.\n\n"
        "💰 <b>MAIN CONDITIONS</b>\n"
        "• Amount: 500 to 50,000 USDT\n"
        "• Duration: 6 to 44 months\n"
        "• Stated interest: 1% per month\n"
        "• Indicative guarantee: 15% of the requested amount\n\n"
        "🛡️ <b>GUARANTEE</b>\n"
        "The guarantee is a security mechanism intended, among other things, to limit the risk of non-repayment. It is intended to be returned after the loan is fully repaid, according to the terms of the loan file.\n\n"
        "🔐 <b>KYC</b>\n"
        "KYC verification is mandatory before submitting a loan request. The information and documents provided must be accurate and readable.\n\n"
        "⚠️ <b>IMPORTANT</b>\n"
        "Submitting a request does not guarantee loan approval. Each application is subject to the program's verification and conditions.\n\n"
        "By clicking « ✅ I agree », you confirm that you have read and understood this information."
    ),
    "es": (
        "📘 <b>INFORMACIÓN Y CONDICIONES</b>\n\n"
        "🌍 Loan Request Assistant permite enviar y seguir una solicitud de préstamo en USDT.\n\n"
        "💰 <b>CONDICIONES PRINCIPALES</b>\n"
        "• Importe: 500 a 50.000 USDT\n"
        "• Duración: 6 a 44 meses\n"
        "• Interés indicado: 1 % mensual\n"
        "• Garantía indicativa: 15 % del importe solicitado\n\n"
        "🛡️ <b>GARANTÍA</b>\n"
        "La garantía es un mecanismo de seguridad destinado, entre otras cosas, a limitar el riesgo de impago. Está prevista su devolución después del reembolso completo del préstamo, según las condiciones del expediente.\n\n"
        "🔐 <b>KYC</b>\n"
        "La verificación KYC es obligatoria antes de solicitar un préstamo. La información y los documentos deben ser exactos y legibles.\n\n"
        "⚠️ <b>IMPORTANTE</b>\n"
        "Enviar una solicitud no garantiza la aprobación del préstamo. Cada expediente está sujeto a las verificaciones y condiciones del programa.\n\n"
        "Al pulsar « ✅ Estoy de acuerdo », confirma que ha leído y comprendido esta información."
    ),
    "pt": (
        "📘 <b>SOBRE E CONDIÇÕES</b>\n\n"
        "🌍 O Loan Request Assistant permite enviar e acompanhar um pedido de empréstimo em USDT.\n\n"
        "💰 <b>CONDIÇÕES PRINCIPAIS</b>\n"
        "• Valor: 500 a 50.000 USDT\n"
        "• Prazo: 6 a 44 meses\n"
        "• Juros indicados: 1% por mês\n"
        "• Garantia indicativa: 15% do valor solicitado\n\n"
        "🛡️ <b>GARANTIA</b>\n"
        "A garantia é um mecanismo de segurança destinado, entre outras coisas, a limitar o risco de não pagamento. Está prevista a sua devolução após o reembolso total do empréstimo, de acordo com as condições do processo.\n\n"
        "🔐 <b>KYC</b>\n"
        "A verificação KYC é obrigatória antes de solicitar um empréstimo. As informações e documentos fornecidos devem ser corretos e legíveis.\n\n"
        "⚠️ <b>IMPORTANTE</b>\n"
        "O envio de um pedido não garante a aprovação do empréstimo. Cada pedido está sujeito às verificações e condições do programa.\n\n"
        "Ao clicar em « ✅ Concordo », confirma que leu e compreendeu estas informações."
    ),
}


def _group_terms_keyboard(lang, bot_username=None):
    labels = {
        "fr": "✅ Je suis d’accord",
        "en": "✅ I agree",
        "es": "✅ Estoy de acuerdo",
        "pt": "✅ Concordo",
    }
    open_labels = {
        "fr": "🤖 Ouvrir le bot",
        "en": "🤖 Open the bot",
        "es": "🤖 Abrir el bot",
        "pt": "🤖 Abrir o bot",
    }
    rows = [[InlineKeyboardButton(labels[lang], callback_data="group_terms_accept")]]
    if bot_username:
        rows.append([InlineKeyboardButton(open_labels[lang], url=f"https://t.me/{bot_username}")])
    return InlineKeyboardMarkup(rows)


GROUP_TEXT = {
    "fr": {
        "welcome": "👋 Bienvenue {name} !\n\n🌍 Bienvenue dans Global USDT Finance Community.\n🤖 Pour utiliser LoanApply24Bot, ouvrez le bot en privé : @LoanApply24Bot.\nℹ️ Aide : /help",
        "hello": "👋 Bonjour {name} !\n\n🤖 Je suis LoanApply24Bot.\nPour effectuer une demande ou utiliser les fonctions du bot, ouvrez-moi en privé : @LoanApply24Bot",
        "help": "🤖 <b>LoanApply24Bot — Aide</b>\n\n📌 <b>Commandes :</b>\n• /help — afficher cette aide\n• @LoanApply24Bot — demander l’assistance\n• Répondre à un message du bot — obtenir une réponse\n\n💰 Pour utiliser toutes les fonctions, ouvrez @LoanApply24Bot en privé.\n🔕 Les messages ordinaires du groupe restent silencieux.",
        "link_deleted": "⚠️ {name}, les liens et invitations externes ne sont pas autorisés dans ce groupe. Votre message a été supprimé.",
        "spam_deleted": "⚠️ {name}, ce message a été supprimé car il ressemble à du spam ou à une publicité non autorisée.",
        "restricted": "🔇 {name}, plusieurs infractions ont été détectées. Vous êtes temporairement restreint pendant 30 minutes.",
    },
    "en": {
        "welcome": "👋 Welcome {name}!\n\n🌍 Welcome to Global USDT Finance Community.\n🤖 To use LoanApply24Bot, open the bot privately: @LoanApply24Bot.\nℹ️ Help: /help",
        "hello": "👋 Hello {name}!\n\n🤖 I am LoanApply24Bot.\nTo submit a request or use the bot's functions, open me privately: @LoanApply24Bot",
        "help": "🤖 <b>LoanApply24Bot — Help</b>\n\n📌 <b>Commands:</b>\n• /help — show this help\n• @LoanApply24Bot — ask for assistance\n• Reply to a bot message — get a response\n\n💰 To use all features, open @LoanApply24Bot privately.\n🔕 Ordinary group messages remain silent.",
        "link_deleted": "⚠️ {name}, external links and invitations are not allowed in this group. Your message was deleted.",
        "spam_deleted": "⚠️ {name}, this message was deleted because it looks like spam or unauthorized advertising.",
        "restricted": "🔇 {name}, several violations were detected. You are temporarily restricted for 30 minutes.",
    },
    "es": {
        "welcome": "👋 ¡Bienvenido {name}!\n\n🌍 Bienvenido a Global USDT Finance Community.\n🤖 Para usar LoanApply24Bot, abre el bot en privado: @LoanApply24Bot.\nℹ️ Ayuda: /help",
        "hello": "👋 ¡Hola {name}!\n\n🤖 Soy LoanApply24Bot.\nPara enviar una solicitud o usar las funciones del bot, ábreme en privado: @LoanApply24Bot",
        "help": "🤖 <b>LoanApply24Bot — Ayuda</b>\n\n📌 <b>Comandos:</b>\n• /help — mostrar esta ayuda\n• @LoanApply24Bot — pedir asistencia\n• Responder a un mensaje del bot — obtener una respuesta\n\n💰 Para usar todas las funciones, abre @LoanApply24Bot en privado.\n🔕 Los mensajes normales del grupo permanecen en silencio.",
        "link_deleted": "⚠️ {name}, los enlaces y las invitaciones externas no están permitidos en este grupo. Tu mensaje fue eliminado.",
        "spam_deleted": "⚠️ {name}, este mensaje fue eliminado porque parece spam o publicidad no autorizada.",
        "restricted": "🔇 {name}, se detectaron varias infracciones. Has sido restringido temporalmente durante 30 minutos.",
    },
    "pt": {
        "welcome": "👋 Bem-vindo {name}!\n\n🌍 Bem-vindo à Global USDT Finance Community.\n🤖 Para usar o LoanApply24Bot, abra o bot em privado: @LoanApply24Bot.\nℹ️ Ajuda: /help",
        "hello": "👋 Olá {name}!\n\n🤖 Sou o LoanApply24Bot.\nPara enviar um pedido ou usar as funções do bot, abra-me em privado: @LoanApply24Bot",
        "help": "🤖 <b>LoanApply24Bot — Ajuda</b>\n\n📌 <b>Comandos:</b>\n• /help — mostrar esta ajuda\n• @LoanApply24Bot — pedir assistência\n• Responder a uma mensagem do bot — obter uma resposta\n\n💰 Para usar todos os recursos, abra @LoanApply24Bot em privado.\n🔕 Mensagens normais do grupo permanecem silenciosas.",
        "link_deleted": "⚠️ {name}, links e convites externos não são permitidos neste grupo. A sua mensagem foi eliminada.",
        "spam_deleted": "⚠️ {name}, esta mensagem foi eliminada porque parece spam ou publicidade não autorizada.",
        "restricted": "🔇 {name}, foram detetadas várias infrações. Você foi temporariamente restringido por 30 minutos.",
    },
}


# Liens externes / invitations. La mention officielle du bot n'est pas bloquée.
_GROUP_LINK_RE = re.compile(
    r"(?:https?://|www\.|t\.me/|telegram\.me/|telegram\.dog/|joinchat/|wa\.me/)",
    re.IGNORECASE,
)

# Signaux simples de publicité/spam répétitif, sans bloquer les conversations normales.
_GROUP_SPAM_RE = re.compile(
    r"(?:double\s+(?:your|ton|vos)|guaranteed\s+(?:profit|income)|\bfree\s+crypto\b|\bairdrop\s+claim\b|\binvest\s+now\b|\bpromo(?:tion)?\b)",
    re.IGNORECASE,
)


async def group_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Accueille les nouveaux membres et leur permet de choisir leur langue dans le groupe."""
    message = update.effective_message
    if not message or not message.new_chat_members:
        return

    for member in message.new_chat_members:
        if getattr(member, "is_bot", False):
            continue
        name = member.mention_html()
        intro = (
            f"👋 Bienvenue {name} !\n\n"
            "🌍 <b>Global USDT Finance Community</b>\n\n"
            "🌐 <b>Choisissez votre langue / Choose your language</b>\n"
            "🇫🇷 Français • 🇬🇧 English • 🇪🇸 Español • 🇵🇹 Português"
        )
        await message.reply_text(
            intro,
            parse_mode="HTML",
            reply_markup=_group_language_keyboard(),
        )


async def group_language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sélection de langue directement dans le groupe, même avant l'inscription privée."""
    query = update.callback_query
    if not query or not query.from_user:
        return

    await query.answer()
    lang = query.data.rsplit("_", 1)[-1]
    if lang not in LANGUAGES:
        return

    context.user_data["language"] = lang

    name = query.from_user.mention_html()
    bot_username = getattr(context.bot, "username", None)
    welcome_next = {
        "fr": f"👋 {name}, votre langue est <b>Français</b>.\n\n📘 Voici les principales conditions. Lisez-les avant de continuer.",
        "en": f"👋 {name}, your language is <b>English</b>.\n\n📘 Here are the main conditions. Please read them before continuing.",
        "es": f"👋 {name}, su idioma es <b>Español</b>.\n\n📘 Estas son las condiciones principales. Léelas antes de continuar.",
        "pt": f"👋 {name}, o seu idioma é <b>Português</b>.\n\n📘 Estas são as principais condições. Leia-as antes de continuar.",
    }

    await query.message.reply_text(
        welcome_next[lang],
        parse_mode="HTML",
    )
    await query.message.reply_text(
        GROUP_TERMS[lang],
        parse_mode="HTML",
        reply_markup=_group_terms_keyboard(lang, bot_username),
    )


async def group_terms_accept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enregistre l'acceptation des conditions dans le groupe et guide vers le bot privé."""
    query = update.callback_query
    if not query or not query.from_user:
        return

    await query.answer()
    lang = context.user_data.get("language") or _group_language(query.from_user)
    if lang not in LANGUAGES:
        lang = "fr"
    context.user_data["language"] = lang
    context.user_data["terms_accepted"] = True

    bot_username = getattr(context.bot, "username", None) or "LoanApply24Bot"
    messages = {
        "fr": "✅ Conditions enregistrées.\n\n🤖 Pour commencer votre inscription et demander un prêt, ouvrez le bot en privé puis envoyez /start.",
        "en": "✅ Terms recorded.\n\n🤖 To start your registration and request a loan, open the bot privately and send /start.",
        "es": "✅ Condiciones registradas.\n\n🤖 Para comenzar su registro y solicitar un préstamo, abra el bot en privado y envíe /start.",
        "pt": "✅ Condições registadas.\n\n🤖 Para iniciar o seu cadastro e solicitar um empréstimo, abra o bot em privado e envie /start.",
    }
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(
        messages[lang],
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton(
                {"fr":"🤖 Ouvrir LoanApply24Bot","en":"🤖 Open LoanApply24Bot","es":"🤖 Abrir LoanApply24Bot","pt":"🤖 Abrir LoanApply24Bot"}[lang],
                url=f"https://t.me/{bot_username}"
            )
        ]]),
    )


async def group_conditions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Affiche les conditions dans le groupe dans la langue du demandeur."""
    user = update.effective_user
    lang = _group_language(user)
    bot_username = getattr(context.bot, "username", None)
    await update.effective_message.reply_text(
        GROUP_TERMS[lang],
        parse_mode="HTML",
        reply_markup=_group_terms_keyboard(lang, bot_username),
    )


async def group_assistant_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Répond seulement à une mention ou à une réponse au bot."""
    message = update.effective_message
    if not message or not message.text:
        return

    text = message.text or ""
    bot_username = getattr(context.bot, "username", None)
    mentioned = bool(bot_username and f"@{bot_username}".lower() in text.lower())
    replied_to_bot = bool(
        message.reply_to_message
        and message.reply_to_message.from_user
        and message.reply_to_message.from_user.id == context.bot.id
    )

    if not (mentioned or replied_to_bot):
        return

    user = update.effective_user
    lang = _group_language(user)
    name = user.mention_html() if user else ""
    await message.reply_text(
        GROUP_TEXT[lang]["hello"].format(name=name),
        parse_mode="HTML",
    )


async def group_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _group_language(user)
    await update.effective_message.reply_text(
        GROUP_TEXT[lang]["help"],
        parse_mode="HTML",
    )


async def private_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _group_language(user)
    texts = {
        "fr": "🤖 <b>Aide LoanApply24Bot</b>\n\nUtilisez les boutons du menu pour accéder à votre profil, demander un prêt, suivre votre dossier, consulter votre prêt en cours, le parrainage, le support et la langue.\n\n🌐 Langues : Français, English, Español, Português.",
        "en": "🤖 <b>LoanApply24Bot Help</b>\n\nUse the menu buttons to access your profile, apply for a loan, track your application, view your active loan, referrals, support and language settings.\n\n🌐 Languages: Français, English, Español, Português.",
        "es": "🤖 <b>Ayuda de LoanApply24Bot</b>\n\nUsa los botones del menú para acceder a tu perfil, solicitar un préstamo, seguir tu solicitud, consultar tu préstamo activo, referidos, soporte e idioma.\n\n🌐 Idiomas: Français, English, Español, Português.",
        "pt": "🤖 <b>Ajuda do LoanApply24Bot</b>\n\nUse os botões do menu para acessar seu perfil, solicitar um empréstimo, acompanhar sua solicitação, consultar seu empréstimo ativo, indicações, suporte e idioma.\n\n🌐 Idiomas: Français, English, Español, Português.",
    }
    await update.effective_message.reply_text(
        texts.get(lang, texts["fr"]),
        parse_mode="HTML",
    )


async def group_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Modération d'abord; si le message est autorisé, traiter une mention/réponse.
    handled = await group_moderation(update, context)
    if handled:
        return
    await group_assistant_trigger(update, context)


async def group_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Modération de base : liens externes, invitations et spam.

    Les administrateurs sont toujours exemptés. Après 3 infractions,
    l'utilisateur est restreint 30 minutes. Les messages ordinaires restent
    silencieux lorsqu'ils ne violent aucune règle.
    """
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat or chat.type not in ("group", "supergroup"):
        return False

    # Ne jamais modérer les administrateurs.
    if user.id == ADMIN_ID:
        return False
    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ("administrator", "creator"):
            return False
    except Exception as exc:
        print(f"⚠️ Vérification admin impossible: {exc}")
        # En cas d'erreur API, on ne supprime pas le message par prudence.
        return False

    content = message.text or message.caption or ""
    lower = content.lower()

    # Autoriser explicitement les références au bot et au support officiel.
    sanitized = re.sub(r"@loanapply24bot|@globalusdtfinance", "", lower)
    has_link = bool(_GROUP_LINK_RE.search(sanitized))
    has_spam = bool(_GROUP_SPAM_RE.search(sanitized))

    if not (has_link or has_spam):
        return False

    lang = _group_language(user)
    name = user.mention_html()
    reason_key = "link_deleted" if has_link else "spam_deleted"

    try:
        await message.delete()
    except Exception as exc:
        print(f"⚠️ Suppression du message impossible: {exc}")
        return False

    warnings = context.chat_data.setdefault("moderation_warnings", {})
    uid = str(user.id)
    warnings[uid] = int(warnings.get(uid, 0)) + 1
    count = warnings[uid]

    # Message d'avertissement court; après 3 infractions, restriction automatique.
    if count >= 3:
        try:
            await context.bot.restrict_chat_member(
                chat_id=chat.id,
                user_id=user.id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            await chat.send_message(
                GROUP_TEXT[lang]["restricted"].format(name=name),
                parse_mode="HTML",
            )
            warnings[uid] = 0
            return True
        except Exception as exc:
            print(f"⚠️ Restriction impossible: {exc}")
            return True
    else:
        try:
            await chat.send_message(
                GROUP_TEXT[lang][reason_key].format(name=name),
                parse_mode="HTML",
            )
        except Exception as exc:
            print(f"⚠️ Avertissement impossible: {exc}")
        return True


async def post_init(application):
    """Expose /start, /help and /cancel in Telegram's bot command menu."""
    await application.bot.set_my_commands([
        ("start", "Start / Ouvrir le bot"),
        ("help", "Help / Aide"),
        ("conditions", "Loan conditions / Conditions"),
        ("cancel", "Cancel / Annuler"),
    ])

def main():

    init_database()
    ensure_enterprise_schema()

    persistence = PicklePersistence(filepath=PERSISTENCE_PATH, update_interval=1)
    application = Application.builder().token(TOKEN).persistence(persistence).post_init(post_init).connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30).build()

    register_enterprise_handlers(application)

    registration = ConversationHandler(
        entry_points=[
            CommandHandler("start", start, filters=filters.ChatType.PRIVATE),
            CallbackQueryHandler(
                registration_resume_entry,
                pattern=r"^registration_resume$"
            )
        ],
        allow_reentry=True,
        persistent=True,
        name="registration",

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
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                ),
            ],

            2: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    first_name
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            3: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    last_name
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            4: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    country
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            5: [
                MessageHandler(
                    filters.CONTACT | (filters.TEXT & ~filters.COMMAND),
                    phone
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            6: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    email
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            7: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    profession
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            8: [
                MessageHandler(
                    filters.PHOTO,
                    registration_photo_or_kyc
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            9: [
                MessageHandler(
                    filters.TEXT,
                    trc20
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],

            10: [
                MessageHandler(
                    filters.TEXT,
                    bep20
                ),
                MessageHandler(
                    filters.ALL & ~filters.COMMAND,
                    registration_invalid_input
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel, filters=filters.ChatType.PRIVATE)
        ],
    )

    application.add_handler(CommandHandler("admin", admin_panel))

    application.add_handler(
        CallbackQueryHandler(
            channel_callback,
            pattern=r"^admin_channel(?:_|$)"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern=r"^admin_"
        )
    )


    application.add_handler(registration)

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.PHOTO,
            kyc_photo_handler
        )
    )

    # =========================
    # SUIVI DU DOSSIER
    # =========================
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.Regex(
                r"^(📊 Suivi du dossier|📊 Application tracking|📊 Seguimiento de la solicitud|📊 Acompanhamento do pedido)$"
            ),
            loan_tracking,
        )
    )

    # =========================
    # MON PRÊT EN COURS
    # =========================

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.Regex(r"^(💳 Mon prêt en cours|💳 My active loan|💳 Mi préstamo activo|💳 Meu empréstimo ativo)$"),
            my_loan
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            loan_schedule_callback,
            pattern=r"^loan_schedule:\d+:\d+$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            loan_current_callback,
            pattern=r"^loan_current:\d+$"
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE
            & filters.User(user_id=ADMIN_ID)
            & filters.TEXT
            & ~filters.COMMAND,
            admin_disbursement_router
        )
    )

    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.Regex(r"^(🇫🇷 Français|🇬🇧 English|🇪🇸 Español|🇵🇹 Português)$"),
            change_existing_language,
        )
    )

    # =========================
    # GROUPE — SILENCIEUX + AIDE + MODÉRATION
    # =========================
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.StatusUpdate.NEW_CHAT_MEMBERS,
            group_welcome,
        )
    )
    application.add_handler(
        CommandHandler("help", group_help, filters=filters.ChatType.GROUPS),
    )
    application.add_handler(
        CommandHandler("help", private_help, filters=filters.ChatType.PRIVATE),
    )
    application.add_handler(
        CommandHandler("conditions", group_conditions, filters=filters.ChatType.GROUPS),
    )
    application.add_handler(
        CallbackQueryHandler(group_language_callback, pattern=r"^group_lang_(fr|en|es|pt)$"),
    )
    application.add_handler(
        CallbackQueryHandler(group_terms_accept_callback, pattern=r"^group_terms_accept$"),
    )
    application.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            group_message_router,
        )
    )

    # =========================
    # PRIVÉ — TABLEAU DE BORD
    # =========================
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            dashboard
        )
    )

    # =========================
    # NOTIFICATIONS D'ÉCHÉANCES
    # =========================
    if application.job_queue is not None:
        application.job_queue.run_repeating(
            check_due_notifications,
            interval=3600,
            first=30,
            name="loan_due_notifications",
        )
        print("🔔 Notifications d'échéances activées.")
    else:
        print("⚠️ JobQueue indisponible : notifications d'échéances désactivées.")

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
    application.add_handler(
        CallbackQueryHandler(
            verify_guarantee_address_callback,
            pattern=r"^verify_guarantee_address$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            loan_guarantee_sent_callback,
            pattern=r"^continue_after_verify$"
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
