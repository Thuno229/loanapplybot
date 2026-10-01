from storage import DB_PATH
import sqlite3
from i18n import get_client_language


async def send_notification_once(
    bot,
    telegram_id,
    notification_type,
    reference_id,
    text,
    reply_markup=None,
):
    """
    Envoie une notification une seule fois.
    Une notification échouée peut être retentée.
    """

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(
            """
            INSERT OR IGNORE INTO notification_log
            (telegram_id, notification_type, reference_id)
            VALUES (?, ?, ?)
            """,
            (
                int(telegram_id),
                str(notification_type),
                str(reference_id),
            ),
        )

        inserted = cur.rowcount
        conn.commit()

        if inserted == 0:
            return False

        try:
            await bot.send_message(
                chat_id=int(telegram_id),
                text=text,
                reply_markup=reply_markup,
            )
            return True

        except Exception:
            cur.execute(
                """
                DELETE FROM notification_log
                WHERE telegram_id = ?
                  AND notification_type = ?
                  AND reference_id = ?
                """,
                (
                    int(telegram_id),
                    str(notification_type),
                    str(reference_id),
                ),
            )
            conn.commit()
            raise

    finally:
        conn.close()


# =========================================================
# NOTIFICATIONS ADMIN → CLIENT
# =========================================================

def get_client_notification_language(telegram_id):
    """Use the same canonical language resolver as the rest of the bot."""
    return get_client_language(telegram_id)


