#!/usr/bin/env python3
"""
ElektroValidator (scripts/validate_question_bank.py)
----------------------------------------------------
Narzędzie nr 3 w pipeline'ie ElektroLeszek.
Przeprowadza pełny audyt pliku `question_bank.json`:
  1. Ciągłość ID (1..N) i poprawność schematu JSON.
  2. Detekcję niepołączonych wariantów liczbowych (Zasada #3: Skeleton Matching).
  3. Walidację składni LaTeX/MathJax (nawiasy `\\(...\\)`, `\\[...\\]`, surowe `_` poza trybem math).
  4. Wykrywanie surowych znaczników Markdown `**` (nieobsługiwanych przez czysty HTML).
  5. Walidację zadań otwartych (`numericTarget`, `tolerance`, brak podpowiedzi zdradzających wynik w `q`, obecność jednostek w `correct`).
  6. Weryfikację istnienia plików schematów `img` we wszystkich repozytoriach.

Użycie:
    python3 scripts/validate_question_bank.py [--file question_bank.json]
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


def build_question_skeleton(q_text: str) -> str:
    """Tworzy szkielet tekstu pytania po usunięciu wartości liczbowych (do wykrywania niepołączonych wariantów)."""
    text = q_text.lower()
    # Usuń zapisy liczb dziesiętnych LaTeX np. 1{,}4 lub 120,77 lub 4\cdot 10^{-3}
    text = re.sub(r"\d+\s*\{,\}\s*\d+", "<NUM>", text)
    text = re.sub(r"\d+[,\.]\d+", "<NUM>", text)
    text = re.sub(r"\b\d+\b", "<NUM>", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_math_segments(text: str) -> str:
    """Usuwa fragmenty wewnątrz \\(...\\), \\[...\\] oraz $...$ w celu sprawdzenia surowych znaków poza trybem math."""
    no_display = re.sub(r"\\\[[\s\S]*?\\\]", "", text)
    no_inline = re.sub(r"\\\([\s\S]*?\\\)", "", no_display)
    no_dollar = re.sub(r"\$[^\$]+\$", "", no_inline)
    return no_dollar


def validate_latex(text: str, field_name: str, qid: int, errors: list, warnings: list):
    open_inline = len(re.findall(r"\\\(", text))
    close_inline = len(re.findall(r"\\\)", text))
    if open_inline != close_inline:
        errors.append(f"Q{qid} [{field_name}]: Niezbalansowane nawiasy LaTeX \\( ({open_inline}) vs \\) ({close_inline}).")

    open_disp = len(re.findall(r"\\\[", text))
    close_disp = len(re.findall(r"\\\]", text))
    if open_disp != close_disp:
        errors.append(f"Q{qid} [{field_name}]: Niezbalansowane nawiasy LaTeX \\[ ({open_disp}) vs \\] ({close_disp}).")

    outside_math = strip_math_segments(text)
    if "_" in outside_math:
        errors.append(f"Q{qid} [{field_name}]: Surowy znak podkreślenia '_' poza trybem matematycznym LaTeX.")

    if "**" in text:
        errors.append(f"Q{qid} [{field_name}]: Surowy znacznik Markdown '**' (interfejs renderuje whitespace-pre-line bez parsera Markdown).")


def main():
    parser = argparse.ArgumentParser(description="ElektroValidator – Walidator bazy pytań.")
    parser.add_argument("--file", default="question_bank.json", help="Ścieżka do pliku question_bank.json")
    args = parser.parse_args()

    qb_path = Path(args.file)
    if not qb_path.exists():
        print(f"[BŁĄD] Plik {qb_path} nie istnieje.")
        sys.exit(1)

    with open(qb_path, "r", encoding="utf-8") as f:
        qb = json.load(f)

    errors = []
    warnings = []
    skeletons = defaultdict(list)

    for idx, q in enumerate(qb):
        expected_id = idx + 1
        qid = q.get("id")
        if qid != expected_id:
            errors.append(f"Brak ciągłości ID na pozycji {idx}: oczekiwano ID={expected_id}, znaleziono ID={qid}.")

        qtype = q.get("type")
        if qtype not in {"choice", "multi", "open"}:
            errors.append(f"Q{qid}: Nieprawidłowy typ pytania '{qtype}'.")

        labs = q.get("labs")
        if not labs or not isinstance(labs, list):
            errors.append(f"Q{qid}: Brak lub niepoprawna tablica 'labs'.")

        q_text = q.get("q", "")
        exp_text = q.get("exp", "")
        corr_text = str(q.get("correct", ""))

        if not q_text.strip():
            errors.append(f"Q{qid}: Pusta treść pytania 'q'.")
        if not exp_text.strip():
            errors.append(f"Q{qid}: Puste wyjaśnienie 'exp'.")

        # Sprawdź szkielet pod kątem niepołączonych wariantów liczbowych (Zasada #3)
        skel = build_question_skeleton(q_text)
        skeletons[skel].append(qid)

        # Sprawdź LaTeX we wszystkich polach tekstowych
        validate_latex(q_text, "q", qid, errors, warnings)
        validate_latex(exp_text, "exp", qid, errors, warnings)
        for key in ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]:
            if key in q and q[key]:
                validate_latex(str(q[key]), f"opt_{key}", qid, errors, warnings)

        # Walidacja zadań otwartych
        if qtype == "open":
            if "numericTarget" not in q or q["numericTarget"] is None:
                errors.append(f"Q{qid}: Zadanie typu 'open' nie posiada pola 'numericTarget'.")
            else:
                target = float(q["numericTarget"])
                # Sprawdź, czy w treści pytania nie zaszyto podpowiedzi zdradzającej wynik
                m_hint = re.search(r"\(np\.\s*([0-9]+[,\.][0-9]+)\)", q_text)
                if m_hint:
                    hint_val = float(m_hint.group(1).replace(",", "."))
                    if abs(hint_val - target) <= max(0.5, abs(target * 0.05)):
                        errors.append(f"Q{qid}: Treść pytania zawiera podpowiedź '{m_hint.group(0)}' zdradzającą wynik ({target})!")
                    else:
                        warnings.append(f"Q{qid}: Treść pytania zawiera przykład '{m_hint.group(0)}' – zalecany jest wyłącznie placeholder w polu input.")

            # Sprawdź czy exp zawiera wzór LaTeX
            if "\\[" not in exp_text and "\\(" not in exp_text:
                errors.append(f"Q{qid}: Zadanie obliczeniowe nie zawiera żadnego wzoru LaTeX w polu 'exp'.")

            # Sprawdź czy pole correct zawiera jednostkę (poza bezwymiarowymi lub kątowymi z symbolem °)
            if re.fullmatch(r"-?\d+(?:[,\.]\d+)?", corr_text.strip()):
                warnings.append(f"Q{qid}: Pole 'correct' ('{corr_text}') zawiera samą liczbę bez jednostki fizycznej.")

        # Walidacja ścieżek obrazków
        img = q.get("img")
        if img:
            for repo_dir in [".", "ElektroBaza", "FizykaBaza"]:
                if os.path.exists(repo_dir):
                    img_full = Path(repo_dir) / img
                    if not img_full.exists():
                        errors.append(f"Q{qid}: Brak pliku obrazu '{img_full}'.")

    # Sprawdź duplikaty szkieletów (Zasada #3)
    for skel, ids in skeletons.items():
        if len(ids) > 1:
            errors.append(
                f"Naruszenie Zasady #3 (Niepołączone warianty liczbowe): Pytania o ID {ids} mają identyczny szablon treści i różnią się tylko liczbami!"
            )

    print(f"=== ELEKTRO-VALIDATOR: SPRAWDZONO {len(qb)} PYTAŃ W {qb_path} ===")
    if errors:
        print(f"\n[BŁĘDY KRYTYCZNE: {len(errors)}]")
        for e in errors:
            print(f"  ✗ {e}")
    else:
        print("\n[OK] Zero błędów krytycznych (struktura, LaTeX, obrazy i deduplikacja poprawne).")

    if warnings:
        print(f"\n[OSTRZEŻENIA: {len(warnings)}]")
        for w in warnings:
            print(f"  ! {w}")
    else:
        print("[OK] Zero ostrzeżeń.")

    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
