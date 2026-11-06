#!/usr/bin/env python3
"""
ElektroSync (sync_bank_to_html.py)
----------------------------------
Narzędzie nr 4 w potoku ElektroLeszek:
Synchronizuje plik `question_bank.json` z plikiem aplikacji `index.html` (wstrzykuje tablicę `questionBank`),
automatycznie aktualizuje liczniki pytań we wszystkich widokach (Dashboard, Tryb Nauki, Egzamin, Baza Pytań)
oraz powiela pliki do katalogów `ElektroBaza/` i `FizykaBaza/`.

Użycie:
    python3 scripts/sync_bank_to_html.py
"""

import json
import re
import shutil
import sys
from pathlib import Path


def sync():
    root = Path(__file__).resolve().parent.parent
    bank_path = root / "question_bank.json"
    html_path = root / "ElektroBaza" / "index.html"

    if not bank_path.exists():
        print(f"[BŁĄD] Nie znaleziono pliku {bank_path}")
        return 1
    if not html_path.exists():
        html_path = root / "index.html"

    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    total_count = len(bank)

    # Oblicz liczbę pytań dla każdego laboratorium
    lab_counts = {}
    for q in bank:
        for lab in q.get("labs", []):
            key = str(lab)
            lab_counts[key] = lab_counts.get(key, 0) + 1

    html = html_path.read_text(encoding="utf-8")

    # 1. Wstrzyknij questionBank do skryptu
    formatted_json = json.dumps(bank, ensure_ascii=False, indent=4)
    indented_lines = []
    for i, line in enumerate(formatted_json.splitlines()):
        if i == 0:
            indented_lines.append("        const questionBank = " + line)
        else:
            indented_lines.append("        " + line)
    replacement_block = "\n".join(indented_lines) + ";"

    pattern_bank = re.compile(
        r"        const questionBank = \[.*?\n\s*\];",
        re.DOTALL,
    )
    if not pattern_bank.search(html):
        print("[BŁĄD] Nie znaleziono bloku `const questionBank = [...]` w index.html")
        return 1
    html = pattern_bank.sub(lambda _: replacement_block, html, count=1)

    # 2. Zaktualizuj globalne liczniki wszystkich pytań
    html = re.sub(
        r'(<span id="stat-solved"[^>]*>0 / )\d+(</span>)',
        rf"\g<1>{total_count}\2",
        html,
    )
    html = re.sub(
        r'(Kompleksowa baza pytań i zadań obliczeniowych z Elektrotechniki \()\d+( pytań\))',
        rf"\g<1>{total_count}\2",
        html,
    )
    html = re.sub(
        r'(<option value="all">Wszystkie laboratoria \()\d+(\)</option>)',
        rf"\g<1>{total_count}\2",
        html,
    )
    html = re.sub(
        r'(<input type="number" id="study-go-to" min="1" max=")\d+(")',
        rf"\g<1>{total_count}\2",
        html,
    )
    html = re.sub(
        r'(<option value="all" selected id="exam-count-all-opt">Wszystkie wybrane pytania \()\d+(\)</option>)',
        rf"\g<1>{total_count}\2",
        html,
    )
    html = re.sub(
        r'(id="browse-title">Baza pytań \()\d+(\)</h2>)',
        rf"\g<1>{total_count}\2",
        html,
    )

    # 3. Zaktualizuj liczniki poszczególnych laboratoriów (1..9 oraz wejsciowka1)
    for lab_key, count in lab_counts.items():
        suffix = "pytania" if (count in (2, 3, 4)) else "pytań"
        # Dashboard card: onclick="filterToLabStudy('X')" ... >COUNT pytań/pytania</span>
        dash_pattern = re.compile(
            rf"(onclick=\"filterToLabStudy\('{re.escape(lab_key)}'\)\".*?<span class=\"text-\[11px\] font-mono px-1\.5 py-0\.5 rounded border border-neutral-200 dark:border-neutral-700 text-neutral-500\">)\d+ pyt\w+(</span>)",
            re.DOTALL,
        )
        html = dash_pattern.sub(rf"\g<1>{count} {suffix}\2", html, count=1)

        # Study select option: <option value="X">... (COUNT)</option>
        study_opt_pattern = re.compile(
            rf'(<option value="{re.escape(lab_key)}">[^<]*?\()\d+(\)</option>)'
        )
        html = study_opt_pattern.sub(rf"\g<1>{count}\2", html)

        # Exam checkbox label: name="exam-lab" value="X" ... <span>... (COUNT)</span>
        exam_cb_pattern = re.compile(
            rf'(name="exam-lab" value="{re.escape(lab_key)}"[^>]*>\s*<span>[^<(]+\()\d+(\)</span>)',
            re.DOTALL,
        )
        html = exam_cb_pattern.sub(rf"\g<1>{count}\2", html)

    # 4. Zapisz zaktualizowany index.html i zsynchronizuj kopie
    target_htmls = [
        root / "index.html",
        root / "ElektroBaza" / "index.html",
        root / "FizykaBaza" / "index.html",
    ]
    for t_html in target_htmls:
        if t_html.parent.exists():
            t_html.write_text(html, encoding="utf-8")

    target_banks = [
        root / "ElektroBaza" / "question_bank.json",
        root / "FizykaBaza" / "question_bank.json",
    ]
    for t_bank in target_banks:
        if t_bank.parent.exists():
            shutil.copy2(bank_path, t_bank)

    # Synchronizuj katalogi img/ oraz scripts/ do podkatalogów repozytoriów
    for subrepo in ["ElektroBaza", "FizykaBaza"]:
        sub_dir = root / subrepo
        if sub_dir.exists():
            for folder_name in ["img", "scripts"]:
                src_folder = root / folder_name
                dst_folder = sub_dir / folder_name
                if src_folder.exists():
                    dst_folder.mkdir(parents=True, exist_ok=True)
                    for item in src_folder.iterdir():
                        if item.is_file():
                            shutil.copy2(item, dst_folder / item.name)

    print("=== ELEKTRO-SYNC: ZAKOŃCZONO SYNCHRONIZACJĘ ===")
    print(f"• Całkowita liczba unikalnych pytań: {total_count}")
    for k in sorted(lab_counts.keys()):
        print(f"  - Lab/Moduł '{k}': {lab_counts[k]} pytań")
    print("• Zaktualizowano: index.html, ElektroBaza/index.html, FizykaBaza/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(sync())
