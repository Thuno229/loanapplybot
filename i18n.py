from storage import DB_PATH
import sqlite3

DB = DB_PATH

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


TEXT["fr"]["loan_approved"] = ("✅ Votre demande de prêt #{request_id} a été approuvée.\n\n💰 Montant : {amount:g} USDT\n📈 Taux : {interest_rate:g} % / mois\n💳 Total à rembourser : {total_repayment:.2f} USDT\n🧮 Mensualité : {monthly_payment:.2f} USDT\n📅 Durée : {duration_months} mois\n\n📤 Décaissement : en attente de confirmation administrative.\nLe prêt n'est pas considéré comme versé tant que le décaissement n'a pas été enregistré par l'administrateur.\n\n💳 Vous pourrez consulter les détails de votre prêt depuis votre tableau de bord.")
TEXT["en"]["loan_approved"] = ("✅ Your loan application #{request_id} has been approved.\n\n💰 Amount: {amount:g} USDT\n📈 Rate: {interest_rate:g}% / month\n💳 Total repayment: {total_repayment:.2f} USDT\n🧮 Monthly payment: {monthly_payment:.2f} USDT\n📅 Duration: {duration_months} months\n\n📤 Disbursement: awaiting administrative confirmation.\nThe loan is not considered disbursed until the administrator records the disbursement.\n\n💳 You can view your loan details from your dashboard.")
TEXT["es"]["loan_approved"] = ("✅ Su solicitud de préstamo #{request_id} ha sido aprobada.\n\n💰 Importe: {amount:g} USDT\n📈 Tasa: {interest_rate:g}% / mes\n💳 Total a reembolsar: {total_repayment:.2f} USDT\n🧮 Cuota mensual: {monthly_payment:.2f} USDT\n📅 Duración: {duration_months} meses\n\n📤 Desembolso: pendiente de confirmación administrativa.\nEl préstamo no se considera desembolsado hasta que el administrador registre el desembolso.\n\n💳 Puede consultar los detalles de su préstamo desde su panel.")
TEXT["pt"]["loan_approved"] = ("✅ O seu pedido de empréstimo #{request_id} foi aprovado.\n\n💰 Valor: {amount:g} USDT\n📈 Taxa: {interest_rate:g}% / mês\n💳 Total a reembolsar: {total_repayment:.2f} USDT\n🧮 Parcela mensal: {monthly_payment:.2f} USDT\n📅 Duração: {duration_months} meses\n\n📤 Desembolso: aguardando confirmação administrativa.\nO empréstimo não é considerado desembolsado até que o administrador registe o desembolso.\n\n💳 Pode consultar os detalhes do seu empréstimo no seu painel.")
TEXT["fr"]["loan_rejected"] = "❌ Votre demande de prêt #{request_id} a été rejetée.\n\nLa décision a été enregistrée dans votre dossier.\n\n📞 Pour toute question, contactez le support."
TEXT["en"]["loan_rejected"] = "❌ Your loan application #{request_id} has been rejected.\n\nThe decision has been recorded in your file.\n\n📞 For any questions, please contact support."
TEXT["es"]["loan_rejected"] = "❌ Su solicitud de préstamo #{request_id} ha sido rechazada.\n\nLa decisión ha sido registrada en su expediente.\n\n📞 Para cualquier pregunta, contacte con soporte."
TEXT["pt"]["loan_rejected"] = "❌ O seu pedido de empréstimo #{request_id} foi rejeitado.\n\nA decisão foi registada no seu processo.\n\n📞 Para qualquer questão, contacte o suporte."



