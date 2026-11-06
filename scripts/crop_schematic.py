#!/usr/bin/env python3
"""
ElektroCropper (scripts/crop_schematic.py)
------------------------------------------
Narzędzie nr 2 w pipeline'ie ElektroLeszek.
Służy do wycinania schematów obwodów elektrycznych, wykresów i tabel ze zrzutów ekranu
(`zadanie X.Y.png`) bez żadnych zewnętrznych bibliotek (czysty Python stdlib `zlib` + `struct`)
oraz automatycznej synchronizacji wyciętego pliku do katalogów:
  - `./img/<nazwa>.png`
  - `./ElektroBaza/img/<nazwa>.png`
  - `./FizykaBaza/img/<nazwa>.png`

Użycie (współrzędne pikselowe x, y, width, height):
    python3 scripts/crop_schematic.py --src "zadanie 4.2.png" --out "img/lab4_schemat.png" --bbox 40,120,380,220

Użycie (współrzędne względne 0.0 - 1.0: x1, y1, x2, y2):
    python3 scripts/crop_schematic.py --src "zadanie 4.2.png" --out "img/lab4_schemat.png" --rel 0.05,0.20,0.55,0.75
"""

import argparse
import shutil
import struct
import zlib
from pathlib import Path


def read_png(path: Path):
    """Dekoduje plik PNG (8-bit RGB/RGBA/Grayscale) używając wyłącznie biblioteki standardowej."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Plik {path} nie jest prawidłowym plikiem PNG.")

    pos = 8
    width = height = bit_depth = color_type = None
    idat_chunks = []

    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        pos += 12 + length

        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, comp, filt, interlace = struct.unpack(">IIBBBBB", chunk_data)
            if bit_depth != 8 or interlace != 0:
                raise ValueError(f"Obsługiwane są tylko 8-bitowe pliki PNG bez przeplotu (bit_depth={bit_depth}).")
        elif chunk_type == b"IDAT":
            idat_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            break

    bpp_map = {0: 1, 2: 3, 4: 2, 6: 4}
    if color_type not in bpp_map:
        raise ValueError(f"Nieobsługiwany color_type PNG: {color_type}")
    bpp = bpp_map[color_type]

    raw = zlib.decompress(b"".join(idat_chunks))
    stride = width * bpp
    rows = []
    offset = 0

    for y in range(height):
        filter_type = raw[offset]
        offset += 1
        row = bytearray(raw[offset:offset + stride])
        offset += stride
        prev_row = rows[-1] if rows else bytearray(stride)

        if filter_type == 1:  # Sub
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif filter_type == 2:  # Up
            for i in range(stride):
                row[i] = (row[i] + prev_row[i]) & 0xFF
        elif filter_type == 3:  # Average
            for i in range(stride):
                left = row[i - bpp] if i >= bpp else 0
                up = prev_row[i]
                row[i] = (row[i] + ((left + up) >> 1)) & 0xFF
        elif filter_type == 4:  # Paeth
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prev_row[i]
                c = prev_row[i - bpp] if i >= bpp else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                row[i] = (row[i] + pr) & 0xFF

        rows.append(row)

    return width, height, color_type, bpp, rows


def make_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF
    return struct.pack(">I", len(chunk_data)) + chunk_type + chunk_data + struct.pack(">I", crc)


def write_png(path: Path, width: int, height: int, color_type: int, rows: list):
    """Zapisuje wycięty bufor wierszy do pliku PNG."""
    ihdr = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    raw_Filtered = bytearray()
    for row in rows:
        raw_Filtered.append(0)  # Filter type 0 (None)
        raw_Filtered.extend(row)
    compressed = zlib.compress(bytes(raw_Filtered), level=9)

    png_bytes = (
        b"\x89PNG\r\n\x1a\n"
        + make_chunk(b"IHDR", ihdr)
        + make_chunk(b"IDAT", compressed)
        + make_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png_bytes)


def crop_png(src_path: Path, dst_path: Path, x: int, y: int, w: int, h: int):
    width, height, color_type, bpp, rows = read_png(src_path)
    x = max(0, min(x, width - 1))
    y = max(0, min(y, height - 1))
    w = max(1, min(w, width - x))
    h = max(1, min(h, height - y))

    cropped_rows = []
    for row in rows[y:y + h]:
        cropped_rows.append(row[x * bpp:(x + w) * bpp])

    write_png(dst_path, w, h, color_type, cropped_rows)
    return w, h


def sync_image_mirrors(rel_img_path: str):
    """Synchronizuje wycięty obrazek pomiędzy ./img/, ElektroBaza/img/ oraz FizykaBaza/img/."""
    src = Path(rel_img_path)
    if not src.exists():
        return
    for mirror in [Path("ElektroBaza") / rel_img_path, Path("FizykaBaza") / rel_img_path]:
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, mirror)
        print(f"  [SYNC] Skopiowano do: {mirror}")


def main():
    parser = argparse.ArgumentParser(description="ElektroCropper – Wycinanie schematów do katalogu img/.")
    parser.add_argument("--src", required=True, help="Ścieżka do źródłowego zrzutu ekranu PNG")
    parser.add_argument("--out", required=True, help="Ścieżka docelowa (np. img/lab5_zad1.png)")
    parser.add_argument("--bbox", default=None, help="Współrzędne pikselowe: x,y,w,h")
    parser.add_argument("--rel", default=None, help="Współrzędne względne (0.0-1.0): x1,y1,x2,y2")
    args = parser.parse_args()

    src_path = Path(args.src)
    out_path = Path(args.out)

    width, height, _, _, _ = read_png(src_path)
    if args.bbox:
        x, y, w, h = [int(v.strip()) for v in args.bbox.split(",")]
    elif args.rel:
        x1, y1, x2, y2 = [float(v.strip()) for v in args.rel.split(",")]
        x = int(x1 * width)
        y = int(y1 * height)
        w = int((x2 - x1) * width)
        h = int((y2 - y1) * height)
    else:
        raise SystemExit("Podaj --bbox x,y,w,h lub --rel x1,y1,x2,y2.")

    cw, ch = crop_png(src_path, out_path, x, y, w, h)
    print(f"[OK] Wycięto schemat: {out_path} ({cw}x{ch} px z oryginału {width}x{height} px)")
    sync_image_mirrors(args.out)


if __name__ == "__main__":
    main()
