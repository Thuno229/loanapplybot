import sqlite3

DB = "loan_bot.db"

SUPPORTED_LANGUAGES = {"fr", "en", "es", "pt"}


def get_client_language(telegram_id):
    try:
        conn = sqlite3.connect(DB)
        cur = conn.cursor()
        cur.execute(
            "SELECT language FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = cur.fetchone()
        conn.close()

        lang = row[0] if row and row[0] else "fr"
    except Exception:
        lang = "fr"

    lang = str(lang).lower().strip()

    aliases = {
        "french": "fr",
        "français": "fr",
        "francais": "fr",
        "fr": "fr",
        "english": "en",
        "anglais": "en",
        "en": "en",
        "spanish": "es",
        "español": "es",
        "espanol": "es",
        "es": "es",
        "portuguese": "pt",
        "português": "pt",
        "portugues": "pt",
        "pt": "pt",
    }

    lang = aliases.get(lang, lang)

    return lang if lang in SUPPORTED_LANGUAGES else "fr"


TEXT = {
    "fr": {
        "loan_impossible": "❌ Impossible de traiter cette demande pour le moment.",
        "profile_not_found": "❌ Profil client introuvable.",
        "kyc_sent": (
            "🪪 Votre document KYC a été envoyé.\n\n"
            "⏳ Statut : en attente de vérification manuelle.\n\n"
            "Vous serez informé après la vérification."
        ),
        "kyc_approved": (
            "🎉 Votre vérification KYC a été validée.\n\n"
            "✅ Statut : KYC approuvé.\n\n"
            "Vous pouvez maintenant accéder aux fonctionnalités disponibles."
        ),
        "kyc_rejected": (
            "❌ Votre vérification KYC a été rejetée.\n\n"
            "Veuillez envoyer un document clair et lisible correspondant "
            "aux informations de votre inscription."
        ),
        "loan_incomplete": "❌ Votre demande de prêt est incomplète.",
        "loan_recorded": "✅ Votre demande de prêt a été enregistrée.",
        "loan_conditions": (
            "📋 Conditions du prêt\n\n"
            "Veuillez vérifier les conditions avant de continuer."
        ),
        "network_unknown": "❌ Réseau non reconnu.",
        "address_unavailable": "❌ L'adresse de réception n'est pas disponible.",
        "guarantee_address": (
            "💳 Adresse de réception configurée\n\n"
            "Réseau : {network}\n"
            "Adresse : {address}\n\n"
            "⚠️ Vérifiez attentivement le réseau et l'adresse avant toute opération."
        ),
        "txid": (
            "📄 TXID / HASH DE LA TRANSACTION\n\n"
            "💰 Valeur du prêt : {amount:g} USDT\n"
            "📊 Garantie indicative : {guarantee:g} USDT\n"
            "🌐 Réseau : {network}\n"
            "📝 Si une opération liée à cette demande a déjà été réalisée, "
            "envoyez maintenant le TXID/hash.\n\n"
            "⚠️ Le TXID sera vérifié manuellement.\n"
            "Le bot ne valide pas automatiquement les paiements.\n\n"
            "Exemple : 0x... ou TXID..."
        ),
        "cancelled": "❌ Opération annulée.",
        "already_processing": (
            "⏳ Une opération est déjà en cours de traitement."
        ),

        "copy_address": "📋 Copier l'adresse",
        "continue_button": "➡️ Continuer",
        "loan_incomplete_callback": "❌ Informations de demande incomplètes.\n\nVeuillez recommencer la demande de prêt.",
        "network_not_found_callback": "❌ Réseau non reconnu.\n\nVeuillez recommencer la demande.",
        "guarantee_sent_missing": "❌ Les informations de votre demande sont incomplètes.\n\nVeuillez recommencer la demande.",
    },

    "en": {
        "loan_impossible": "❌ This request cannot be processed at the moment.",
        "profile_not_found": "❌ Client profile not found.",
        "kyc_sent": (
            "🪪 Your KYC document has been submitted.\n\n"
            "⏳ Status: waiting for manual verification.\n\n"
            "You will be informed after verification."
        ),
        "kyc_approved": (
            "🎉 Your KYC verification has been approved.\n\n"
            "✅ Status: KYC approved.\n\n"
            "You can now access the available features."
        ),
        "kyc_rejected": (
            "❌ Your KYC verification was rejected.\n\n"
            "Please send a clear and readable document matching "
            "your registration information."
        ),
        "loan_incomplete": "❌ Your loan request is incomplete.",
        "loan_recorded": "✅ Your loan request has been recorded.",
        "loan_conditions": (
            "📋 Loan Terms\n\n"
            "Please review the terms before continuing."
        ),
        "network_unknown": "❌ Unknown network.",
        "address_unavailable": "❌ The receiving address is unavailable.",
        "guarantee_address": (
            "💳 Configured receiving address\n\n"
            "Network: {network}\n"
            "Address: {address}\n\n"
            "⚠️ Carefully verify the network and address before any operation."
        ),
        "txid": (
            "📄 TRANSACTION TXID / HASH\n\n"
            "💰 Loan amount: {amount:g} USDT\n"
            "📊 Indicative guarantee: {guarantee:g} USDT\n"
            "🌐 Network: {network}\n"
            "📝 If an operation related to this request has already been made, "
            "send the TXID/hash now.\n\n"
            "⚠️ The TXID will be checked manually.\n"
            "The bot does not automatically validate payments.\n\n"
            "Example: 0x... or TXID..."
        ),
        "cancelled": "❌ Operation cancelled.",
        "already_processing": (
            "⏳ An operation is already being processed."
        ),

        "copy_address": "📋 Copy address",
        "continue_button": "➡️ Continue",
        "loan_incomplete_callback": "❌ Application information is incomplete.\n\nPlease restart the loan application.",
        "network_not_found_callback": "❌ Network not recognized.\n\nPlease restart the application.",
        "guarantee_sent_missing": "❌ Your application information is incomplete.\n\nPlease restart the application.",
    },

    "es": {
        "loan_impossible": "❌ No se puede procesar esta solicitud en este momento.",
        "profile_not_found": "❌ Perfil del cliente no encontrado.",
        "kyc_sent": (
            "🪪 Su documento KYC ha sido enviado.\n\n"
            "⏳ Estado: pendiente de verificación manual.\n\n"
            "Se le informará después de la verificación."
        ),
        "kyc_approved": (
            "🎉 Su verificación KYC ha sido aprobada.\n\n"
            "✅ Estado: KYC aprobado.\n\n"
            "Ahora puede acceder a las funciones disponibles."
        ),
        "kyc_rejected": (
            "❌ Su verificación KYC ha sido rechazada.\n\n"
            "Envíe un documento claro y legible que corresponda "
            "a la información de su registro."
        ),
        "loan_incomplete": "❌ Su solicitud de préstamo está incompleta.",
        "loan_recorded": "✅ Su solicitud de préstamo ha sido registrada.",
        "loan_conditions": (
            "📋 Condiciones del préstamo\n\n"
            "Revise las condiciones antes de continuar."
        ),
        "network_unknown": "❌ Red no reconocida.",
        "address_unavailable": "❌ La dirección de recepción no está disponible.",
        "guarantee_address": (
            "💳 Dirección de recepción configurada\n\n"
            "Red: {network}\n"
            "Dirección: {address}\n\n"
            "⚠️ Verifique cuidadosamente la red y la dirección antes de cualquier operación."
        ),
        "txid": (
            "📄 TXID / HASH DE LA TRANSACCIÓN\n\n"
            "💰 Importe del préstamo: {amount:g} USDT\n"
            "📊 Garantía indicativa: {guarantee:g} USDT\n"
            "🌐 Red: {network}\n"
            "📝 Si ya se ha realizado una operación relacionada con esta solicitud, "
            "envíe ahora el TXID/hash.\n\n"
            "⚠️ El TXID será verificado manualmente.\n"
            "El bot no valida los pagos automáticamente.\n\n"
            "Ejemplo: 0x... o TXID..."
        ),
        "cancelled": "❌ Operación cancelada.",
        "already_processing": (
            "⏳ Ya hay una operación en proceso."
        ),

        "copy_address": "📋 Copiar dirección",
        "continue_button": "➡️ Continuar",
        "loan_incomplete_callback": "❌ La información de la solicitud está incompleta.\n\nReinicia la solicitud de préstamo.",
        "network_not_found_callback": "❌ Red no reconocida.\n\nReinicia la solicitud.",
        "guarantee_sent_missing": "❌ La información de tu solicitud está incompleta.\n\nReinicia la solicitud.",
    },

    "pt": {
        "loan_impossible": "❌ Não é possível processar esta solicitação no momento.",
        "profile_not_found": "❌ Perfil do cliente não encontrado.",
        "kyc_sent": (
            "🪪 Seu documento KYC foi enviado.\n\n"
            "⏳ Status: aguardando verificação manual.\n\n"
            "Você será informado após a verificação."
        ),
        "kyc_approved": (
            "🎉 Sua verificação KYC foi aprovada.\n\n"
            "✅ Status: KYC aprovado.\n\n"
            "Agora você pode acessar os recursos disponíveis."
        ),
        "kyc_rejected": (
            "❌ Sua verificação KYC foi rejeitada.\n\n"
            "Envie um documento claro e legível correspondente "
            "às informações do seu cadastro."
        ),
        "loan_incomplete": "❌ Sua solicitação de empréstimo está incompleta.",
        "loan_recorded": "✅ Sua solicitação de empréstimo foi registrada.",
        "loan_conditions": (
            "📋 Condições do empréstimo\n\n"
            "Revise as condições antes de continuar."
        ),
        "network_unknown": "❌ Rede não reconhecida.",
        "address_unavailable": "❌ O endereço de recebimento não está disponível.",
        "guarantee_address": (
            "💳 Endereço de recebimento configurado\n\n"
            "Rede: {network}\n"
            "Endereço: {address}\n\n"
            "⚠️ Verifique cuidadosamente a rede e o endereço antes de qualquer operação."
        ),
        "txid": (
            "📄 TXID / HASH DA TRANSAÇÃO\n\n"
            "💰 Valor do empréstimo: {amount:g} USDT\n"
            "📊 Garantia indicativa: {guarantee:g} USDT\n"
            "🌐 Rede: {network}\n"
            "📝 Se uma operação relacionada a esta solicitação já foi realizada, "
            "envie agora o TXID/hash.\n\n"
            "⚠️ O TXID será verificado manualmente.\n"
            "O bot não valida pagamentos automaticamente.\n\n"
            "Exemplo: 0x... ou TXID..."
        ),
        "cancelled": "❌ Operação cancelada.",
        "already_processing": (
            "⏳ Uma operação já está sendo processada."
        ),

        "copy_address": "📋 Copiar endereço",
        "continue_button": "➡️ Continuar",
        "loan_incomplete_callback": "❌ As informações do pedido estão incompletas.\n\nReinicie o pedido de empréstimo.",
        "network_not_found_callback": "❌ Rede não reconhecida.\n\nReinicie o pedido.",
        "guarantee_sent_missing": "❌ As informações do seu pedido estão incompletas.\n\nReinicie o pedido.",
    },
}


def tr(telegram_id, key, **kwargs):
    """Retourne le texte client dans la langue enregistrée."""
    lang = get_client_language(telegram_id)

    text = TEXT.get(lang, TEXT["fr"]).get(key)

    if text is None:
        text = TEXT["fr"].get(key, key)

    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        return text

TEXT["fr"]["loan_processing"] = "⏳ Cette demande est déjà en cours de traitement."
TEXT["en"]["loan_processing"] = "⏳ This request is already being processed."
TEXT["es"]["loan_processing"] = "⏳ Esta solicitud ya está siendo procesada."
TEXT["pt"]["loan_processing"] = "⏳ Este pedido já está sendo processado."

TEXT["fr"]["loan_request_incomplete"] = "❌ Les informations de la demande sont incomplètes.\n\nVeuillez recommencer la demande."
TEXT["en"]["loan_request_incomplete"] = "❌ The loan request information is incomplete.\n\nPlease restart the request."
TEXT["es"]["loan_request_incomplete"] = "❌ La información de la solicitud está incompleta.\n\nVuelve a iniciar la solicitud."
TEXT["pt"]["loan_request_incomplete"] = "❌ As informações do pedido estão incompletas.\n\nReinicie o pedido."


# ===== CALLBACKS : DEMANDE ENREGISTRÉE =====

TEXT["fr"]["loan_submitted"] = (
    "✅ Demande enregistrée avec succès.\n\n"
    "🆔 Demande : #{request_id}\n"
    "💰 Montant : {amount:g} USDT\n"
    "📊 Garantie indicative (15%) : {guarantee:g} USDT\n"
    "🌐 Réseau : {network}\n"
    "📍 Adresse : {wallet}\n"
    "📄 TXID : {txid}\n\n"
    "⏳ Statut : en attente de vérification manuelle.\n\n"
    "⚠️ Aucune validation automatique du paiement n'est effectuée."
)

TEXT["en"]["loan_submitted"] = (
    "✅ Loan request submitted successfully.\n\n"
    "🆔 Request: #{request_id}\n"
    "💰 Amount: {amount:g} USDT\n"
    "📊 Indicative guarantee (15%): {guarantee:g} USDT\n"
    "🌐 Network: {network}\n"
    "📍 Address: {wallet}\n"
    "📄 TXID: {txid}\n\n"
    "⏳ Status: awaiting manual verification.\n\n"
    "⚠️ Payment is not verified automatically."
)

TEXT["es"]["loan_submitted"] = (
    "✅ Solicitud registrada correctamente.\n\n"
    "🆔 Solicitud: #{request_id}\n"
    "💰 Importe: {amount:g} USDT\n"
    "📊 Garantía indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Red: {network}\n"
    "📍 Dirección: {wallet}\n"
    "📄 TXID: {txid}\n\n"
    "⏳ Estado: pendiente de verificación manual.\n\n"
    "⚠️ El pago no se verifica automáticamente."
)

TEXT["pt"]["loan_submitted"] = (
    "✅ Pedido registrado com sucesso.\n\n"
    "🆔 Pedido: #{request_id}\n"
    "💰 Valor: {amount:g} USDT\n"
    "📊 Garantia indicativa (15%): {guarantee:g} USDT\n"
    "🌐 Rede: {network}\n"
    "📍 Endereço: {wallet}\n"
    "📄 TXID: {txid}\n\n"
    "⏳ Status: aguardando verificação manual.\n\n"
    "⚠️ O pagamento não é verificado automaticamente."
)

# ===== CALLBACKS : ADRESSE DE GARANTIE =====

TEXT["fr"]["guarantee_address_title"] = (
    "🔐 ADRESSE DE GARANTIE\n\n"
    "🌐 Réseau : {network}\n\n"
    "📍 Adresse de garantie :\n"
    "{address}\n\n"
    "💵 Garantie indicative : {guarantee:g} USDT\n\n"
    "⚠️ Vérifiez attentivement le réseau et l'adresse "
    "avant toute opération éventuelle.\n\n"
    "Cette adresse est uniquement l'adresse configurée "
    "dans le bot. Aucun paiement n'est vérifié automatiquement."
)

TEXT["en"]["guarantee_address_title"] = (
    "🔐 GUARANTEE ADDRESS\n\n"
    "🌐 Network: {network}\n\n"
    "📍 Guarantee address:\n"
    "{address}\n\n"
    "💵 Indicative guarantee: {guarantee:g} USDT\n\n"
    "⚠️ Carefully verify the network and address "
    "before any possible operation.\n\n"
    "This address is only the address configured "
    "in the bot. No payment is verified automatically."
)

TEXT["es"]["guarantee_address_title"] = (
    "🔐 DIRECCIÓN DE GARANTÍA\n\n"
    "🌐 Red: {network}\n\n"
    "📍 Dirección de garantía:\n"
    "{address}\n\n"
    "💵 Garantía indicativa: {guarantee:g} USDT\n\n"
    "⚠️ Verifica cuidadosamente la red y la dirección "
    "antes de cualquier posible operación.\n\n"
    "Esta dirección es únicamente la dirección configurada "
    "en el bot. Ningún pago se verifica automáticamente."
)

TEXT["pt"]["guarantee_address_title"] = (
    "🔐 ENDEREÇO DA GARANTIA\n\n"
    "🌐 Rede: {network}\n\n"
    "📍 Endereço da garantia:\n"
    "{address}\n\n"
    "💵 Garantia indicativa: {guarantee:g} USDT\n\n"
    "⚠️ Verifique cuidadosamente a rede e o endereço "
    "antes de qualquer possível operação.\n\n"
    "Este endereço é apenas o endereço configurado "
    "no bot. Nenhum pagamento é verificado automaticamente."
)

# ===== CALLBACKS : ANNULATION =====

TEXT["fr"]["loan_cancelled"] = (
    "❌ Demande annulée.\n\n"
    "Aucune demande n'a été enregistrée."
)

TEXT["en"]["loan_cancelled"] = (
    "❌ Request cancelled.\n\n"
    "No request was registered."
)

TEXT["es"]["loan_cancelled"] = (
    "❌ Solicitud cancelada.\n\n"
    "No se ha registrado ninguna solicitud."
)

TEXT["pt"]["loan_cancelled"] = (
    "❌ Pedido cancelado.\n\n"
    "Nenhum pedido foi registrado."
)
