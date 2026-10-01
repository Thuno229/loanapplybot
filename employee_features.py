"""Employee/referral dashboard for LoanApply24Bot.

This module intentionally keeps commission activation under administrator control.
It does not mark a commission available merely because a client claims to have paid.
"""
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from storage import DB_PATH

ADMIN_ID = 8266012108
DB = DB_PATH


def db():
    return sqlite3.connect(DB)


def ensure_employee_schema():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS employees (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS employee_commissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        referred_id INTEGER,
        base_amount REAL NOT NULL DEFAULT 0,
        employee_share REAL NOT NULL DEFAULT 0,
        company_share REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'pending',
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        available_at TIMESTAMP,
        paid_at TIMESTAMP,
        loan_request_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS client_confirmations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        message TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        responded_at TIMESTAMP
    );
    """)
    # Ajouter la colonne sur une installation existante
    columns = [row[1] for row in conn.execute("PRAGMA table_info(employee_commissions)").fetchall()]
    if "loan_request_id" not in columns:
        conn.execute("ALTER TABLE employee_commissions ADD COLUMN loan_request_id INTEGER")

    conn.commit()
    conn.close()


def create_commission_for_loan(conn, loan_request_id, referred_id, guarantee_amount):
    """Crée une commission en attente pour le prêt d'un filleul."""
    if not referred_id or guarantee_amount <= 0:
        return None

    employee = conn.execute(
        """
        SELECT r.referrer_id
        FROM referrals r
        JOIN employees e ON e.telegram_id = r.referrer_id
        WHERE r.referred_id = ?
          AND r.status = 'completed'
          AND e.active = 1
        LIMIT 1
        """,
        (referred_id,),
    ).fetchone()

    if not employee:
        return None

    employee_id = employee[0]

    existing = conn.execute(
        """
        SELECT id
        FROM employee_commissions
        WHERE loan_request_id = ?
        LIMIT 1
        """,
        (loan_request_id,),
    ).fetchone()

    if existing:
        return existing[0]

    employee_share = round(guarantee_amount * 0.50, 8)
    company_share = round(guarantee_amount * 0.50, 8)

    cur = conn.execute(
        """
        INSERT INTO employee_commissions
        (
            employee_id,
            referred_id,
            base_amount,
            employee_share,
            company_share,
            status,
            note,
            loan_request_id
        )
        VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)
        """,
        (
            employee_id,
            referred_id,
            guarantee_amount,
            employee_share,
            company_share,
            "Garantie 15 %; partage 50/50; validation administrative requise.",
            loan_request_id,
        ),
    )

    return cur.lastrowid


def is_admin(update):
    return bool(update.effective_user and update.effective_user.id == ADMIN_ID)


def is_employee(telegram_id):
    conn = db()
    row = conn.execute(
        "SELECT 1 FROM employees WHERE telegram_id = ? AND active = 1",
        (telegram_id,),
    ).fetchone()
    conn.close()
    return row is not None


def employee_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Mes filleuls", callback_data="employee_referrals")],
        [InlineKeyboardButton("💰 Mes commissions", callback_data="employee_commissions")],
        [InlineKeyboardButton("🔗 Mon lien", callback_data="employee_link")],
    ])


def admin_employee_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Liste des employés", callback_data="admin_employee_list")],
        [InlineKeyboardButton("➕ Ajouter un employé", callback_data="admin_employee_help")],
        [InlineKeyboardButton("📊 Commissions à valider", callback_data="admin_employee_pending")],
        [InlineKeyboardButton("🔔 Envoyer une demande de confirmation", callback_data="admin_confirmation_help")],
    ])


async def employee_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_employee(uid):
        await update.message.reply_text("❌ Cette section est réservée aux employés autorisés.")
        return
    await update.message.reply_text(
        "💼 ESPACE EMPLOYÉ\n\n"
        "Consultez vos filleuls et l'état de vos commissions.",
        reply_markup=employee_keyboard(),
    )


