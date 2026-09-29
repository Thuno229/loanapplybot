#!/usr/bin/env python3
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

HELPER = '\ndef _lang(update):\n    """Return the user\'s stored language, restricted to supported languages."""\n    try:\n        import sqlite3\n        from storage import DB_PATH\n        conn = sqlite3.connect(DB_PATH)\n        try:\n            row = conn.execute(\n                "SELECT language FROM users WHERE telegram_id=?",\n                (update.effective_user.id,)\n            ).fetchone()\n        finally:\n            conn.close()\n        lang = row[0] if row else None\n        return lang if lang in ("fr", "en", "es", "pt") else "fr"\n    except Exception:\n        return "fr"\n'\n\nCLIENT_FUNCTIONS = {
    "loanstatus", "schedule", "support", "client_support",
    "repay", "client_loan_status", "client_schedule"
}

def fail(message):
    print("ERROR:", message)
    sys.exit(1)

def backup(path):
    bak = path.with_name(path.name + ".before_language_fix.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print("Backup:", bak.name)

def function_blocks(source):
    tree = ast.parse(source)
    lines = source.splitlines(keepends=True)
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = (
                node.lineno - 1,
                getattr(node, "end_lineno", node.lineno)
            )
    return result, lines

def patch_enterprise():
    path = PROJECT / "enterprise_features.py"
    if not path.exists():
        print("enterprise_features.py absent: skip")
        return

    source = path.read_text(encoding="utf-8")
    ranges, lines = function_blocks(source)
    changed = False

    for name in CLIENT_FUNCTIONS:
        if name not in ranges:
            continue
        start, end = ranges[name]
        block = "".join(lines[start:end])
        new_block = block.replace('T["fr"]', "T[_lang(update)]")
        new_block = new_block.replace("T['fr']", "T[_lang(update)]")
        if new_block != block:
            lines[start:end] = [new_block]
            changed = True

    new_source = "".join(lines)

    if "def _lang(" not in new_source:
        lines2 = new_source.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines2):
            if line.startswith("import ") or line.startswith("from "):
                insert_at = i + 1
        lines2.insert(insert_at, HELPER)
        new_source = "".join(lines2)
        changed = True

    if changed:
        backup(path)
        path.write_text(new_source, encoding="utf-8")
        print("enterprise_features.py: corrected")
    else:
        print("enterprise_features.py: no automatic correction needed")

def audit_forced_french():
    print("\nAUDIT T['fr']")
    found = []
    for filename in CORE:
        path = PROJECT / filename
        if not path.exists():
            continue
        for number, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if re.search(r"T\s*\[\s*['\"]fr['\"]\s*\]", line):
                found.append((filename, number, line.strip()))

    if not found:
        print("OK: no direct T['fr'] references found.")
    else:
        print("WARNING: direct French references remain:")
        for filename, number, line in found:
            print(f"  {filename}:{number}: {line}")
        print("Review these before deployment; some may be admin-only.")

def check_languages():
    print("\nLANGUAGE CHECK")
    path = PROJECT / "enterprise_features.py"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    for lang in ("fr", "en", "es", "pt"):
        if re.search(r"['\"]" + lang + r"['\"]\s*:", text):
            print(lang.upper(), "OK")
        else:
            print(lang.upper(), "MISSING")

def compile_modules():
    print("\nPYTHON COMPILE CHECK")
    for filename in CORE:
        path = PROJECT / filename
        if not path.exists():
            continue
        py_compile.compile(str(path), doraise=True)
        print("OK:", filename)

def main():
    print("LANGUAGE ROUTING AUDIT - LoanApplyBot")
    print("=" * 50)
    if not PROJECT.exists():
        fail("Project directory not found.")
    patch_enterprise()
    check_languages()
    audit_forced_french()
    compile_modules()
    print("\nDONE")
    print("No git push was performed.")
    print("BOT_TOKEN was not read or changed.")
    print("Test the English account before deployment.")

if __name__ == "__main__":
    main()
