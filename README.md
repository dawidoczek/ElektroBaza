# ElektroBaza – Interaktywny Trenażer Elektrotechniki

Nowoczesna, zoptymalizowana aplikacja webowa do nauki, powtórki i symulacji kartkówek oraz egzaminów z **Elektrotechniki (Laboratoria 1, 2 i 3)**.

Aplikacja jest w pełni autonomiczna (Single Page Application w czystym HTML/JS/Tailwind CDN/MathJax 3), nie wymaga instalacji żadnych zależności ani serwera backendowego. Działa bezpośrednio po otwarciu w przeglądarce oraz jest w 100% gotowa do publikacji przez **GitHub Pages**.

---

## ⚡ Główne funkcjonalności

- **Tryb Nauki (Study Mode)**:
  - Fiszki i pytania interaktywne (wybór pojedynczy, wielokrotny oraz pytania otwarte/obliczeniowe).
  - Precyzyjnie sformatowane wzory matematyczne w **LaTeX/MathJax** z wyjaśnieniem symboli i kroków obliczeniowych.
  - Wypisane obliczenia i wyniki dla wszystkich wariantów liczbowych ze zrzutów laboratoryjnych.
  - Filtrowanie pytań po konkretnym laboratorium (`Lab 1`, `Lab 2`, `Lab 3` lub `Wszystkie`).
  - Losowa kolejność pytań oraz szybki skok do zadanego numeru.

- **Tryb Egzaminu (Exam Simulation)**:
  - Konfiguracja liczby pytań (5, 10, 15, 20 lub wszystkie) oraz limitu czasu (lub brak limitu).
  - Wybór zakresu laboratoriów do egzaminu.
  - Zegar odliczający czas w czasie rzeczywistym.
  - Szczegółowe podsumowanie wyników: procent punktów, ocena (pozytywna/negatywna), czas, autooceana pytań otwartych oraz wgląd we wzorce odpowiedzi.

- **Przeglądaj Bazę (Database Browser)**:
  - Błyskawiczna wyszukiwarka zagadnień i treści pytań (indeksowana w pamięci RAM, z debouncingiem 150 ms).
  - Filtrowanie według laboratorium.
  - Paginacja i leniwe doładowywanie pytań (Lazy Batch Rendering / Infinite Scroll).
  - Przycisk *"Ucz się teraz"* przenoszący bezpośrednio do wybranego pytania w trybie nauki.

- **Ulubione pytania (Starred)**:
  - Oznaczanie trudnych pytań gwiazdką i szybka powtórka wyselekcjonowanego materiału.

- **Schematy obwodów i wykresy**:
  - Wykadrowane, czytelne schematy układów elektrycznych i wykresy sygnałów.
  - Interaktywny modal (lightbox) powiększający schemat po kliknięciu.

- **Dark Mode / Light Mode**:
  - Automatyczne dopasowanie do motywu systemu oraz ręczny przełącznik w nagłówku.

- **Wydajność (Performance)**:
  - **In-Memory Cache & Indexing**: natychmiastowe filtrowanie w pamięci RAM.
  - **Targeted MathJax**: renderowanie formuł wyłącznie dla aktywnej karty, bez blokowania wątku interfejsu.
  - **Lazy Loading**: start strony w poniżej 10 ms.

---

## 📚 Zakres merytoryczny

1. **Laboratorium 1 (Elementy obwodowe i relacje)**:
   - Klasyfikacja elementów idealnych: transformator, dioda półprzewodnikowa, rezystor, kondensator, cewka (dwójniki, wielobiegunniki, elementy pasywne, aktywne, dyssypatywne, konserwatywne, odwracalne i nieodwracalne).
   - Prawo Ohma ($I = U/R$, $R = U/I$).
   - Rezystancja przewodnika prostokątnego ($R = \frac{\rho l}{a \cdot b}$) i okrągłego ($R = \frac{4 \rho l}{\pi d^2}$).
   - Relacje ładunku, napięcia i pojemności ($C = Q/U$, $U = Q/C$, $Q = C \cdot U$).
   - Pojemność kondensatora płaskiego ($C = \varepsilon_0 \varepsilon_r \frac{S}{d}$).
   - Cewka i strumień magnetyczny ($L = \Psi/I$, $I = \Psi/L$, $\Psi = L \cdot I$).
   - Indukcyjność cewki cylindrycznej powietrznej ($L = \mu_0 \frac{z^2 S}{l}$).