async def admin_employee_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Accès réservé à l'administrateur.")
        return
    await update.message.reply_text(
        "👔 GESTION DES EMPLOYÉS\n\n"
        "Les commissions sont calculées selon la règle 50/50 et restent sous contrôle administratif jusqu'à leur validation.",
        reply_markup=admin_employee_keyboard(),
    )


async def employee_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = update.effective_user.id
    data = q.data

    if data.startswith("employee_") and not is_employee(uid):
        await q.edit_message_text("❌ Accès réservé aux employés autorisés.")
        return

    conn = db()
    try:
        if data == "employee_link":
            link = f"https://t.me/LoanApply24Bot?start=ref_{uid}"
            await q.edit_message_text(
                f"🔗 VOTRE LIEN PERSONNEL\n\n{link}\n\n"
                "Les inscriptions effectuées avec ce lien sont attribuées à votre compte.",
                reply_markup=employee_keyboard(),
            )
            return

        if data == "employee_referrals":
            rows = conn.execute("""
                SELECT u.telegram_id, u.username, u.first_name, r.status
                FROM referrals r
                JOIN users u ON u.telegram_id = r.referred_id
                WHERE r.referrer_id = ?
                ORDER BY r.id DESC
                LIMIT 50
            """, (uid,)).fetchall()
            if not rows:
                text = "👥 MES FILLEULS\n\nAucun filleul enregistré."
            else:
                lines = ["👥 MES FILLEULS\n"]
                for tg, username, first, status in rows:
                    label = f"@{username}" if username else (first or str(tg))
                    lines.append(f"• {label} — {status}")
                text = "\n".join(lines)
            await q.edit_message_text(text, reply_markup=employee_keyboard())
            return

        if data == "employee_commissions":
            pending = conn.execute(
                "SELECT COALESCE(SUM(employee_share),0) FROM employee_commissions WHERE employee_id=? AND status='pending'",
                (uid,),
            ).fetchone()[0]
            available = conn.execute(
                "SELECT COALESCE(SUM(employee_share),0) FROM employee_commissions WHERE employee_id=? AND status='available'",
                (uid,),
            ).fetchone()[0]
            paid = conn.execute(
                "SELECT COALESCE(SUM(employee_share),0) FROM employee_commissions WHERE employee_id=? AND status='paid'",
                (uid,),
            ).fetchone()[0]
            await q.edit_message_text(
                "💰 MES COMMISSIONS\n\n"
                f"⏳ En attente : {pending:.2f} USDT\n"
                f"✅ Disponible : {available:.2f} USDT\n"
                f"💸 Déjà retiré : {paid:.2f} USDT\n\n"
                "Règle : 50 % employé / 50 % entreprise.\n"
                "La disponibilité est validée par l'administration après vérification des conditions du programme.",
                reply_markup=employee_keyboard(),
            )
            return
    finally:
        conn.close()


