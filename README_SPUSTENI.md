# Webomat - Opravený spouštěcí skript

## 🚀 **Jak spustit:**

### **Windows:**
```bash
cd C:\Users\psimek\Projects\Webomat
spust_webomat.bat
```

Nebo **dvakrát klikněte** na `spust_webomat.bat`.

## 📋 **Co dělá nový skript:**

### ✅ **Automatická detekce portu:**
1. **Zkontroluje port 8501** - pokud je volný, použije ho
2. **Pokud je obsazený** (jako váš jiný projekt), najde volný port výš
3. **Spustí Webomat** na nalezeném volném portu
4. **Otevře prohlížeč** s tím správným portem

### ✅ **Robustní spouštění:**
- **České popisky** a srozumitelné zprávy
- **Kódování UTF-8** pro české znaky
- **Správné adresáře** - přejde do streamlit_app složky
- **Chybové hlášení** s detailními informacemi

## 🎯 **Očekávaný výsledek:**

```
WEBOMAT - Spouštěč aplikace
============================

* Kontroluji dostupnost portu 8501...
* Port 8501 je obsazený jiným projektem
* Hledám volný port...
* Našel jsem volný port: 8502

* Spouštím Webomat na portu 8502...

=================================
   WEBOMAT BEŽÍ!
   Otevři: http://localhost:8502
=================================
```

## 🌐 **Po spuštění:**

- **Webomat se otevře na:** `http://localhost:8502` (nebo jiný volný port)
- **6 stránek:** Dashboard, Businesses, Map, Search, Quick Generate, Settings
- **První návštěva:** Settings → nastavit API klíče pro plnou funkcionalitu

## 🔧 **Pokud stále nefunguje:**

### **Ruční spuštění s volbou portu:**
```bash
cd C:\Users\psimek\Projects\Webomat\webomat\streamlit_app
streamlit run app.py --server.port 8502  # Změňte na volný port
```

### **Zastavení všech streamlit procesů:**
```bash
taskkill /f /im streamlit.exe
```

## 🌟 **Výhody nového spouštěče:**

- ✅ **Automatické řešení port konfliktů**
- ✅ **České rozhraní** s srozumitelnými zprávami
- ✅ **Robustní detekce** volného portu
- ✅ **Automatické otevření** v prohlížeči
- ✅ **Detailní logging** pro debugging

**Nyní zkuste `spust_webomat.bat` - mělo by fungovat bez port konfliktů!** 🎉