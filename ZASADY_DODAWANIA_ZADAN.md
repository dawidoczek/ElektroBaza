# ElektroLeszek – Standard Operacyjny i Pipeline Dodawania Zadań (`ZASADY_DODAWANIA_ZADAN.md`)

Dokument definiuje kompletny zbiór zasad merytorycznych, technicznych i wizualnych oraz ścisłą kolejność kroków (**Pipeline 6-etapowy**) obowiązującą przy rozbudowie bazy pytań i zadań **ElektroLeszek** (`question_bank.json` + `index.html`). Został opracowany na bazie głównej specyfikacji projektu oraz narzędzi CLI w katalogu `scripts/`.

---

## 1. Architektura Narzędzi i Skryptów (`scripts/`)

Do automatyzacji pracy ze zrzutami ekranu, wycinania schematów, walidacji LaTeX/deduplikacji oraz synchronizacji z aplikacją służą **4 dedykowane narzędzia CLI**:

| Nazwa narzędzia | Skrypt w `scripts/` | Przeznaczenie |
| :--- | :--- | :--- |
| **ElektroScanner** | `scripts/scan_screenshots.py` | Skanuje katalog w poszukiwaniu plików `zad X.Y` / `zadanie X.Y`, parsuje numer laboratorium `X` i indeks zrzutu `Y`, odczytuje wymiary obrazów PNG oraz zestawia pokrycie z aktualną bazą `question_bank.json`. |
| **ElektroCropper** | `scripts/crop_schematic.py` | Wycina ze zrzutu ekranu sam schemat obwodu elektrycznego lub wykres (bez treści pytania i bez interfejsu Moodle) przy użyciu współrzędnych znormalizowanych `0.0–1.0` lub pikselowych i zapisuje wynik w `img/labX_<opis>.png`. |
| **ElektroValidator** | `scripts/validate_question_bank.py` | Przeprowadza pełny audyt `question_bank.json`: sprawdza ciągłość `id`, strukturę pól, obecność plików `img`, parowanie nawiasów LaTeX `\( ... \)` i `\[ ... \]`, brak surowego Markdownu (`**`), brak zdradzania odpowiedzi w treści pytania oraz **automatycznie wykrywa niepołączone warianty liczbowe** (algorytm *skeleton matching*). |
| **ElektroSync** | `scripts/sync_bank_to_html.py` | Wstrzykuje `question_bank.json` do zmiennej `questionBank` w `index.html`, automatycznie przelicza i aktualizuje liczniki pytań we wszystkich widokach (Dashboard, Tryb Nauki, Egzamin, Baza Pytań) oraz synchronizuje pliki pomiędzy `./`, `ElektroBaza/` i `FizykaBaza/`. |

---

## 2. Kolejność Dodawania Nowych Zadań (Pipeline Krok po Kroku)

```
[Krok 1: ElektroScanner]  --> Inwentaryzacja zrzutów ekranu `zadanie X.Y.png`
         |
         v
[Krok 2: Odczyt Wizyjny]  --> Odczytanie treści wszystkich pytań z arkuszy i ściągawek
         |
         v
[Krok 3: ElektroCropper]  --> Wycięcie czystych schematów obwodów/wykresów do `img/`
         |
         v
[Krok 4: Deduplikacja]    --> Złączenie duplikatów 1:1 (`labs`) i wariantów liczbowych (`exp`)
         |
         v
[Krok 5: ElektroValidator]--> Walidacja LaTeX, obliczeń, jednostek i braku duplikatów
         |
         v
[Krok 6: ElektroSync]     --> Wstrzyknięcie do `index.html`, aktualizacja liczników i test JS
```