async def admin_employee_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(update):
        await q.edit_message_text("❌ Accès réservé à l'administrateur.")
        return
    data = q.data
    conn = db()
    try:
        if data == "admin_employee_open":
            await q.edit_message_text(
                "👔 GESTION DES EMPLOYÉS\n\nGérez les employés, les filleuls et les commissions.",
                reply_markup=admin_employee_keyboard(),
            )
            return

        if data == "admin_employee_help":
            await q.edit_message_text(
                "➕ AJOUTER UN EMPLOYÉ\n\n"
                "Utilisez la commande :\n\n"
                "/employe_add TELEGRAM_ID\n\n"
                "Exemple : /employe_add 123456789\n\n"
                "Pour désactiver : /employe_remove TELEGRAM_ID",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Retour", callback_data="admin_employee_back")]])
            )
            return
        if data == "admin_employee_back":
            await q.edit_message_text("👔 GESTION DES EMPLOYÉS", reply_markup=admin_employee_keyboard())
            return
        if data == "admin_employee_list":
            rows = conn.execute("SELECT telegram_id, username, active FROM employees ORDER BY created_at DESC").fetchall()
            lines = ["👥 EMPLOYÉS\n"]
            if not rows:
                lines.append("Aucun employé.")
            else:
                for tg, username, active in rows:
                    lines.append(f"• {tg} — @{username or '-'} — {'🟢 actif' if active else '🔴 désactivé'}")
            await q.edit_message_text("\n".join(lines), reply_markup=admin_employee_keyboard())
            return
        if data == "admin_employee_pending":
            rows = conn.execute("""
                SELECT id, employee_id, referred_id, base_amount, employee_share, created_at
                FROM employee_commissions WHERE status='pending' ORDER BY id DESC LIMIT 30
            """).fetchall()
            buttons = []
            if not rows:
                text = "📊 Aucune commission en attente de validation."
            else:
                text = "📊 COMMISSIONS EN ATTENTE\n\nSélectionnez une commission à valider :"
                for cid, eid, rid, base, share, created in rows:
                    buttons.append([InlineKeyboardButton(
                        f"#{cid} • {share:.2f} USDT • employé {eid}",
                        callback_data=f"admin_commission_validate:{cid}"
                    )])
            buttons.append([InlineKeyboardButton("↩️ Retour", callback_data="admin_employee_back")])
            await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
            return
        if data.startswith("admin_commission_validate:"):
            cid = int(data.split(":",1)[1])
            cur = conn.execute("UPDATE employee_commissions SET status='available', available_at=CURRENT_TIMESTAMP WHERE id=? AND status='pending'", (cid,))
            conn.commit()
            if cur.rowcount:
                row = conn.execute("SELECT employee_id, employee_share FROM employee_commissions WHERE id=?", (cid,)).fetchone()
                if row:
                    try:
                        await context.bot.send_message(row[0], f"✅ Commission #{cid} disponible : {row[1]:.2f} USDT")
                    except Exception:
                        pass
                await q.answer("Commission rendue disponible.", show_alert=True)
            else:
                await q.answer("Commission déjà traitée.", show_alert=True)
            return
    finally:
        conn.close()


async def employee_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Accès réservé à l'administrateur.")
        return
    if not context.args:
        await update.message.reply_text("Usage : /employe_add TELEGRAM_ID")
        return
    try:
        tg = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID invalide.")
        return
    conn = db()
    row = conn.execute("SELECT username FROM users WHERE telegram_id=?", (tg,)).fetchone()
    username = row[0] if row else None
    conn.execute("INSERT INTO employees(telegram_id, username, active) VALUES(?,?,1) ON CONFLICT(telegram_id) DO UPDATE SET username=excluded.username, active=1", (tg, username))
    conn.commit(); conn.close()
    await update.message.reply_text(f"✅ {tg} est maintenant employé actif.")


