# Webomat

Automatizovaný systém pro hledání podniků bez webových stránek pomocí Google Places API.

## Popis

Webomat automaticky prohledává okolí zadané adresy, hledá podniky s dobrým hodnocením, které nemají webové stránky. Tyto podniky ukládá do lokální databáze a exportuje do CSV souboru pro další oslovení.

## Funkce

- **Automatické geocoding** - Převod adresy na GPS souřadnice
- **Nearby Search** - Hledání podniků v okolí pomocí Google Places API
- **Inteligentní filtrování** - Hodnocení ≥ 4.0, počet recenzí ≥ 10
- **SQLite databáze** - Lokální uložení výsledků
- **Export do CSV** - Snadné zpracování výsledků
- **Rate limiting** - Respektování Google API limitů

## Požadavky

- Python 3.7+
- Google Places API klíč

## Instalace

1. **Klonujte repozitář:**
```bash
git clone <repository-url>
cd webomat
```

2. **Nainstalujte závislosti:**
```bash
pip install -r requirements.txt
```

3. **Nastavte API klíč:**
```bash
cp .env.example .env
# Upravte .env soubor a vložte váš Google Places API klíč
```

## Použití

### Základní spuštění

```bash
python webomat.py
```

### Co skript dělá:

1. **Geocoding** - Převede startovní adresu na GPS souřadnice
2. **Hledání** - Najde podniky v okolí (default: 1.5km)
3. **Filtrování** - Vyfiltruje podniky s hodnocením ≥ 4.0 a ≥ 10 recenzemi
4. **Kontrola webu** - Získá detailní informace a zkontroluje přítomnost webu
5. **Uložení** - Podniky bez webu uloží do databáze
6. **Export** - Vytvoří CSV soubor s výsledky

## Konfigurace

Upravte `config.py` pro změnu parametrů:

```python
START_ADDRESS = "Balbínova 5, Praha 2, Vinohrady"  # Startovní adresa
SEARCH_RADIUS = 1500  # Radius hledání v metrech
MIN_RATING = 4.0      # Minimální hodnocení
MIN_REVIEWS = 10      # Minimální počet recenzí
```

## Výstupy

- **businesses_without_website.csv** - Podniky bez webu připravené k oslovení
- **businesses.db** - SQLite databáze se všemi výsledky
- **webomat.log** - Log soubor s detailním průběhem

## Příklad výsledku

```
name,address,phone,rating,review_count,website
Dahlia Inn,20, Lípová 1444, Nové Město...,776 686 719,4.5,216,
Caffe Jungmann,2, Jungmannovo nám. 762...,224 219 501,4.4,113,
```

## API klíč

1. Přejděte na [Google Cloud Console](https://console.cloud.google.com/)
2. Vytvořte nový projekt nebo vyberte existující
3. Povolte **Places API (New)** a **Geocoding API**
4. Vytvořte API klíč v sekci Credentials
5. Vložte klíč do `.env` souboru

## Náklady

- **Google Places API**: ~$0.032 za 1000 requestů
- **SQLite databáze**: Zdarma
- **Python knihovny**: Zdarma

## Škálovatelnost

- Rate limiting: 2 sekundy mezi requesty
- Batch processing: Zpracovává po 60 podnicích (3 stránky)
- Lokální databáze: Bez omezení velikosti

## Architektura

```
webomat/
├── webomat.py          # Hlavní skript
├── config.py           # Konfigurace
├── database.py         # SQLite databáze
├── .env               # API klíč (nevkládejte do git!)
├── .env.example       # Šablona pro API klíč
├── requirements.txt    # Python závislosti
└── README.md          # Tato dokumentace
```

## Další vývoj

Plánované funkce:
- **Email automatizace** - Automatické oslovení podniků
- **Web generátor** - Vytváření jednoduchých webů
- **Rozšířené filtry** - Kategorizace podniků
- **Dashboard** - Webové rozhraní pro správu

## Licence

MIT License - můžete používat a upravovat dle libosti.

## Kontakt

Pro otázky nebo připomínky vytvořte issue v GitHub repozitáři.