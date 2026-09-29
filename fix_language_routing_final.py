#!/usr/bin/env python3
from pathlib import Path
import ast
import py_compile
import shutil
import re
import sys

PROJECT = Path(__file__).resolve().parent
CORE = ["bot.py","database.py","admin_panel.py","loan_callbacks.py","i18n.py","notifications.py","kyc_flow.py","enterprise_features.py","api.py","storage.py"]
CLIENT_FUNCTIONS = {"loanstatus","schedule","support","client_support","repay","client_loan_status","client_schedule"}

def backup(path):
    bak = path.with_name(path.name + ".before_language_fix.bak")
    if not bak.exists():
        shutil.copy2(path, bak)
        print("Backup:", bak.name)

def get_functions(source):
    tree = ast.parse(source)
    result = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result[node.name] = (node.lineno - 1, getattr(node, 'end_lineno', node.lineno))
    return result

def patch_enterprise():
    path = PROJECT / "enterprise_features.py"
    if not path.exists():
        print("enterprise_features.py absent")
        return
    source = path.read_text(encoding="utf-8")
    ranges = get_functions(source)
    lines = source.splitlines(keepends=True)
    changed = False
    for name in CLIENT_FUNCTIONS:
        if name not in ranges:
            continue
        start, end = ranges[name]
        block = "".join(lines[start:end])
        new = block.replace("T['fr']", "T[_lang(update)]").replace('T["fr"]', "T[_lang(update)]")
        if new != block:
            lines[start:end] = [new]
            changed = True
    source = "".join(lines)
    if changed:
        backup(path)
        path.write_text(source, encoding="utf-8")
        print("enterprise_features.py: corrected")
    else:
        print("enterprise_features.py: no automatic change")

def audit():
    print("\nAUDIT DES REFERENCES FRANCAISES FORCEES")
    found = []
    for filename in CORE:
        path = PROJECT / filename
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if re.search(r"T\s*\[\s*['\"]fr['\"]\s*\]", line):
                found.append((filename, n, line.strip()))
    if not found:
        print("OK: aucune reference directe T[fr]")
    else:
        for filename, n, line in found:
            print(f"ATTENTION {filename}:{n}: {line}")
        print("Ces references restantes doivent etre verifiees; certaines peuvent etre reservees a l admin.")

def languages():
    path = PROJECT / "enterprise_features.py"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    print("\nLANGUES")
    for lang in ("fr","en","es","pt"):
        ok = re.search(r"['\"]" + lang + r"['\"]\s*:", text) is not None
        print(("OK " if ok else "MANQUANTE ") + lang.upper())

def compile_all():
    print("\nCOMPILATION")
    for filename in CORE:
        path = PROJECT / filename
        if path.exists():
            py_compile.compile(str(path), doraise=True)
            print("OK", filename)

def main():
    print("LOANAPPLYBOT - AUDIT ROUTAGE DES LANGUES")
    if not PROJECT.exists():
        print("Projet introuvable")
        sys.exit(1)
    patch_enterprise()
    languages()
    audit()
    compile_all()
    print("\nTERMINE - aucun git push effectue")

if __name__ == "__main__":
    main()
