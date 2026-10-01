from pathlib import Path

p = Path("bot.py")
s = p.read_text()

marker = "# =========================\n# BASE DE DONNÉES"

block = '''
# KYC — libellés multilingues
TEXT["fr"]["kyc"] = "🪪 Vérification KYC"
TEXT["en"]["kyc"] = "🪪 KYC Verification"
TEXT["es"]["kyc"] = "🪪 Verificación KYC"
TEXT["pt"]["kyc"] = "🪪 Verificação KYC"

'''

if 'TEXT["fr"]["kyc"]' not in s:
    s = s.replace(marker, block + marker, 1)

old = '''[t["profile"], t["loan"]],
        [t["referral"], t["history"]],
        [t["support"], t["language"]],'''

new = '''[t["profile"], t["loan"]],
        [t["kyc"], t["history"]],
        [t["referral"], t["support"]],
        [t["language"]],'''

if old in s and 't["kyc"]' not in s[s.find("def dashboard_keyboard"):s.find("def dashboard_keyboard")+1000]:
    s = s.replace(old, new, 1)

p.write_text(s)
print("✅ Bouton KYC préparé")
