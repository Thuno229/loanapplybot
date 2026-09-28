#!/data/data/com.termux/files/usr/bin/bash

set -e

echo "======================================"
echo "  INSTALLATION LOAN REQUEST ASSISTANT"
echo "======================================"

echo "📦 Mise à jour des paquets..."
pkg update -y
pkg install python -y

echo "🐍 Vérification de Python..."
python --version

echo "📚 Installation des dépendances..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "🔍 Vérification des fichiers principaux..."

for file in bot.py database.py admin_panel.py loan_callbacks.py kyc_flow.py notifications.py i18n.py; do
    if [ ! -f "$file" ]; then
        echo "❌ Fichier manquant : $file"
        exit 1
    fi
done

if [ ! -f "loan_bot.db" ]; then
    echo "⚠️ loan_bot.db est absent."
    echo "Le code existe, mais la base de données actuelle n'a pas été restaurée."
    exit 1
fi

echo "🧪 Vérification de la syntaxe..."
python -m py_compile bot.py
python -m py_compile admin_panel.py
python -m py_compile database.py

echo ""
echo "✅ INSTALLATION TERMINÉE"
echo ""
echo "Pour démarrer le bot :"
echo "    bash START.sh"
echo ""