### Krok 1: Inwentaryzacja zrzutów ekranu (`ElektroScanner`)
Uruchom skaner, aby wylistować wszystkie pliki graficzne według laboratoriów:
```bash
python3 scripts/scan_screenshots.py
# lub w formacie JSON:
python3 scripts/scan_screenshots.py --json
```
- Pierwsza liczba (`X`) w nazwie pliku `zad X.Y` / `zadanie X.Y` oznacza **numer Laboratorium** (np. `zadanie 5.1.png` $\to$ Lab 5).
- Druga liczba (`Y`) oznacza kolejny zrzut ekranu w ramach danego laboratorium.
- Pliki z dopiskiem `sciągawka` / `sciagawka` są klasyfikowane jako materiał referencyjny ze wzorami do zakładki **Wzory**.

### Krok 2: Odczyt wizyjny (OCR / Analiza obrazu)
Przeanalizuj każdy nowy zrzut ekranu (`zadanie X.1.png` ... `zadanie X.N.png`):
1. Odczytaj pełną treść każdego widocznego na zrzucie pytania.
2. Sprawdź typ pytania:
   - **`open`** – pole tekstowe `Odpowiedź:` wymagające wpisania wyniku liczbowego,
   - **`choice`** – pytanie jednokrotnego wyboru (okrągłe przyciski radiowe),
   - **`multi`** – pytanie wielokrotnego wyboru (kwadratowe pola wyboru `Wybierz jedną lub więcej`).
3. Sprawdź, czy pytanie zawiera schemat obwodu elektrycznego lub wykres przebiegu czasowego.

### Krok 3: Wycinanie schematów i wykresów (`ElektroCropper`)
Jeżeli pytanie odwołuje się do rysunku/schematu/wykresu:
1. **Nigdy nie dołączaj pełnego zrzutu ekranu z tekstem pytania lub ramką Moodle.**
2. Wytnij wyłącznie sam schemat obwodu lub wykres przy pomocy narzędzia `ElektroCropper`:
   ```bash
   # Przykład ze współrzędnymi znormalizowanymi (x1 y1 x2 y2 w zakresie 0.0 - 1.0):
   python3 scripts/crop_schematic.py "zadanie 4.1.png" "img/lab4_rownolegly_lc.png" --norm 0.12 0.25 0.55 0.68

   # Przykład ze współrzędnymi w pikselach:
   python3 scripts/crop_schematic.py "zadanie 4.1.png" "img/lab4_rownolegly_lc.png" --px 120 240 520 610
   ```
3. Nazwij plik według konwencji `img/lab<X>_<krotki_opis_schematu>.png` i wpisz tę ścieżkę w polu `"img"` zadania.

### Krok 4: Przetwarzanie, Deduplikacja i Rozwiązywanie Zadań (Zasady Krytyczne)
Przed dopisaniem pytań do `question_bank.json` pogrupuj wszystkie pytania odczytane ze zrzutów i zastosuj **5 złotych reguł**:

#### Reguła 1 – Brak duplikatów 1:1 (`labs`)
- Jeżeli identyczne pytanie (z tymi samymi danymi lub ta sama teoria) pojawia się na kilku zrzutach w tym samym lub różnych laboratoriach, **zapisz je w bazie tylko raz**.
- Jeżeli pytanie występuje w więcej niż jednym laboratorium, wpisz wszystkie numery w tablicy `"labs"`, np. `"labs": [1, 2]`.