# ===== GLOBAL CLIENT-SAFE TRANSLATIONS =====
_GLOBAL_CLIENT_TEXT = {
    'fr': {
        'generic_error': "⚠️ Impossible d'afficher ce message pour le moment.",
        'language_prompt': '🌐 Choisissez votre langue :',
        'language_changed': '✅ Langue mise à jour.',
        'language_invalid': '🌐 Veuillez choisir une langue avec l’un des boutons ci-dessous.',
        'loan_not_associated': "❌ Ce prêt n'est pas associé à votre compte.",
        'no_approved_loan': "ℹ️ Aucun prêt approuvé ou en cours n'est actuellement associé à votre compte.",
        'no_schedule': "📅 ÉCHÉANCIER\n\nAucune échéance n'est encore enregistrée.",
        'network_select': '⚠️ Veuillez sélectionner votre réseau en appuyant sur TRC20 ou BEP20.',
        'invalid_txid': '❌ TXID invalide.\n\nEnvoyez uniquement le TXID/hash de la transaction, sans espace.',
        'invalid_amount': '❌ Veuillez entrer uniquement un montant en USDT.\n\nExemple : 500',
        'no_requests': "📋 Vous n'avez pas encore de demande de prêt.",
        'referral_new_user': "🎉 NOUVEAU FILLEUL !\n\n👤 {name} vient de s'inscrire avec votre lien.\n\n🎁 Parrainage enregistré avec succès.\n💰 Récompense potentielle : 5 USDT\n⏳ Statut : en attente des conditions du programme.",
        'referral_linked': '🎁 PARRAINAGE ENREGISTRÉ !\n👤 Votre parrain : {name}\n✅ Votre inscription a bien été associée à son lien.\n💰 Récompense potentielle du parrain : 5 USDT\n⏳ Statut : en attente des conditions du programme.',
        'active_loan_button': '💳 Mon prêt en cours',
        'cancel_button': '❌ Annuler',
        'show_guarantee_address': '🔐 Voir l’adresse de garantie',
        'loan_stage_update': "📊 MISE À JOUR DE VOTRE DOSSIER\n\n🆔 Demande : #{request_id}\n📌 Nouvelle étape : {stage_label}\n\nVotre dossier a été mis à jour.",
        'due_3d': "🔔 RAPPEL D'ÉCHÉANCE\n\n💳 Prêt : #{loan_id}\n📄 Échéance n° : {installment_number}\n📅 Date : {due_date}\n💰 Montant : {amount:.2f} USDT\n\nVotre échéance est prévue dans 3 jours.\n\nConsultez votre espace pour les détails.",
        'due_today': "📅 ÉCHÉANCE AUJOURD'HUI\n\n💳 Prêt : #{loan_id}\n📄 Échéance n° : {installment_number}\n💰 Montant : {amount:.2f} USDT\n\nCette échéance arrive aujourd'hui.\nConsultez votre espace pour les détails.",
        'due_overdue': '⚠️ ÉCHÉANCE EN RETARD\n\n💳 Prêt : #{loan_id}\n📄 Échéance n° : {installment_number}\n📅 Date prévue : {due_date}\n💰 Montant : {amount:.2f} USDT\n\nCette échéance est maintenant en retard.\nConsultez votre espace pour les détails.',
    },
    'en': {
        'generic_error': '⚠️ Unable to display this message right now.',
        'language_prompt': '🌐 Choose your language:',
        'language_changed': '✅ Language updated.',
        'language_invalid': '🌐 Please choose a language using one of the buttons below.',
        'loan_not_associated': '❌ This loan is not associated with your account.',
        'no_approved_loan': 'ℹ️ No approved or active loan is currently associated with your account.',
        'no_schedule': '📅 REPAYMENT SCHEDULE\n\nNo installment is currently recorded.',
        'network_select': '⚠️ Please select your network by pressing TRC20 or BEP20.',
        'invalid_txid': '❌ Invalid TXID.\n\nSend only the transaction TXID/hash, without spaces.',
        'invalid_amount': '❌ Please enter a USDT amount only.\n\nExample: 500',
        'no_requests': '📋 You do not have any loan applications yet.',
        'referral_new_user': '🎉 NEW REFERRAL!\n\n👤 {name} just registered using your link.\n\n🎁 Referral recorded successfully.\n💰 Potential reward: 5 USDT\n⏳ Status: waiting for the program conditions.',
        'referral_linked': '🎁 REFERRAL RECORDED!\n👤 Your referrer: {name}\n✅ Your registration has been linked to their referral.\n💰 Potential referrer reward: 5 USDT\n⏳ Status: waiting for the program conditions.',
        'active_loan_button': '💳 My active loan',
        'cancel_button': '❌ Cancel',
        'show_guarantee_address': '🔐 Show guarantee address',
        'loan_stage_update': "📊 APPLICATION UPDATE\n\n🆔 Application: #{request_id}\n📌 New stage: {stage_label}\n\nYour application has been updated.",
        'due_3d': '🔔 PAYMENT REMINDER\n\n💳 Loan: #{loan_id}\n📄 Installment: #{installment_number}\n📅 Date: {due_date}\n💰 Amount: {amount:.2f} USDT\n\nYour installment is due in 3 days.\n\nOpen your account for details.',
        'due_today': '📅 PAYMENT DUE TODAY\n\n💳 Loan: #{loan_id}\n📄 Installment: #{installment_number}\n💰 Amount: {amount:.2f} USDT\n\nThis installment is due today.\nOpen your account for details.',
        'due_overdue': '⚠️ OVERDUE PAYMENT\n\n💳 Loan: #{loan_id}\n📄 Installment: #{installment_number}\n📅 Due date: {due_date}\n💰 Amount: {amount:.2f} USDT\n\nThis installment is now overdue.\nOpen your account for details.',
    },
    'es': {
        'generic_error': '⚠️ No se puede mostrar este mensaje en este momento.',
        'language_prompt': '🌐 Elige tu idioma:',
        'language_changed': '✅ Idioma actualizado.',
        'language_invalid': '🌐 Elige un idioma con uno de los botones siguientes.',
        'loan_not_associated': '❌ Este préstamo no está asociado a tu cuenta.',
        'no_approved_loan': 'ℹ️ No hay ningún préstamo aprobado o activo asociado actualmente a tu cuenta.',
        'no_schedule': '📅 CALENDARIO DE PAGOS\n\nTodavía no hay ninguna cuota registrada.',
        'network_select': '⚠️ Selecciona tu red pulsando TRC20 o BEP20.',
        'invalid_txid': '❌ TXID no válido.\n\nEnvía únicamente el TXID/hash de la transacción, sin espacios.',
        'invalid_amount': '❌ Introduce únicamente un importe en USDT.\n\nEjemplo: 500',
        'no_requests': '📋 Todavía no tienes ninguna solicitud de préstamo.',
        'referral_new_user': '🎉 ¡NUEVO REFERIDO!\n\n👤 {name} acaba de registrarse con tu enlace.\n\n🎁 Referido registrado correctamente.\n💰 Recompensa potencial: 5 USDT\n⏳ Estado: esperando las condiciones del programa.',
        'referral_linked': '🎁 ¡REFERIDO REGISTRADO!\n👤 Tu referente: {name}\n✅ Tu registro se ha asociado a su enlace.\n💰 Recompensa potencial del referente: 5 USDT\n⏳ Estado: esperando las condiciones del programa.',
        'active_loan_button': '💳 Mi préstamo activo',
        'cancel_button': '❌ Cancelar',
        'show_guarantee_address': '🔐 Ver dirección de garantía',
        'loan_stage_update': "📊 ACTUALIZACIÓN DE SU SOLICITUD\n\n🆔 Solicitud: #{request_id}\n📌 Nueva etapa: {stage_label}\n\nSu solicitud ha sido actualizada.",
        'due_3d': '🔔 RECORDATORIO DE PAGO\n\n💳 Préstamo: #{loan_id}\n📄 Cuota: #{installment_number}\n📅 Fecha: {due_date}\n💰 Importe: {amount:.2f} USDT\n\nTu cuota vence en 3 días.\n\nConsulta tu cuenta para más detalles.',
        'due_today': '📅 PAGO VENCE HOY\n\n💳 Préstamo: #{loan_id}\n📄 Cuota: #{installment_number}\n💰 Importe: {amount:.2f} USDT\n\nEsta cuota vence hoy.\nConsulta tu cuenta para más detalles.',
        'due_overdue': '⚠️ PAGO VENCIDO\n\n💳 Préstamo: #{loan_id}\n📄 Cuota: #{installment_number}\n📅 Fecha de vencimiento: {due_date}\n💰 Importe: {amount:.2f} USDT\n\nEsta cuota está vencida.\nConsulta tu cuenta para más detalles.',
    },
    'pt': {
        'generic_error': '⚠️ Não foi possível apresentar esta mensagem neste momento.',
        'language_prompt': '🌐 Escolha o seu idioma:',
        'language_changed': '✅ Idioma atualizado.',
        'language_invalid': '🌐 Escolha um idioma usando um dos botões abaixo.',
        'loan_not_associated': '❌ Este empréstimo não está associado à sua conta.',
        'no_approved_loan': 'ℹ️ Nenhum empréstimo aprovado ou ativo está atualmente associado à sua conta.',
        'no_schedule': '📅 PLANO DE PAGAMENTOS\n\nAinda não há nenhuma prestação registada.',
        'network_select': '⚠️ Selecione a sua rede pressionando TRC20 ou BEP20.',
        'invalid_txid': '❌ TXID inválido.\n\nEnvie apenas o TXID/hash da transação, sem espaços.',
        'invalid_amount': '❌ Introduza apenas um valor em USDT.\n\nExemplo: 500',
        'no_requests': '📋 Ainda não tem nenhum pedido de empréstimo.',
        'referral_new_user': '🎉 NOVA REFERÊNCIA!\n\n👤 {name} acabou de se registar através do seu link.\n\n🎁 Referência registada com sucesso.\n💰 Recompensa potencial: 5 USDT\n⏳ Estado: aguardando as condições do programa.',
        'referral_linked': '🎁 REFERÊNCIA REGISTADA!\n👤 O seu referente: {name}\n✅ O seu registo foi associado ao respetivo link.\n💰 Recompensa potencial do referente: 5 USDT\n⏳ Estado: aguardando as condições do programa.',
        'active_loan_button': '💳 Meu empréstimo ativo',
        'cancel_button': '❌ Cancelar',
        'show_guarantee_address': '🔐 Ver endereço da garantia',
        'loan_stage_update': "📊 ATUALIZAÇÃO DO SEU PEDIDO\n\n🆔 Pedido: #{request_id}\n📌 Nova etapa: {stage_label}\n\nO seu pedido foi atualizado.",
        'due_3d': '🔔 LEMBRETE DE PAGAMENTO\n\n💳 Empréstimo: #{loan_id}\n📄 Prestação: #{installment_number}\n📅 Data: {due_date}\n💰 Valor: {amount:.2f} USDT\n\nA sua prestação vence em 3 dias.\n\nConsulte a sua conta para mais detalhes.',
        'due_today': '📅 PAGAMENTO VENCE HOJE\n\n💳 Empréstimo: #{loan_id}\n📄 Prestação: #{installment_number}\n💰 Valor: {amount:.2f} USDT\n\nEsta prestação vence hoje.\nConsulte a sua conta para mais detalhes.',
        'due_overdue': '⚠️ PAGAMENTO EM ATRASO\n\n💳 Empréstimo: #{loan_id}\n📄 Prestação: #{installment_number}\n📅 Data de vencimento: {due_date}\n💰 Valor: {amount:.2f} USDT\n\nEsta prestação está em atraso.\nConsulte a sua conta para mais detalhes.',
    },
}
for _lang, _values in _GLOBAL_CLIENT_TEXT.items():
    TEXT[_lang].update(_values)
    TEXT[_lang].update(_values)

def tr(telegram_id, key, **kwargs):
    """Retourne le texte client dans la langue enregistrée."""
    lang = get_client_language(telegram_id)

    language_texts = TEXT.get(lang, {})
    text = language_texts.get(key)

    # Never fall back to French for a non-French client.
    # A missing translation uses a generic message in the client language.
    if text is None:
        text = language_texts.get("generic_error")
        print(f"⚠️ Missing translation: lang={lang}, key={key}")

    if text is None:
        text = "⚠️ Unable to display this message right now." if lang == "en" else "⚠️ Impossible d'afficher ce message pour le moment."

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
