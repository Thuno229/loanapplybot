#!/usr/bin/env python3
# fix_language_routing.py
# Correction sûre du routage FR/EN/ES/PT de LoanApplyBot.
# Ce script NE fait aucun git push et ne touche pas aux secrets.

from pathlib import Path
import ast
import py_compile
import shutil
import re
import sys

PROJECT = Path(__file__).resolve().parent

CORE = [
    "bot.py", "database.py", "admin_panel.py", "loan_callbacks.py",
    "i18n.py", "notifications.py", "kyc_flow.py",
    "enterprise_features.py", "api.py", "storage.py"
]

CLIENT_FUNCTIONS = {
    "loanstatus", "schedule", "support", "client_support",
    "repay", "client_loan_status", "client_schedule"
}

def fail(msg):
    print(f"❌ {msg}")
    sys.exit(1)

def backup(path):
    bak = path.with_suffix(path.suffix + ".before_language_fix.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print(f"💾 Backup: {bak.name}")

def find_function_ranges(source):
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    ranges = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            ranges[node.name] = (start, end)
    return ranges, lines

def patch_enterprise():
    path = PROJECT / "enterprise_features.py"
    if not path.exists():
        print("ℹ️ enterprise_features.py absent — rien à corriger.")
        return

    source = path.read_text(encoding="utf-8")
    old = source
    ranges, lines = find_function_ranges(source)

    # Fonctions destinées aux clients.
    # On remplace uniquement les références françaises forcées.
    changed = False
    for name in CLIENT_FUNCTIONS:
        if name not in ranges:
            continue
        start, end = ranges[name]
        block = "".join(lines[start:end])

        replacements = [
            ("T['fr']", "T[_lang(update)]"),
            ('T["fr"]', "T[_lang(update)]"),
        ]

        new_block = block
        for a, b in replacements:
            new_block = new_block.replace(a, b)

        if new_block != block:
            lines[start:end] = [new_block]
            changed = True

    source = "".join(lines)

    # S'assurer que le module possède un helper _lang compatible.
    if "def _lang(" not in source:
        helper = 