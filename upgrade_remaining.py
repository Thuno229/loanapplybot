#!/usr/bin/env python3
from pathlib import Path
import sqlite3, shutil, py_compile
from datetime import datetime

P=Path(__file__).resolve().parent
DB=P/'loan_bot.db'
STAMP=datetime.now().strftime('%Y%m%d_%H%M%S')
BACK=P/'backups'/f'remaining_upgrade_{STAMP}'
BACK.mkdir(parents=True,exist_ok=True)

for name in ['bot.py','database.py','admin_panel.py','loan_callbacks.py','i18n.py','notifications.py','kyc_flow.py','loan_bot.db']:
    f=P/name
    if f.exists(): shutil.copy2(f,BACK/name)
print('💾 Backup:', BACK)

# --- database migration ---
con=sqlite3.connect(DB,timeout=30)
con.execute('PRAGMA busy_timeout=30000')
try:
    con.executescript('''
    CREATE TABLE IF NOT EXISTS repayment_records (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      loan_id INTEGER NOT NULL, telegram_id INTEGER NOT NULL,
      amount REAL NOT NULL, txid TEXT NOT NULL, recorded_by INTEGER NOT NULL,
      status TEXT DEFAULT 'confirmed', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS support_tickets (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      telegram_id INTEGER NOT NULL, subject TEXT, message TEXT NOT NULL,
      status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      closed_at TIMESTAMP
    );
    ''')
    cols={r[1] for r in con.execute('PRAGMA table_info(loan_installments)')}
    if 'amount_paid' not in cols:
        con.execute('ALTER TABLE loan_installments ADD COLUMN amount_paid REAL DEFAULT 0')
    con.execute('UPDATE loan_installments SET amount_paid=COALESCE(amount_paid,0)')
    con.commit()
    assert con.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
finally:
    con.close()
print('🗄️ Base de données OK')

# --- database.py: future fresh databases get the same schema ---
dbpy=P/'database.py'
s=dbpy.read_text(encoding='utf-8')
s=s.replace('interest_rate REAL NOT NULL DEFAULT 5,','interest_rate REAL NOT NULL DEFAULT 1.0,')
if 'CREATE TABLE IF NOT EXISTS repayment_records' not in s:
    marker='    conn.commit()\n    conn.close()'
    addition="""    cursor.execute(\"\"\"CREATE TABLE IF NOT EXISTS repayment_records (id INTEGER PRIMARY KEY AUTOINCREMENT, loan_id INTEGER NOT NULL, telegram_id INTEGER NOT NULL, amount REAL NOT NULL, txid TEXT NOT NULL, recorded_by INTEGER NOT NULL, status TEXT DEFAULT 'confirmed', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)\"\"\")
    cursor.execute(\"\"\"CREATE TABLE IF NOT EXISTS support_tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER NOT NULL, subject TEXT, message TEXT NOT NULL, status TEXT DEFAULT 'open', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, closed_at TIMESTAMP)\"\"\")
"""
    if marker not in s: raise SystemExit('❌ database.py: zone de migration introuvable')
    s=s.replace(marker,addition+marker,1)
dbpy.write_text(s,encoding='utf-8')
print('🔧 database.py synchronisé')

