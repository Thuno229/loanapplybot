from pathlib import Path
import re

p = Path("bot.py")
s = p.read_text()

pattern = r'(?ms)^    elif text == t\["loan"\]:\n.*?(?=^    elif text == t\["history"\]:)'

replacement = '''    elif text == t["loan"]:
        user = get_user(user_id)
        kyc_status = user[13] or "not_submitted"

        if kyc_status != "approved":
            if kyc_status == "pending":
                message = (
                    "⏳ Votre vérification KYC est en cours.\\n\\n"
                    "Vous devez attendre sa validation avant de demander un prêt."
                )
            elif kyc_status == "rejected":
                message = (
                    "❌ Votre vérification KYC a été rejetée.\\n\\n"
                    "Veuillez effectuer à nouveau votre KYC avant de demander un prêt."
                )
            else:
                message = (
                    "❌ Demande de prêt impossible.\\n\\n"
                    "🪪 Vous devez d'abord effectuer votre vérification KYC.\\n\\n"
                    "Appuyez sur « 🪪 Vérification KYC » dans le menu, "
                    "puis envoyez votre document d'identité."
                )

            await update.message.reply_text(message)
            return

        context.user_data["awaiting_loan_amount"] = True

        await update.message.reply_text(
            "💰 Entrez le montant du prêt souhaité en USDT.\\n\\n"
            "📌 Minimum : 500 USDT\\n"
            "📌 Maximum : 50 000 USDT\\n\\n"
            "Exemple : 500"
        )
        return

'''

new_s, count = re.subn(
    pattern,
    lambda match: replacement,
    s,
    count=1
)

if count != 1:
    print("❌ Bloc loan introuvable")
    raise SystemExit(1)

p.write_text(new_s)
print("✅ Bloc loan remplacé proprement")
