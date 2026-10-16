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

1. Proti webu mzpico.com (MZ-800) a dalším platformám, hra s joystickem.
2. SD karta v DPI: dvakrát přestala fungovat (firmware: zotavení po chybě, SPI 12,5 MHz).
3. Zrychlit porovnání buněk ve `flush_screen`, pokud to bude na skutečném SAPI potřeba.

## První zkouška na skutečném SAPI (2026-10-16 v noci)

- `BOMBNET.COM` na A: (`RD60.BIN`) i na SD kartě DPI. Spuštěno z konzole COM18, TURBO zapnuté, bez joysticku.
- Titulek a menu fungují, Martin klávesnicí nastavil NETWORK HOST a mezerou založil místnost CZSY (DPI:
  `in room`, 2 členové). SAPIemu (instance 8594, `tools/emu/join.py CZSY`) se připojil a dal READY.
- **Problém 1:** v lobby mezera (SPACE READY) nereaguje, zápas nezačal. Na titulku mezera fungovala.
  Hypotéza: v lobby se mezi snímky dlouho pracuje s DPI (STATUS, zprávy, WAIT), Consul bez 7474 dává STROBE jen
  1 ms a stisk se ztratí; nebo palba držená 1 snímek nevytvoří hranu. Zjistit typ klávesnice, vyzkoušet v SAPIemu
  s `strict` klávesnicí.
- **Problém 2:** „divné barvy“ na skutečném CGA-1V. Zjistit, jak vypadají (foto). Podezření: nový zápis palety
  v zatemnění (CONFIG 80h) nebo pořadí R, G, B a 6bitové hodnoty Bt476.

## Skutečné SAPI hraje (2026-10-16 ráno)

- **Divné barvy** byly chyba v `pal_load`: makro `CGA_PAL_DATA` se v asm rozvinulo na `(0xc000 + …)` a
  `ld de,(…)` načetlo DE z paměti. Paleta se nenahrála a 96 bajtů se zapsalo jinam. Opraveno (čísla v asm).
- **Mezera v lobby** fungovala, READY ale nedošlo na relay: chyba firmwaru DPI (rámec WebSocketu dvěma
  `tcp_write`, malá halda lwIP), opraveno ve firmwaru (`..\SAPI_DPI-firmware\docs\mereni.md`).
- **Zápas skutečné SAPI (host, klávesnice, TURBO) × SAPIemu 0.6.0 přes produkční relay běží**, 59 ms na snímek,
  bez desynchronizace. Martin: „teď to hraje“.
- `BOMBNET.COM` je i na RAM disku sestavy `sapi1v_BomberNet` v SAPIemu-release (A:, CP/M volbou 3).

- **Klávesnice: půlkroky** (Martin: „občas kročí o jednu polovinu“). Stisk šipky stárnul každý snímek, i když ho hra
  v tom snímku nepřečetla (zachycený uprostřed snímku nebo při čekání lockstepu na síť), a vydržel jen 3 čtení.
  Teď stárne jen přečtený stisk (`seen`), klávesnice se čte před vyhodnocením, nečtené stisky zmizí po 20 snímcích
  bez klávesy. `tools/emu/taps.py`: 40 ťuknutí v náhodném okamžiku snímku, 0 půlkroků.
- **Desync jednou** (SAPI host po předchozím zápase, GUI SAPIemu čerstvě JOIN, mapy se lišily od začátku).
  Nezopakoval se: v emulátorech v obou pořadích (čerstvý × použitý) bez desyncu, Martin pak 5 zápasů po sobě SAPI
  × GUI bez restartu bez desyncu (`tools/emu/watch.py`). Příčina neznámá, při dalším výskytu porovnat záznam
  `watch.py` (seed, místa, hashe).

## Otevřené otázky

- **Licence** repa (BomberNet nemá soubor LICENSE).
- Na autorově JPR-1V je TURBO rozpojené (2 MHz). BomberNet potřebuje 4 MHz.
- EKL-1 má asi autorepeat: držená šipka přidává políčka (nejvýš 2 dopředu). Ověřit na skutečné klávesnici.