# --- enterprise module ---
module=r'''import sqlite3
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
DB='loan_bot.db'
ADMIN_ID=8266012108
T={
'fr':{'none':'ℹ️ Aucun prêt actif ou approuvé.','status':'💳 État de votre prêt','schedule':'📅 Votre échéancier','support_usage':'🆘 Utilisation : /support votre message','ticket':'✅ Ticket support #{id} enregistré.','admin':'❌ Accès réservé à l’administrateur.','repay_usage':'🧾 Utilisation : /repay ID_PRÊT MONTANT TXID','repay_ok':'✅ Remboursement enregistré.\nPrêt #{id}\nMontant : {amount:.2f} USDT\nTXID : {txid}\nÉchéances soldées : {paid}','repay_err':'❌ Remboursement impossible : {reason}'},
'en':{'none':'ℹ️ No active or approved loan.','status':'💳 Your loan status','schedule':'📅 Your repayment schedule','support_usage':'🆘 Usage: /support your message','ticket':'✅ Support ticket #{id} recorded.','admin':'❌ Administrator access only.','repay_usage':'🧾 Usage: /repay LOAN_ID AMOUNT TXID','repay_ok':'✅ Repayment recorded.\nLoan #{id}\nAmount: {amount:.2f} USDT\nTXID: {txid}\nInstallments settled: {paid}','repay_err':'❌ Repayment failed: {reason}'},
'es':{'none':'ℹ️ No hay préstamo activo o aprobado.','status':'💳 Estado de su préstamo','schedule':'📅 Calendario de pagos','support_usage':'🆘 Uso: /support su mensaje','ticket':'✅ Ticket de soporte #{id} registrado.','admin':'❌ Acceso solo para el administrador.','repay_usage':'🧾 Uso: /repay ID_PRÉSTAMO IMPORTE TXID','repay_ok':'✅ Reembolso registrado.\nPréstamo #{id}\nImporte: {amount:.2f} USDT\nTXID: {txid}\nCuotas saldadas: {paid}','repay_err':'❌ Reembolso fallido: {reason}'},
'pt':{'none':'ℹ️ Nenhum empréstimo ativo ou aprovado.','status':'💳 Estado do empréstimo','schedule':'📅 Calendário de pagamentos','support_usage':'🆘 Uso: /support sua mensagem','ticket':'✅ Ticket de suporte #{id} registrado.','admin':'❌ Acesso somente do administrador.','repay_usage':'🧾 Uso: /repay ID_EMPRÉSTIMO VALOR TXID','repay_ok':'✅ Pagamento registrado.\nEmpréstimo #{id}\nValor: {amount:.2f} USDT\nTXID: {txid}\nParcelas quitadas: {paid}','repay_err':'❌ Falha no pagamento: {reason}'}}
def L(uid):
    try:
        with sqlite3.connect(DB) as c:r=c.execute('SELECT language FROM users WHERE telegram_id=?',(uid,)).fetchone()
        return r[0] if r and r[0] in T else 'fr'
    except Exception:return 'fr'
def tr(uid,k,**kw):return T[L(uid)][k].format(**kw)
def audit(action,target=None,tid=None,details=None):
    try:
        with sqlite3.connect(DB) as c:c.execute('INSERT INTO admin_actions(admin_id,action,target_type,target_id,details) VALUES(?,?,?,?,?)',(ADMIN_ID,action,target,tid,details));c.commit()
    except Exception:pass
async def loanstatus(u,c):
    if u.effective_chat.type!='private':return
    uid=u.effective_user.id
    with sqlite3.connect(DB) as x:r=x.execute("SELECT id,amount,interest_rate,total_repayment,amount_repaid,status,next_due_date FROM loans WHERE telegram_id=? AND status NOT IN ('rejected','cancelled') ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
    if not r:return await u.message.reply_text(tr(uid,'none'))
    i,a,rate,total,paid,status,due=r
    await u.message.reply_text(f"{tr(uid,'status')} #{i}\n\n🔹 Status: {status}\n💰 Montant: {a:.2f} USDT\n📈 Taux: {rate:g}% / mois\n💳 Total: {total:.2f} USDT\n💸 Remboursé: {paid or 0:.2f} USDT\n📉 Reste: {max(total-(paid or 0),0):.2f} USDT\n📅 Prochaine échéance: {due or '-'}")
async def schedule(u,c):
    if u.effective_chat.type!='private':return
    uid=u.effective_user.id
    with sqlite3.connect(DB) as x:
        loan=x.execute("SELECT id FROM loans WHERE telegram_id=? AND status NOT IN ('rejected','cancelled') ORDER BY id DESC LIMIT 1",(uid,)).fetchone()
        rows=x.execute("SELECT installment_number,due_date,amount,COALESCE(amount_paid,0),status FROM loan_installments WHERE loan_id=? ORDER BY installment_number",(loan[0],)).fetchall() if loan else []
    if not rows:return await u.message.reply_text(tr(uid,'none'))
    await u.message.reply_text(tr(uid,'schedule')+f" #{loan[0]}\n\n"+'\n'.join(f'#{n} — {d or "-"} — {a:.2f} USDT — {st} (payé {p:.2f})' for n,d,a,p,st in rows[:30]))
async def support(u,c):
    if u.effective_chat.type!='private':return
    uid=u.effective_user.id;m=' '.join(c.args).strip()
    if not m:return await u.message.reply_text(tr(uid,'support_usage'))
    with sqlite3.connect(DB) as x:
        q=x.execute("INSERT INTO support_tickets(telegram_id,subject,message,status) VALUES(?,?,?,'open')",(uid,'Telegram support',m[:4000]));tid=q.lastrowid;x.commit()
    await u.message.reply_text(tr(uid,'ticket',id=tid))
async def repay(u,c):
    if u.effective_user.id!=ADMIN_ID:return await u.message.reply_text(tr(u.effective_user.id,'admin'))
    if len(c.args)<3:return await u.message.reply_text(T['fr']['repay_usage'])
    try:lid=int(c.args[0]);amount=float(c.args[1])
    except Exception:return await u.message.reply_text(T['fr']['repay_usage'])
    txid=c.args[2].strip()
    if amount<=0 or len(txid)<6:return await u.message.reply_text(T['fr']['repay_err'].format(reason='montant/TXID invalide'))
    x=sqlite3.connect(DB)
    try:
        x.execute('BEGIN IMMEDIATE');loan=x.execute('SELECT id,telegram_id,total_repayment,amount_repaid,status FROM loans WHERE id=?',(lid,)).fetchone()
        if not loan:raise ValueError('prêt introuvable')
        remaining=float(loan[2])-float(loan[3] or 0)
        if amount>remaining+.01:raise ValueError('montant supérieur au reste')
        x.execute("INSERT INTO repayment_records(loan_id,telegram_id,amount,txid,recorded_by,status) VALUES(?,?,?,?,?,'confirmed')",(lid,loan[1],amount,txid,ADMIN_ID))
        left=amount;paidn=0
        for iid,ia,ip,st in x.execute("SELECT id,amount,COALESCE(amount_paid,0),status FROM loan_installments WHERE loan_id=? AND status!='paid' ORDER BY installment_number",(lid,)).fetchall():
            if left<=0:break
            apply=min(left,max(float(ia)-float(ip),0));new=float(ip)+apply
            if new+.00001>=float(ia):x.execute('UPDATE loan_installments SET amount_paid=?,status=\'paid\',paid_at=CURRENT_TIMESTAMP,payment_txid=? WHERE id=?',(ia,txid,iid));paidn+=1
            else:x.execute('UPDATE loan_installments SET amount_paid=?,payment_txid=? WHERE id=?',(new,txid,iid))
            left-=apply
        newrep=min(float(loan[3] or 0)+amount,float(loan[2]));status='completed' if newrep+.01>=float(loan[2]) else 'active'
        nx=x.execute("SELECT due_date FROM loan_installments WHERE loan_id=? AND status!='paid' ORDER BY installment_number LIMIT 1",(lid,)).fetchone()
        x.execute("UPDATE loans SET amount_repaid=?,installments_paid=(SELECT COUNT(*) FROM loan_installments WHERE loan_id=? AND status='paid'),next_due_date=?,last_payment_at=CURRENT_TIMESTAMP,status=? WHERE id=?",(newrep,lid,nx[0] if nx else None,status,lid));x.commit()
    except Exception as e:x.rollback();await u.message.reply_text(T['fr']['repay_err'].format(reason=str(e)));return
    finally:x.close()
    audit('record_repayment','loan',lid,f'amount={amount};txid={txid}')
    await u.message.reply_text(T['fr']['repay_ok'].format(id=lid,amount=amount,txid=txid,paid=paidn))
def register_enterprise_handlers(app):
    for n,f in [('loanstatus',loanstatus),('schedule',schedule),('support',support),('repay',repay)]:app.add_handler(CommandHandler(n,f))
'''
(P/'enterprise_features.py').write_text(module,encoding='utf-8')

# Patch bot import and command registration.
bot=P/'bot.py'; s=bot.read_text(encoding='utf-8')
if 'from enterprise_features import register_enterprise_handlers' not in s:
    s=s.replace('from database import init_database','from database import init_database\nfrom enterprise_features import register_enterprise_handlers',1)
needle='    application = Application.builder().token(TOKEN).connect_timeout(30).read_timeout(30).write_timeout(30).pool_timeout(30).build()'
if 'register_enterprise_handlers(application)' not in s:
    if needle not in s: raise SystemExit('❌ Ligne Application introuvable dans bot.py')
    s=s.replace(needle,needle+'\n\n    register_enterprise_handlers(application)',1)
s=s.replace('duration=months,','duration=duration,')
bot.write_text(s,encoding='utf-8')

for n in ['bot.py','database.py','enterprise_features.py']:
    py_compile.compile(str(P/n),doraise=True)
print('🧪 Syntaxe OK')
print('🎉 UPGRADE TERMINÉ')
print('➡️ Relance le bot avec: python bot.py')