2. **Laboratorium 2 (Twierdzenia teorii obwodów i obwody DC)**:
   - Twierdzenie Thevenina i twierdzenie Nortona (obwody zastępcze rzeczywistych źródeł).
   - Zasada superpozycji (warunki stosowalności i ograniczenia).
   - Twierdzenie o wzajemności (brak zastosowania przy wielu źródłach).
   - Analiza obwodów z elementami nieliniowymi (uniwersalność praw Kirchhoffa).
   - Sprawność energetyczna źródła rzeczywistego ($\eta = \frac{R_{odb}}{R_{odb} + R_w} \cdot 100\%$).
   - Stan dopasowania na moc maksymalną ($P_{max} = \frac{E^2}{4 R_w}$).
   - I i II prawo Kirchhoffa dla rozgałęzionych obwodów DC (wyznaczanie prądów gałęziowych $I_1$ i $I_3$ na podstawie schematów).

3. **Laboratorium 3 (Sygnały zmienne, moc i prostowniki)**:
   - Klasyfikacja sygnałów: fala trójkątna symetryczna, sygnał zaniku wykładniczego.
   - Ciepło Joule'a wydzielone na rezystorze przy prądzie trójkątnym ($W = \frac{I_m^2 R}{3} t$) i sinusoidalnym ($W = \frac{I_m^2 R}{2} t$).
   - Mostek prostowniczy Graetza z napięciem prostokątnym, trójkątnym i sinusoidalnym (wartości średnie i skuteczne prądu wyprostowanego).
   - Pomiary ładunku miernikami magnetoelektrycznymi DC i elektromagnetycznymi AC ($Q = I_{DC} \cdot t$).

---

## 🚀 Jak uruchomić lokalnie

Wystarczy pobrać repozytorium i otworzyć plik `index.html` w dowolnej nowoczesnej przeglądarce (Chrome, Firefox, Safari, Edge):

```bash
open index.html   # na macOS
xdg-open index.html # na Linuxie
start index.html  # na Windowsie
```

---

## 🌐 Jak wrzucić na swojego GitHuba i włączyć GitHub Pages

Repozytorium w tym folderze jest już zainicjalizowane w Git z gałęzią `main`. Aby opublikować projekt na swoim profilu GitHub:

1. Wejdź na [GitHub.com](https://github.com) i kliknij **New repository**.
2. Wpisz nazwę, np. `ElektroBaza`, wybierz widoczność (Publiczne) i **nie zaznaczaj** dodawania README / .gitignore (już je masz).
3. W terminalu w tym folderze wykonaj polecenia:

```bash
cd ElektroBaza

# Dodaj adres swojego zdalnego repozytorium:
git remote add origin https://github.com/TWOJA_NAZWA_UZYTKOWNIKA/ElektroBaza.git

# Wyślij kod na GitHub:
git push -u origin main
```

4. **Włączenie darmowego hostingu (GitHub Pages)**:
   - W repozytorium na GitHubie wejdź w zakładkę **Settings** $\to$ **Pages** (w menu po lewej).
   - W sekcji **Build and deployment** $\to$ **Source** wybierz **GitHub Actions** (repozytorium posiada już gotowy workflow w `.github/workflows/static.yml`).
   - Strona po kilkunastu sekundach pojawi się pod adresem:
     `https://TWOJA_NAZWA_UZYTKOWNIKA.github.io/ElektroBaza/`

---

## 📁 Struktura plików

```
ElektroBaza/
├── index.html                  # Główna aplikacja SPA (HTML + Tailwind + MathJax 3 + JS)
├── question_bank.json          # Zewnętrzna baza pytań i zadań w formacie JSON
├── img/                        # Zoptymalizowane schematy obwodów i wykresy sygnałów
│   ├── lab2_obwod_a.png
│   ├── lab2_obwod_bc.png
│   ├── lab2_obwod_d.png
│   ├── lab3_sygnal_trojkatny.png
│   └── lab3_sygnal_wykladniczy.png
├── .github/
│   └── workflows/
│       └── static.yml          # Automatyczne wdrożenie GitHub Actions na GitHub Pages
├── .gitignore
└── README.md
```