#### Reguła 2 – Łączenie zadań o tej samej treści i różnych danych liczbowych (Warianty Liczbowe)
- **KRYTYCZNE:** Jeżeli na zrzutach ekranu znajdują się 2 lub więcej zadań o tym samym schemacie słownym/obliczeniowym, które różnią się wyłącznie wartościami liczbowymi (np. inne wartości $R, L, C, U, I, f_r, Q$), **BEZWZGLĘDNIE połącz je w jedno zadanie w bazie (nie twórz osobnych pytań z osobnymi ID!)**.
- W polu `"q"` wpisz treść z pierwszego (głównego) wariantu ze zrzutu.
- W polu `"numericTarget"` wpisz wartość liczbową (typ `number`, z kropką dziesiętną) dla wariantu głównego.
- W polu `"correct"` wpisz wynik główny z polskim przecinkiem dziesiętnym **wraz z jednostką fizyczną** (np. `"13,62 Hz"`, `"120,77 Ω"`).
- W polu `"exp"` zastosuj obowiązkową strukturę trójdzielną:
  1. **`Wzór ogólny:`** – pełny wzór wyjściowy i jego przekształcenie w LaTeX (`\[ ... \]`), wraz z objaśnieniem symboli.
  2. **`Podstawienie dla danych z pytania (...):`** – szczegółowe podstawienie liczb z wariantu głównego krok po kroku prowadzące do wyniku.
  3. **`Pozostałe warianty ze zrzutów:`** – lista wypunktowana (`• Wariant 2 (...): ...`, `• Wariant 3 (...): ...`) zawierająca podstawienia i gotowe wyniki dla każdego pozostałego wariantu liczbowego ze zdjęć.

#### Reguła 3 – Zadania obliczeniowe (pojedyncze)
- Nigdy nie podawaj samej suchej liczby w wyjaśnieniu (`exp`).
- Każde zadanie obliczeniowe musi zawierać wzór ogólny w LaTeX, przeliczenie jednostek do układu SI (np. $\text{mm}^2 \to 10^{-6}\text{ m}^2$, $\mu\text{F} \to 10^{-6}\text{ F}$, $\text{min} \to \text{s}$) oraz wynik końcowy z jednostką.
- **Zakaz spoilerów w treści pytania:** W polu `"q"` nie wolno podawać podpowiedzi formatowania zdradzających wynik zadania (np. zamiast `Wynik podaj w procentach (np. 22,5)` pisz `Wynik podaj w procentach [%]`).

#### Reguła 4 – Zadania teoretyczne (`choice` oraz `multi`)
- Zachowaj wszystkie opcje wyboru pod kluczami `"a"`, `"b"`, `"c"`, ... (do `"j"`).
- W polu `"correct"` podaj klucz poprawnej odpowiedzi (np. `"a"` dla `choice`) lub klucze oddzielone przecinkiem bez spacji (np. `"a,b,c,d"` dla `multi`).
- Aplikacja automatycznie losuje kolejność wyświetlania opcji zarówno w **Trybie Nauki**, jak i w **Trybie Egzaminu**, dzięki czemu kolejność kluczy w pliku JSON nie zdradza odpowiedzi użytkownikowi.

#### Reguła 5 – Formatowanie LaTeX / MathJax i Czysty Tekst w `exp`
- **Wzory w linii tekstu (inline):** używaj wyłącznie `\( ... \)` (w JSON zapisane jako `\\( ... \\)`).
- **Wzory wyróżnione w osobnej linii (display):** używaj wyłącznie `\[ ... \]` (w JSON zapisane jako `\\[ ... \\]`).
- **Wewnątrz wypunktowań wariantów (`• Wariant 2 ...`):** używaj wyłącznie trybu inline `\( ... \)`, aby uniknąć łamania wiersza w środku punktu.
- **Jednostki i indeksy tekstowe w LaTeX:** zapisuj przez `\text{...}` lub `\,\Omega`, np. `\(R = 13\,\Omega\)`, `\(C = 105\,\mu\text{F}\)`, `\(I_{sk}\)`.
- **Zakaz surowego Markdownu w `q` i `exp`:** Pola tekstowe są renderowane przez bezpieczne `escapeHtml()` z `whitespace-pre-line`. Nie używaj gwiazdek `**pogrubienie**` – używaj przejrzystej numeracji `1.`, `2.` oraz wypunktowań `•`.

### Krok 5: Walidacja bazy pytań (`ElektroValidator`)
Po zapisaniu zmian w `question_bank.json` uruchom walidator:
```bash
python3 scripts/validate_question_bank.py
```
Skrypt musi zwrócić:
- `[OK] Zero błędów krytycznych (struktura, LaTeX, obrazy i deduplikacja poprawne).`
- `[OK] Zero ostrzeżeń.`

