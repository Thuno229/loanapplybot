#!/usr/bin/env python3
from pathlib import Path
import sqlite3, shutil, py_compile
from datetime import datetime

P=Path(__file__).resolve().parent
DB=P/'loan_bot.db'; BOT=P/'bot.py'; ENT=P/'enterprise_features.py'
ADMIN_ID=8266012108

def backup():
    d=P/'backups'/('admin_keyboard_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    d.mkdir(parents=True,exist_ok=True)
    for f in (BOT,P/'database.py',ENT,DB):
        if f.exists(): shutil.copy2(f,d/f.name)
    print('💾 Backup:',d)

def schema():
    c=sqlite3.connect(DB,timeout=30); c.execute('PRAGMA busy_timeout=30000')
    try:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS repayment_records(id INTEGER PRIMARY KEY AUTOINCREMENT,loan_id INTEGER NOT NULL,telegram_id INTEGER NOT NULL,amount REAL NOT NULL,txid TEXT NOT NULL,recorded_by INTEGER NOT NULL,status TEXT DEFAULT 'confirmed',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS support_tickets(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id INTEGER NOT NULL,subject TEXT,message TEXT NOT NULL,status TEXT DEFAULT 'open',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,closed_at TIMESTAMP);
        """)
        c.execute("INSERT OR IGNORE INTO system_settings(key,value) VALUES('interest_rate_monthly','1.0')")
        c.commit()
    finally: c.close()
    print('🗄️ Base de données OK')

ENTERPRISE=r'''from __future__ import annotations
import sqlite3
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

DB='loan_bot.db'
ADMIN_ID=8266012108
LANGS=('fr','en','es','pt')
T={
'fr':{'no':'ℹ️ Aucun prêt actif ou approuvé.','status':'💳 État du prêt','schedule':'📅 Échéancier','support':'🆘 Utilisation : /support votre message','ticket':'✅ Ticket support #{id} enregistré.','admin':'❌ Commande réservée à l’administrateur.','stats':'📊 TABLEAU ENTREPRISE','repay':'🧾 Utilisation admin : /repay ID_PRÊT MONTANT TXID','tickets':'🎫 Tickets ouverts','none':'✅ Aucun ticket ouvert.','close':'Utilisation : /ticket_close ID','closed':'✅ Ticket #{id} fermé.','notfound':'❌ Ticket introuvable.','help':'🤖 /loanstatus — état du prêt\n/schedule — échéancier\n/support message — support'},
'en':{'no':'ℹ️ No active or approved loan.','status':'💳 Loan status','schedule':'📅 Repayment schedule','support':'🆘 Usage: /support your message','ticket':'✅ Support ticket #{id} created.','admin':'❌ Admin command only.','stats':'📊 ENTERPRISE DASHBOARD','repay':'🧾 Admin usage: /repay LOAN_ID AMOUNT TXID','tickets':'🎫 Open tickets','none':'✅ No open tickets.','close':'Usage: /ticket_close ID','closed':'✅ Ticket #{id} closed.','notfound':'❌ Ticket not found.','help':'🤖 /loanstatus — loan status\n/schedule — repayment schedule\n/support message — support'},
'es':{'no':'ℹ️ No hay préstamo activo o aprobado.','status':'💳 Estado del préstamo','schedule':'📅 Calendario','support':'🆘 Uso: /support su mensaje','ticket':'✅ Ticket de soporte #{id} registrado.','admin':'❌ Solo para el administrador.','stats':'📊 PANEL DE EMPRESA','repay':'🧾 Uso admin: /repay ID_PRÉSTAMO IMPORTE TXID','tickets':'🎫 Tickets abiertos','none':'✅ No hay tickets abiertos.','close':'Uso: /ticket_close ID','closed':'✅ Ticket #{id} cerrado.','notfound':'❌ Ticket no encontrado.','help':'🤖 /loanstatus — estado\n/schedule — calendario\n/support mensaje — soporte'},
'pt':{'no':'ℹ️ Nenhum empréstimo ativo ou aprovado.','status':'💳 Estado do empréstimo','schedule':'📅 Calendário','support':'🆘 Uso: /support sua mensagem','ticket':'✅ Ticket de suporte #{id} registrado.','admin':'❌ Apenas para o administrador.','stats':'📊 PAINEL DA EMPRESA','repay':'🧾 Uso admin: /repay ID_EMPRÉSTIMO VALOR TXID','tickets':'🎫 Tickets abertos','none':'✅ Nenhum ticket aberto.','close':'Uso: /ticket_close ID','closed':'✅ Ticket #{id} fechado.','notfound':'❌ Ticket não encontrado.','help':'🤖 /loanstatus — estado\n/schedule — calendário\n/support mensagem — suporte'}}

def _lang(update):
    c=sqlite3.connect(DB)
    try: r=c.execute('SELECT language FROM users WHERE telegram_id=?',(update.effective_user.id,)).fetchone()
    finally: c.close()
    return r[0] if r and r[0] in LANGS else 'fr'

def ensure_enterprise_schema():
    c=sqlite3.connect(DB,timeout=30)
    try:
        c.execute('PRAGMA busy_timeout=30000')
        c.executescript("""
        CREATE TABLE IF NOT EXISTS system_settings(key TEXT PRIMARY KEY,value TEXT,updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS repayment_records(id INTEGER PRIMARY KEY AUTOINCREMENT,loan_id INTEGER NOT NULL,telegram_id INTEGER NOT NULL,amount REAL NOT NULL,txid TEXT NOT NULL,recorded_by INTEGER NOT NULL,status TEXT DEFAULT 'confirmed',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS support_tickets(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id INTEGER NOT NULL,subject TEXT,message TEXT NOT NULL,status TEXT DEFAULT 'open',created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,closed_at TIMESTAMP);
        """); c.commit()
    finally: c.close()

async def loanstatus(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type!='private': return
    l=_lang(update); c=sqlite3.connect(DB)
    try: r=c.execute("SELECT id,amount,interest_rate,total_repayment,amount_repaid,status,next_due_date FROM loans WHERE telegram_id=? AND status NOT IN('rejected','cancelled') ORDER BY id DESC LIMIT 1",(update.effective_user.id,)).fetchone()
    finally: c.close()
    if not r: await update.message.reply_text(T[l]['no']); return
    await update.message.reply_text(f"{T[l]['status']} #{r[0]}\n\nStatus: {r[5]}\n💰 Amount: {r[1]:.2f} USDT\n📈 Rate: {r[2]:g}%\n💳 Total: {r[3]:.2f} USDT\n💸 Repaid: {float(r[4] or 0):.2f} USDT\n📉 Remaining: {max(float(r[3])-float(r[4] or 0),0):.2f} USDT\n📅 Next: {r[6] or '-'}")

async def schedule(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type!='private': return
    l=_lang(update); c=sqlite3.connect(DB)
    try:
        loan=c.execute("SELECT id FROM loans WHERE telegram_id=? AND status NOT IN('rejected','cancelled') ORDER BY id DESC LIMIT 1",(update.effective_user.id,)).fetchone()
        rows=c.execute('SELECT installment_number,due_date,amount,status FROM loan_installments WHERE loan_id=? ORDER BY installment_number',(loan[0],)).fetchall() if loan else []
    finally: c.close()
    if not rows: await update.message.reply_text(T[l]['schedule']+'\n\nNo schedule available.'); return
    await update.message.reply_text(T[l]['schedule']+f' #{loan[0]}\n\n'+'\n'.join(f'#{a} — {b or "-"} — {c:.2f} USDT — {d}' for a,b,c,d in rows[:25]))

async def support(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type!='private': return
    l=_lang(update); msg=' '.join(context.args).strip()
    if not msg: await update.message.reply_text(T[l]['support']); return
    c=sqlite3.connect(DB)
    try:
        cur=c.execute("INSERT INTO support_tickets(telegram_id,subject,message,status) VALUES(?,?,?,'open')",(update.effective_user.id,'Telegram support',msg[:4000])); tid=cur.lastrowid; c.commit()
    finally: c.close()
    await update.message.reply_text(T[l]['ticket'].format(id=tid))

async def enterprise(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: await update.message.reply_text(T[_lang(update)]['admin']); return
    c=sqlite3.connect(DB)
    try:
        users=c.execute('SELECT COUNT(*) FROM users').fetchone()[0]; req=c.execute('SELECT COUNT(*) FROM loan_requests').fetchone()[0]; active=c.execute("SELECT COUNT(*) FROM loans WHERE status='active'").fetchone()[0]; kyc=c.execute("SELECT COUNT(*) FROM users WHERE kyc_status='pending'").fetchone()[0]; tickets=c.execute("SELECT COUNT(*) FROM support_tickets WHERE status='open'").fetchone()[0]; disb=c.execute("SELECT COALESCE(SUM(disbursement_amount),0) FROM loans WHERE disbursement_status='disbursed'").fetchone()[0]; rep=c.execute("SELECT COALESCE(SUM(amount),0) FROM repayment_records WHERE status='confirmed'").fetchone()[0]; overdue=c.execute("SELECT COUNT(*) FROM loan_installments WHERE status!='paid' AND due_date<date('now')").fetchone()[0]
    finally: c.close()
    await update.message.reply_text(f"{T['fr']['stats']}\n\n👥 Utilisateurs: {users}\n🪪 KYC en attente: {kyc}\n💰 Demandes: {req}\n💳 Prêts actifs: {active}\n📅 Échéances en retard: {overdue}\n💵 Décaissements enregistrés: {float(disb or 0):.2f} USDT\n💸 Remboursements enregistrés: {float(rep or 0):.2f} USDT\n🎫 Tickets ouverts: {tickets}\n\n✅ Base de données accessible")

async def tickets(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: await update.message.reply_text(T[_lang(update)]['admin']); return
    c=sqlite3.connect(DB)
    try: rows=c.execute('SELECT id,telegram_id,message FROM support_tickets WHERE status=\'open\' ORDER BY id DESC LIMIT 20').fetchall()
    finally: c.close()
    if not rows: await update.message.reply_text(T['fr']['none']); return
    await update.message.reply_text(T['fr']['tickets']+'\n\n'+'\n'.join(f"#{a} — {b} — {m[:160].replace(chr(10),' ')}" for a,b,m in rows))

async def ticket_close(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: await update.message.reply_text(T[_lang(update)]['admin']); return
    if not context.args: await update.message.reply_text(T['fr']['close']); return
    try: i=int(context.args[0])
    except: await update.message.reply_text(T['fr']['close']); return
    c=sqlite3.connect(DB)
    try: cur=c.execute("UPDATE support_tickets SET status='closed',closed_at=CURRENT_TIMESTAMP WHERE id=? AND status='open'",(i,)); c.commit(); ok=cur.rowcount
    finally: c.close()
    await update.message.reply_text(T['fr']['closed'].format(id=i) if ok else T['fr']['notfound'])

async def repay(update:Update,context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!=ADMIN_ID: await update.message.reply_text(T[_lang(update)]['admin']); return
    if len(context.args)<3: await update.message.reply_text(T['fr']['repay']+'\n⚠️ Enregistrement administratif uniquement.'); return
    try: loan_id=int(context.args[0]); amount=float(context.args[1]); txid=context.args[2].strip()
    except: await update.message.reply_text(T['fr']['repay']); return
    if amount<=0 or len(txid)<6: await update.message.reply_text('❌ Montant ou TXID invalide.'); return
    c=sqlite3.connect(DB)
    try:
        c.execute('BEGIN IMMEDIATE'); r=c.execute('SELECT telegram_id,total_repayment,amount_repaid,status FROM loans WHERE id=?',(loan_id,)).fetchone()
        if not r: raise ValueError('prêt introuvable')
        remaining=float(r[1])-float(r[2] or 0)
        if amount>remaining+0.01: raise ValueError('montant supérieur au solde restant')
        c.execute("INSERT INTO repayment_records(loan_id,telegram_id,amount,txid,recorded_by,status) VALUES(?,?,?,?,?,'confirmed')",(loan_id,r[0],amount,txid,ADMIN_ID)); newrep=min(float(r[2] or 0)+amount,float(r[1])); status='completed' if newrep+0.01>=float(r[1]) else 'active'; c.execute("UPDATE loans SET amount_repaid=?,status=?,last_payment_at=CURRENT_TIMESTAMP,completed_at=CASE WHEN ?='completed' THEN CURRENT_TIMESTAMP ELSE completed_at END WHERE id=?",(newrep,status,status,loan_id)); c.commit()
    except Exception as e:
        c.rollback(); await update.message.reply_text('❌ '+str(e)); return
    finally: c.close()
    await update.message.reply_text(f'✅ Remboursement enregistré.\nPrêt #{loan_id}\nMontant: {amount:.2f} USDT\nTXID: {txid}')

def register_enterprise_handlers(application):
    application.add_handler(CommandHandler('enterprise',enterprise))
    application.add_handler(CommandHandler('tickets',tickets))
    application.add_handler(CommandHandler('ticket_close',ticket_close))
    application.add_handler(CommandHandler('repay',repay))
    application.add_handler(CommandHandler('loanstatus',loanstatus))
    application.add_handler(CommandHandler('schedule',schedule))
    application.add_handler(CommandHandler('support',support))

async def ignore_group_messages(update,context): return
'''

def write_enterprise():
    ENT.write_text(ENTERPRISE,encoding='utf-8'); print('🧩 enterprise_features.py corrigé')

def patch_bot():
    s=BOT.read_text(encoding='utf-8')
    if 'from enterprise_features import register_enterprise_handlers' not in s:
        s=s.replace('from database import init_database','from database import init_database\nfrom enterprise_features import register_enterprise_handlers, ensure_enterprise_schema, ignore_group_messages',1)
    if 'ensure_enterprise_schema()' not in s:
        s=s.replace('def main():\n\n    init_database()','def main():\n\n    init_database()\n    ensure_enterprise_schema()',1)
    if 'register_enterprise_handlers(application)' not in s:
        target='application = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30).build()'
        repl=target+'\n\n    application.add_handler(MessageHandler(filters.ChatType.GROUPS, ignore_group_messages), group=-10)\n    register_enterprise_handlers(application)'
        s=s.replace(target,repl,1)
    if 'rows.extend([\n            ["/enterprise", "/tickets"]' not in s:
        needle='    rows.append([about_button])'
        repl=needle+'\n\n    if user_id == ADMIN_ID:\n        rows.extend([["/enterprise", "/tickets"],["/ticket_close", "/repay"]])'
        if needle in s: s=s.replace(needle,repl,1)
        else: print('⚠️ Emplacement clavier admin introuvable')
    BOT.write_text(s,encoding='utf-8'); print('⌨️ Clavier administrateur ajouté')

def main():
    print('🚀 CORRECTION AUTOMATIQUE — ADMIN + ENTERPRISE')
    if not DB.exists(): raise SystemExit('❌ loan_bot.db introuvable')
    backup(); schema(); write_enterprise(); patch_bot()
    for f in (ENT,BOT,P/'database.py'): py_compile.compile(str(f),doraise=True)
    c=sqlite3.connect(DB)
    try:
        for t in ('system_settings','repayment_records','support_tickets'):
            if not c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(t,)).fetchone(): raise RuntimeError('table manquante: '+t)
        print('🧪 SQLite : OK')
    finally: c.close()
    print('✅ Syntaxe : OK'); print('🎉 TERMINÉ'); print('➡️ Relance : python bot.py'); print('📌 Puis teste /enterprise depuis le compte admin.')

if __name__=='__main__': main()
