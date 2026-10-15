# Stav a další kroky

## Cíl

Síťový BomberNet na skutečném SAPI-1 s DPI-1L v jedné místnosti se SAPI v SAPIemu, webem mzpico.com (MZ-800),
skutečným MZ-800, ZX Spectrem, CPC, PC a kýmkoli dalším přes relay `ws://api.mzpico.com/net`.
Plán: `..\SAPI_DPI-firmware\docs\plan_faze2.md` (BomberNet na SAPI).

## Hotovo (2026-10-16)

- Repo se submodulem BomberNet (`c6d40a0`, verze 0.2.0, `BUILD_ID 0604h`).
- Platforma SAPI (`sapi/`): CGA-1V, 82C54, YM3812, klávesnice Consul 262.3 a EKL-1, joystick MPH-1V, porty
  DPI-1L. `BOMBNET.COM` asi 37 KB.
- V SAPIemu 0.5.0:
  - titulek, menu a hra se kreslí správně, zvuk hraje;
  - šipky (Consul) i joystick hráče vedou, palba pokládá bomby;
  - **determinismus:** nahrávky z PC simulátoru dávají na SAPI stejné hashe v každém snímku:
    kooperace 1 hráč 447 snímků, deathmatch 2 hráči 993, deathmatch 4 hráči 1499, kooperace 4 hráči 819,
    0 rozdílů;
  - rychlost: při 4 MHz medián 43–46 ms na snímek, 90 % do 58 ms (podobně jako skutečné CPC). **Při 2 MHz
    nehratelné** (91 ms).
- **Síťový zápas dvou SAPI v SAPIemu 0.6.0** (karta DPI-1L) přes produkční relay `ws://api.mzpico.com/net`
  (`tools/emu/netplay.py`): lobby (založení, kód, připojení, READY), deathmatch 90 s s náhodným pohybem joystickem
  a bombami, 8 kol, bez desynchronizace, obě obrazovky shodné.
- **Chyba z88dk 2.4** (2025-10-02): ternární operátor v `net_lockstep_poll` přeložen špatně, síťový zápas pak
  nedostal žádné klávesy. Překlad teď noční z88dk (`Tools\z88dk-nightly`, 2026-10-15), jako BomberNet (snap edge).
  Všechny nahrávky znovu ověřené, 0 rozdílů.
- Paleta CGA-1V se zapisuje v zatemnění (STATUS D7), jinak by skutečný Bt476 ukázal rušené body.

## Další kroky

1. **Síť v emulátoru:** dvě SAPIemu proti sobě hotovo. Zbývá SAPIemu proti webu mzpico.com (MZ-800).
2. **Skutečné SAPI s DPI-1L** (DPI už NET umí): `BOMBNET.COM` přes `DPI GET` ze SD, TURBO zapnuté, joystick na
   MPH-1V. Hra proti webu mzpico.com.
3. Zrychlit porovnání buněk ve `flush_screen`, pokud to bude na skutečném SAPI potřeba.

## Otevřené otázky

- **Licence** repa (BomberNet nemá soubor LICENSE).
- Na autorově JPR-1V je TURBO rozpojené (2 MHz). BomberNet potřebuje 4 MHz.
- EKL-1 má asi autorepeat: držená šipka přidává políčka (nejvýš 2 dopředu). Ověřit na skutečné klávesnici.
