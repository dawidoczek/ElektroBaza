#!/usr/bin/env python3
"""
ElektroScanner (scripts/scan_screenshots.py)
--------------------------------------------
Narzędzie nr 1 w pipeline'ie ElektroLeszek.
Skanuje katalog roboczy w poszukiwaniu zrzutów ekranu zadań (`zad X.Y`, `zadanie X.Y`,
ściągawek oraz wejściówek), rozpoznaje numer laboratorium, wymiary obrazów
i generuje raport inwentaryzacyjny przed odczytaniem treści przez model Vision (read_file).

Użycie:
    python3 scripts/scan_screenshots.py [--dir .] [--lab 5]
"""

import argparse
import json
import os
import re
import struct
from pathlib import Path


def get_png_dimensions(filepath: Path):
    """Odczytuje wymiary (width, height) z nagłówka IHDR pliku PNG."""
    try:
        with open(filepath, "rb") as f:
            header = f.read(24)
            if len(header) >= 24 and header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR":
                width, height = struct.unpack(">II", header[16:24])
                return width, height
    except Exception:
        pass
    return None, None


def scan_directory(base_dir: Path, target_lab: str = None):
    task_pattern = re.compile(
        r"^(?:zad(?:anie)?)\s*(\d+)[\._](\d+)(.*)\.(png|jpg|jpeg|webp)$",
        re.IGNORECASE,
    )
    cheatsheet_pattern = re.compile(
        r"^(?:zad(?:anie)?)\s*(\d+)\s*.*(?:sci[aą]gawka|wzory|teoria).*\.(png|jpg|jpeg|webp)$",
        re.IGNORECASE,
    )
    wejsciowka_pattern = re.compile(
        r"^(?:wej[sś]ci[oó]wka)\s*(\d*)(.*)\.(png|jpg|jpeg|webp)$",
        re.IGNORECASE,
    )

    results = {
        "labs": {},
        "cheatsheets": [],
        "wejsciowki": [],
        "existing_crops": [],
    }

    for entry in sorted(base_dir.iterdir()):
        if entry.is_file():
            name = entry.name
            m_task = task_pattern.match(name)
            m_cheat = cheatsheet_pattern.match(name)
            m_wej = wejsciowka_pattern.match(name)

            if m_cheat:
                lab_num = m_cheat.group(1)
                if target_lab and str(lab_num) != str(target_lab):
                    continue
                w, h = get_png_dimensions(entry)
                results["cheatsheets"].append({
                    "lab": int(lab_num),
                    "filename": name,
                    "path": str(entry.resolve()),
                    "size_bytes": entry.stat().st_size,
                    "dimensions": f"{w}x{h}" if w else "unknown",
                })
            elif m_task:
                lab_num = m_task.group(1)
                shot_num = m_task.group(2)
                if target_lab and str(lab_num) != str(target_lab):
                    continue
                w, h = get_png_dimensions(entry)
                results["labs"].setdefault(lab_num, []).append({
                    "lab": int(lab_num),
                    "shot": int(shot_num),
                    "filename": name,
                    "path": str(entry.resolve()),
                    "size_bytes": entry.stat().st_size,
                    "dimensions": f"{w}x{h}" if w else "unknown",
                })
            elif m_wej:
                w, h = get_png_dimensions(entry)
                results["wejsciowki"].append({
                    "filename": name,
                    "path": str(entry.resolve()),
                    "size_bytes": entry.stat().st_size,
                    "dimensions": f"{w}x{h}" if w else "unknown",
                })

    img_dir = base_dir / "img"
    if img_dir.exists() and img_dir.is_dir():
        for img_file in sorted(img_dir.iterdir()):
            if img_file.is_file() and img_file.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg"}:
                w, h = get_png_dimensions(img_file)
                results["existing_crops"].append({
                    "filename": f"img/{img_file.name}",
                    "size_bytes": img_file.stat().st_size,
                    "dimensions": f"{w}x{h}" if w else "unknown",
                })

    for lab_key in results["labs"]:
        results["labs"][lab_key].sort(key=lambda x: x["shot"])

    return results


def main():
    parser = argparse.ArgumentParser(description="ElektroScanner – Inwentaryzacja zrzutów ekranu zadań.")
    parser.add_argument("--dir", default=".", help="Katalog ze zrzutami ekranu (domyślnie: .)")
    parser.add_argument("--lab", default=None, help="Filtruj tylko wskazany numer laboratorium (np. 5)")
    parser.add_argument("--json", action="store_true", help="Wypisz wynik w formacie JSON")
    args = parser.parse_args()

    data = scan_directory(Path(args.dir), args.lab)
    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print("=== ELEKTRO-SCANNER: RAPORT PLIKÓW WEJŚCIOWYCH ===")
    if not data["labs"] and not data["cheatsheets"] and not data["wejsciowki"]:
        print("Brak plików zrzutów ekranu pasujących do wzorca `zad X.Y` lub `zadanie X.Y`.")
    for lab, files in sorted(data["labs"].items(), key=lambda x: int(x[0])):
        print(f"\n[Laboratorium {lab}] ({len(files)} zrzutów):")
        for f in files:
            print(f"  • {f['filename']:25s} | {f['dimensions']:10s} | {f['size_bytes']:7d} B | {f['path']}")

    if data["cheatsheets"]:
        print(f"\n[Ściągawki / Wzory] ({len(data['cheatsheets'])} plików):")
        for c in data["cheatsheets"]:
            print(f"  • Lab {c['lab']}: {c['filename']:22s} | {c['dimensions']:10s} | {c['path']}")

    if data["existing_crops"]:
        print(f"\n[Wycięte schematy w img/] ({len(data['existing_crops'])} plików):")
        for crop in data["existing_crops"]:
            print(f"  • {crop['filename']:35s} | {crop['dimensions']:10s} | {crop['size_bytes']:6d} B")


if __name__ == "__main__":
    main()