async def commission_create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Crée une commission en attente après vérification administrative.

    Usage: /commission_create EMPLOYEE_ID BASE_AMOUNT [CLIENT_ID]
    La répartition est 50/50 entre employé et entreprise.
    """
    if not is_admin(update):
        await update.message.reply_text("❌ Accès réservé à l'administrateur.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage : /commission_create EMPLOYEE_ID MONTANT_BASE [CLIENT_ID]")
        return
    try:
        employee_id = int(context.args[0])
        base_amount = float(context.args[1])
        referred_id = int(context.args[2]) if len(context.args) >= 3 else None
    except ValueError:
        await update.message.reply_text("❌ Paramètres invalides.")
        return
    if base_amount <= 0:
        await update.message.reply_text("❌ Le montant doit être supérieur à 0.")
        return
    conn = db()
    if not conn.execute("SELECT 1 FROM employees WHERE telegram_id=? AND active=1", (employee_id,)).fetchone():
        conn.close()
        await update.message.reply_text("❌ Employé introuvable ou désactivé.")
        return
    employee_share = round(base_amount * 0.50, 8)
    company_share = round(base_amount * 0.50, 8)
    cur = conn.execute(
        """INSERT INTO employee_commissions
        (employee_id,referred_id,base_amount,employee_share,company_share,status,note)
        VALUES (?,?,?,?,?,'pending','Créée après vérification administrative; validation requise avant disponibilité.')""",
        (employee_id, referred_id, base_amount, employee_share, company_share),
    )
    cid = cur.lastrowid
    conn.commit(); conn.close()
    try:
        await context.bot.send_message(
            employee_id,
            f"💰 Commission #{cid} enregistrée\n\nBase : {base_amount:.2f} USDT\nVotre part (50 %) : {employee_share:.2f} USDT\n\n⏳ Statut : en attente de validation administrative."
        )
    except Exception:
        pass
    await update.message.reply_text(
        f"✅ Commission #{cid} créée.\nEmployé : {employee_id}\nBase : {base_amount:.2f} USDT\nEmployé 50 % : {employee_share:.2f} USDT\nEntreprise 50 % : {company_share:.2f} USDT\nStatut : ⏳ en attente."
    )


async def employee_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("❌ Accès réservé à l'administrateur.")
        return
    if not context.args:
        await update.message.reply_text("Usage : /employe_remove TELEGRAM_ID")
        return
    try:
        tg = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Telegram ID invalide.")
        return
    conn = db(); conn.execute("UPDATE employees SET active=0 WHERE telegram_id=?", (tg,)); conn.commit(); conn.close()
    await update.message.reply_text(f"🔴 Employé {tg} désactivé.")


async def send_confirmation_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin(update):
        return
    await q.edit_message_text(
        "🔔 DEMANDE DE CONFIRMATION CLIENT\n\n"
        "Pour éviter les messages ambigus, cette fonction envoie un modèle de confirmation au client sélectionné.\n\n"
        "Utilisez ensuite le menu Notifications client pour choisir le client.",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Retour", callback_data="admin_back")]])
    )


async def admin_confirmation_for_user(update: Update, context: ContextTypes.DEFAULT_TYPE, telegram_id: int):
    if not is_admin(update):
        return
    conn = db()
    conn.execute("INSERT INTO client_confirmations(telegram_id, admin_id, message) VALUES(?,?,?)", (telegram_id, ADMIN_ID, "Veuillez confirmer ou rejeter la décision/condition communiquée par l'administration."))
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit(); conn.close()
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Accepter", callback_data=f"client_confirm:{cid}:accept"), InlineKeyboardButton("❌ Rejeter", callback_data=f"client_confirm:{cid}:reject")]])
    await context.bot.send_message(telegram_id, "🔔 CONFIRMATION DEMANDÉE\n\nVeuillez confirmer ou rejeter la demande transmise par l'administration.", reply_markup=keyboard)


async def client_confirmation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    parts = q.data.split(":")
    if len(parts) != 3:
        return
    cid, decision = int(parts[1]), parts[2]
    conn = db()
    row = conn.execute("SELECT telegram_id, status FROM client_confirmations WHERE id=?", (cid,)).fetchone()
    if not row or row[0] != update.effective_user.id:
        conn.close(); await q.answer("❌ Confirmation invalide.", show_alert=True); return
    if row[1] != 'pending':
        conn.close(); await q.edit_message_text("ℹ️ Cette confirmation a déjà été traitée."); return
    status = 'accepted' if decision == 'accept' else 'rejected'
    conn.execute("UPDATE client_confirmations SET status=?, responded_at=CURRENT_TIMESTAMP WHERE id=?", (status,cid))
    conn.commit(); conn.close()
    await q.edit_message_text("✅ Votre réponse a été enregistrée." if decision == 'accept' else "❌ Votre rejet a été enregistré.")


def employee_handlers():
    ensure_employee_schema()
    return [
        CommandHandler("employe", employee_menu),
        CommandHandler("employe_add", employee_admin_commands),
        CommandHandler("employe_remove", employee_remove_command),
        CommandHandler("commission_create", commission_create_command),
        CallbackQueryHandler(employee_callback, pattern=r"^employee_"),
        CallbackQueryHandler(admin_employee_callback, pattern=r"^admin_employee_"),
        CallbackQueryHandler(send_confirmation_prompt, pattern=r"^admin_confirmation_help$"),
        CallbackQueryHandler(client_confirmation_callback, pattern=r"^client_confirm:\d+:(accept|reject)$"),
    ]