Jeżeli `ElektroValidator` zgłosi `[BŁĄD DEDUPLIKACJI]`, połącz wskazane pytania o tym samym szkielecie tekstowym w jedno pytanie zgodnie z **Regułą 2**.

### Krok 6: Synchronizacja z `index.html` i Aktualizacja Zakładki Wzory (`ElektroSync`)
1. Jeżeli nowe laboratorium wprowadza nowe wzory (np. na podstawie pliku `zadanie X sciągawka.png`), dodaj karty wzorów w sekcji `id="formula-cards-grid"` w `ElektroBaza/index.html` z atrybutem `data-lab="X"`.
2. Uruchom narzędzie synchronizujące:
   ```bash
   python3 scripts/sync_bank_to_html.py
   ```
3. Zweryfikuj poprawność składni JavaScript wygenerowanego pliku `index.html`:
   ```bash
   python3 -c 'import re; html=open("index.html").read(); open("/tmp/check.js","w").write(re.findall(r"<script>(.*?)</script>", html, re.S)[-1])' && node --check /tmp/check.js
   ```

---

## 3. Wzorzec Schematu JSON Zadania (`question_bank.json`)

```json
{
  "id": 59,
  "labs": [5],
  "type": "open",
  "numericTarget": 13.62,
  "tolerance": 0.05,
  "q": "Jaką należy nastawić częstotliwość generatora napięcia sinusoidalnego, aby wywołać zjawisko rezonansu prądów w obwodzie równoległym o trzech gałęziach (z cewką idealną): \\(R = 13\\,\\Omega\\), \\(L = 1{,}3\\text{ H}\\) i \\(C = 105\\,\\mu\\text{F}\\)? Wynik podaj w hercach [Hz].",
  "correct": "13,62 Hz",
  "exp": "Wzór ogólny:\nCzęstotliwość rezonansowa dla obwodu o trzech równoległych gałęziach (R, idealne L, C):\n\\[f_r = \\frac{1}{2\\pi \\sqrt{L \\cdot C}}\\]\nWartość rezystancji \\(R\\) w gałęzi równoległej nie wpływa na częstotliwość rezonansową.\n\nPodstawienie dla danych z pytania (\\(R = 13\\,\\Omega, L = 1{,}3\\text{ H}, C = 105\\,\\mu\\text{F} = 105 \\cdot 10^{-6}\\text{ F}\\)):\n\\[L \\cdot C = 1{,}3 \\cdot 105 \\cdot 10^{-6} = 1{,}365 \\cdot 10^{-4}\\text{ s}^2\\]\n\\[\\sqrt{L \\cdot C} = \\sqrt{1{,}365 \\cdot 10^{-4}} \\approx 0{,}0116833\\text{ s}\\]\n\\[f_r = \\frac{1}{2\\pi \\cdot 0{,}0116833} = \\frac{1}{0{,}073408} \\approx 13{,}62\\text{ Hz}\\]\n\nPozostałe warianty ze zrzutów:\n• Wariant 2 (\\(R = 14\\,\\Omega, L = 1{,}4\\text{ H}, C = 86\\,\\mu\\text{F}\\)): \\(f_r = \\frac{1}{2\\pi \\sqrt{1{,}4 \\cdot 86 \\cdot 10^{-6}}} \\approx 14{,}50\\text{ Hz}\\) (14,5 Hz)\n• Wariant 3 (\\(R = 11\\,\\Omega, L = 1{,}1\\text{ H}, C = 77\\,\\mu\\text{F}\\)): \\(f_r = \\frac{1}{2\\pi \\sqrt{1{,}1 \\cdot 77 \\cdot 10^{-6}}} \\approx 17{,}29\\text{ Hz}\\)"
}
```
