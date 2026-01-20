# Webomat README - Installation Guide

## 🚀 Quick Start

### Windows:
```bash
# Nejprve zkontrolujte, že jste ve správném adresáři
cd C:\Users\psimek\Projects\Webomat\webomat
dir

# Pokud vidíte: streamlit_app\app.py
# Spusťte:
start_simple_fixed.bat
```

### Linux/Mac:
```bash
# Nejprve zkontrolujte adresářovou strukturu
cd /Users/psimek/Projects/Webomat/webomat
ls -la

# Pokud vidíte: streamlit_app/app.py
# Spusťte:
./start_simple_fixed.sh
```

## 📋 Co dělají vylepšené launchery:

### ✅ **Automatická detekce a instalace:**
- Kontrola existence streamlit_app\app.py
- Kontrola Python instalace (verze)
- Kontrola a automatická instalace streamlit a závislostí
- Automatická detekce volného portu (8501-8600)

### ✅ **Robustní spouštění:**
- Kontrola portu 8501 a automatické hledání volného portu
- Automatická instalace chybějících balíčků
- Automatické otevření prohlížeče se správným portem
- Emoji UI pro lepší přehlednost

### ✅ **České rozhraní s emoji:**
- Srozumitelné chybové hlášky s emoji
- Detailní instrukce pro uživatele
- Podpora pro různé scénáře
- Barevné označení stavu (✅ ⚠️ ❌ 🚀 🌐)

## 🔧 **Pokud problémy přetrvávají:**

### **Metoda 1: Ruční instalace**
```bash
# Windows:
cd C:\Users\psimek\Projects\Webomat\webomat\streamlit_app
pip install streamlit pandas plotly
python -m streamlit run app.py --server.port 8502

# Linux/Mac:
cd /Users/psimek/Projects/Webomat/webomat/streamlit_app
pip3 install streamlit pandas plotly
python3 -m streamlit run app.py --server.port 8502
```

### **Metoda 2: Virtuální prostředí**
```bash
# Vytvořit virtuální prostředí
python -m venv webomat_env

# Windows:
webomat_env\Scripts\activate

# Linux/Mac:
source webomat_env/bin/activate

# Instalace a spuštění
pip install streamlit pandas plotly
cd streamlit_app
python -m streamlit run app.py --server.port 8502
```

## 🌐 **Po úspěšném spuštění:**

1. Aplikace se otevře automaticky v prohlížeči na dostupném portu
2. **Dostupné stránky:** Dashboard, Businesses, Map, Search, Quick Generate, Settings
3. **První návštěva:** Settings → nastavit API klíče pro plnou funkcionalitu
4. **Testování:** Quick Generate → vytvořte testovací web

## 📁 **Struktura souborů:**

```
webomat/
├── start_simple_fixed.bat      # Windows launcher (doporučeno ✨)
├── start_simple_fixed.sh       # Linux/Mac launcher (doporučeno ✨)
├── install_and_setup.bat      # Instalační skript
├── README_INSTALL.md           # Tento soubor
├── start_webomat.bat          # Záložní launcher
├── start_webomat_final.bat    # Jednoduchý launcher
└── streamlit_app/              # Hlavní aplikace
    ├── app.py                  # Streamlit aplikace
    ├── requirements.txt        # Závislosti
    ├── pages/                  # Všechny stránky
    ├── components/             # UI komponenty
    └── utils/                  # Pomocné funkce
```

## 🎯 **Typické problémy a řešení:**

| Problém | Řešení |
|----------|----------|
| `'streamlit' is not recognized` | `start_simple_fixed.bat` to nainstaluje automaticky |
| `ModuleNotFoundError` | Jste ve špatném adresáři, spusťte z `webomat/` |
| `Error 500` | Zkontrolujte app.py kódování UTF-8 |
| Port 8501 obsazený | Automaticky najde volný port (8502-8600) |
| Emoji se nezobrazují | Windows 10+ by měly podporovat emoji |

## 🌟 **Nové funkce ve Streamlit aplikaci:**

- 🗺️ **Interaktivní mapa** s barevnými značkami podniků
- 🔍 **Nearby search** - hledání podniků v okolí
- 🌐 **Quick Generate** - rychlá tvorba webů z ručních vstupů
- 📊 **Real-time statistiky** s grafy a tabulkami
- 🔄 **Background tasks** s progress bary
- 🎨 **Vylepšené UI** s emoji a lepší použitelností

## 🚀 **Vylepšení v novém launcheru:**

- ✅ **Automatická instalace závislostí** (streamlit, pandas, plotly)
- ✅ **Detekce volného portu** (8501-8600)
- ✅ **Emoji UI** pro lepší přehlednost
- ✅ **Automatické otevření prohlížeče** se správným portem
- ✅ **Detailní logging** s chybovými hláškami
- ✅ **Verze Python** kontrola
- ✅ **Rychlejší start** s optimalizovaným workflow

**Doporučený způsob spuštění: `start_simple_fixed.bat` - udělá vše za vás!** 🎉

---

*Poslední aktualizace: 2026-01-20*
*Verze launcheru: 2.0 s automatickou detekcí portu a instalací závislostí*