ADMIN_NOTIFICATION_TEMPLATES = {

    "kyc": {
        "fr": (
            "🪪 RAPPEL KYC\n\n"
            "Votre profil indique qu'une étape KYC doit être complétée "
            "ou vérifiée.\n\n"
            "Ouvrez la section KYC de votre espace pour consulter votre "
            "statut et les étapes disponibles.\n\n"
            "Si votre KYC a déjà été envoyé, aucune nouvelle action "
            "n'est nécessaire tant que le statut n'a pas changé."
        ),

        "en": (
            "🪪 KYC REMINDER\n\n"
            "Your profile indicates that a KYC step needs to be completed "
            "or checked.\n\n"
            "Open the KYC section of your account to view your status "
            "and available steps.\n\n"
            "If your KYC has already been submitted, no further action "
            "is required until the status changes."
        ),

        "es": (
            "🪪 RECORDATORIO KYC\n\n"
            "Su perfil indica que un paso de KYC debe completarse "
            "o verificarse.\n\n"
            "Abra la sección KYC de su cuenta para consultar su estado "
            "y los pasos disponibles.\n\n"
            "Si su KYC ya fue enviado, no es necesaria ninguna otra acción "
            "hasta que cambie el estado."
        ),

        "pt": (
            "🪪 LEMBRETE KYC\n\n"
            "O seu perfil indica que uma etapa KYC precisa ser concluída "
            "ou verificada.\n\n"
            "Abra a seção KYC da sua conta para consultar o seu estado "
            "e as etapas disponíveis.\n\n"
            "Se o seu KYC já foi enviado, nenhuma ação adicional é necessária "
            "até que o estado seja atualizado."
        ),
    },

    "loan": {
        "fr": (
            "💰 INFORMATION SUR VOTRE DOSSIER DE PRÊT\n\n"
            "Vous pouvez consulter votre espace pour vérifier les "
            "informations relatives à votre demande de prêt et les étapes "
            "disponibles pour votre dossier.\n\n"
            "Une demande de prêt reste soumise à vérification et ne "
            "constitue pas une approbation automatique."
        ),

        "en": (
            "💰 LOAN APPLICATION INFORMATION\n\n"
            "You can open your account to review the information related "
            "to your loan application and the steps available for your file.\n\n"
            "A loan application remains subject to verification and does "
            "not constitute automatic approval."
        ),

        "es": (
            "💰 INFORMACIÓN SOBRE SU SOLICITUD DE PRÉSTAMO\n\n"
            "Puede abrir su cuenta para consultar la información relacionada "
            "con su solicitud de préstamo y las etapas disponibles.\n\n"
            "Una solicitud de préstamo sigue sujeta a verificación y no "
            "constituye una aprobación automática."
        ),

        "pt": (
            "💰 INFORMAÇÃO SOBRE O SEU PEDIDO DE EMPRÉSTIMO\n\n"
            "Pode abrir a sua conta para consultar as informações relacionadas "
            "com o seu pedido de empréstimo e as etapas disponíveis.\n\n"
            "Um pedido de empréstimo continua sujeito a verificação e não "
            "constitui uma aprovação automática."
        ),
    },

    "guarantee": {
        "fr": (
            "📋 INFORMATION SUR VOTRE DOSSIER\n\n"
            "Une étape de votre dossier liée à la garantie doit être "
            "consultée ou vérifiée.\n\n"
            "Ouvrez votre demande pour consulter les informations affichées "
            "et l'état actuel de votre dossier.\n\n"
            "⚠️ Le bot ne considère pas une déclaration comme une preuve "
            "automatique de paiement."
        ),

        "en": (
            "📋 INFORMATION ABOUT YOUR FILE\n\n"
            "A step in your file related to the guarantee needs to be "
            "checked or reviewed.\n\n"
            "Open your application to view the displayed information "
            "and the current status of your file.\n\n"
            "⚠️ The bot does not treat a declaration as automatic proof "
            "of payment."
        ),

        "es": (
            "📋 INFORMACIÓN SOBRE SU EXPEDIENTE\n\n"
            "Es necesario consultar o verificar una etapa de su expediente "
            "relacionada con la garantía.\n\n"
            "Abra su solicitud para consultar la información mostrada "
            "y el estado actual de su expediente.\n\n"
            "⚠️ El bot no considera una declaración como prueba automática "
            "de pago."
        ),

        "pt": (
            "📋 INFORMAÇÃO SOBRE O SEU PROCESSO\n\n"
            "Uma etapa do seu processo relacionada com a garantia precisa "
            "ser consultada ou verificada.\n\n"
            "Abra o seu pedido para consultar as informações apresentadas "
            "e o estado atual do processo.\n\n"
            "⚠️ O bot não considera uma declaração como prova automática "
            "de pagamento."
        ),
    },

    "txid": {
        "fr": (
            "🧾 INFORMATION : TXID MANQUANT\n\n"
            "Une référence TXID n'est pas encore enregistrée dans votre "
            "dossier.\n\n"
            "Si une transaction réelle a déjà été effectuée, consultez "
            "votre dossier afin de fournir la référence correspondant "
            "à cette transaction.\n\n"
            "⚠️ N'indiquez jamais un TXID inventé ou qui ne correspond "
            "pas à une transaction réelle."
        ),

        "en": (
            "🧾 INFORMATION: TXID MISSING\n\n"
            "A TXID reference has not yet been recorded in your file.\n\n"
            "If a real transaction has already been made, check your file "
            "to provide the reference corresponding to that transaction.\n\n"
            "⚠️ Never provide an invented TXID or one that does not "
            "correspond to a real transaction."
        ),

        "es": (
            "🧾 INFORMACIÓN: FALTA EL TXID\n\n"
            "Todavía no se ha registrado una referencia TXID en su expediente.\n\n"
            "Si ya se realizó una transacción real, consulte su expediente "
            "para proporcionar la referencia correspondiente.\n\n"
            "⚠️ Nunca indique un TXID inventado o que no corresponda "
            "a una transacción real."
        ),

        "pt": (
            "🧾 INFORMAÇÃO: TXID EM FALTA\n\n"
            "Ainda não foi registada uma referência TXID no seu processo.\n\n"
            "Se uma transação real já foi efetuada, consulte o seu processo "
            "para fornecer a referência correspondente.\n\n"
            "⚠️ Nunca forneça um TXID inventado ou que não corresponda "
            "a uma transação real."
        ),
    },
}


async def send_admin_notification(bot, telegram_id, notification_type):
    """
    Envoie une notification administrative dans la langue du client.

    Chaque clic admin crée une référence unique :
    l'administrateur peut donc renvoyer la notification quand nécessaire.
    """

    language = get_client_notification_language(telegram_id)

    templates = ADMIN_NOTIFICATION_TEMPLATES.get(notification_type)

    if not templates:
        raise ValueError(
            f"Type de notification inconnu : {notification_type}"
        )

    message = templates.get(language) or templates.get("en") or next(iter(templates.values()))

    import time
    reference_id = f"admin_{notification_type}_{time.time_ns()}"

    return await send_notification_once(
        bot=bot,
        telegram_id=telegram_id,
        notification_type=f"admin_{notification_type}",
        reference_id=reference_id,
        text=message,
    )
