# Stav a další kroky

## Cíl

Síťový BomberNet na skutečném SAPI-1 s DPI-1L v jedné místnosti se SAPI v SAPIemu, webem mzpico.com (MZ-800),
skutečným MZ-800, ZX Spectrem, CPC, PC a kýmkoli dalším přes relay `ws://api.mzpico.com/net`.
Plán: `..\SAPI_DPI-firmware\docs\plan_faze2.md` (BomberNet na SAPI).

## Stav (2026-10-16)

**Hraje se: skutečné SAPI-1 s DPI-1L proti SAPIemu 0.6.0 přes produkční relay**, i víc zápasů po sobě, bez
desynchronizace (Martin: „teď to hraje“). Repo je veřejné: `github.com/mlukasek/SAPI-BomberNet` (bez LICENSE).

| Co | Stav |
|---|---|
| Jádro | BomberNet `c6d40a0` jako submodul, verze 0.2.0, `BUILD_ID 0604h`, beze změny |
| Platforma SAPI | `sapi/`: CGA-1V, 82C54, YM3812, Consul 262.3 a EKL-1, joystick MPH-1V, porty DPI-1L; `BOMBNET.COM` asi 38 KB |
| Determinismus | nahrávky z PC simulátoru: kooperace 1 hráč 447 snímků, deathmatch 2 hráči 993, deathmatch 4 hráči 1499, kooperace 4 hráči 819, **0 rozdílů** hashe |
| Rychlost | 4 MHz: medián 43–46 ms na snímek, 90 % do 58 ms (jako skutečné CPC). **2 MHz nehratelné** (91 ms), TURBO nutné |
| Síť v emulátoru | dvě SAPIemu 0.6.0 (karta DPI-1L) spolu: 8 kol deathmatche bez desynchronizace (`tools/emu/netplay.py`) |
| Skutečné SAPI | host (klávesnice, TURBO) × SAPIemu (CLI i GUI): plynule 59 ms na snímek, 5 zápasů po sobě bez restartu |
| Ovládání | šipky po celých políčkách (i rychlé ťukání a zatáčení), joystick ve hře i v menu |
| Titulek | „MZPICO+ML V0.2.0“: značka verze pro SAPI, kreslí ji platforma |

## Kde je hra

- Skutečné SAPI: `BOMBNET.COM` na disku A: (emulovaný RAM disk DPI, `/RAMDISK/RD60.BIN`) a v kořeni SD karty DPI
  (`DPI GET BOMBNET.COM`).
- SAPIemu-release: na RAM disku sestavy `sapi1v_BomberNet` (A:, ECMON volba **3**, pak `BOMBNET`).
- Nasazení nové verze: `docs/vyvoj.md`, Nasazení.

## Opravené chyby (2026-10-16)

- **Chyba z88dk 2.4** (2025-10-02): ternární operátor v `net_lockstep_poll` přeložen špatně, síťový zápas
  nedostal žádné klávesy. Překlad nočním z88dk (`Tools\z88dk-nightly`, 2026-10-15), jako BomberNet (snap edge).
- **Paleta:** `ld de,(…)` z rozvinutého C makra načetlo DE z paměti (na skutečném SAPI „žluté“ barvy a 96 bajtů
  zapsaných jinam). Teď čísla v asm, paleta v zatemnění (STATUS D7).
- **READY hostitele nedošlo na relay:** chyba firmwaru DPI (rámec WebSocketu dvěma `tcp_write`, halda lwIP 4000 B),
  opraveno ve firmwaru (`..\SAPI_DPI-firmware\docs\mereni.md`).
- **Mezipolohy z klávesnice** (tři příčiny):
  1. stisk stárnul i ve snímku, ve kterém ho hra nepřečetla;
  2. jiný směr přepsal rozdělané políčko;
  3. strop podržení uřízl přidané políčko.

  Test `taps.py --fast`: předchozí verze 21 mezipoloh ze 120 ťuknutí, nová 0. Předávka pro assemblerovou verzi:
  `..\SAPI-Bomberman\docs\predavka-klavesnice.md`.
- **Mezera na titulku položila bombu** v prvním snímku zápasu: palba teď platí jeden snímek.

## Další kroky

1. Proti webu mzpico.com (MZ-800) a dalším platformám, hra s joystickem na skutečném SAPI.
2. Firmware DPI: SD karta dvakrát za běhu přestala odpovídat (zotavení po chybě, SPI 12,5 MHz), druhý USB port
   (COM18) jednou přestal přenášet (`..\SAPI_DPI-firmware\docs\mereni.md`).
3. Zrychlit porovnání buněk ve `flush_screen` (asi 9 ms), pokud to bude potřeba.

## Otevřené otázky

- **Desync jednou** (SAPI host po předchozím zápase, GUI SAPIemu čerstvě JOIN, mapy se lišily od začátku).
  Nezopakoval se: v emulátorech v obou pořadích (čerstvý × použitý) ani v 5 zápasech SAPI × GUI po sobě
  (`tools/emu/watch.py`). Při dalším výskytu porovnat záznam `watch.py` (seed, místa, hashe) z obou stran.
- Na autorově JPR-1V je TURBO normálně rozpojené (2 MHz). BomberNet potřebuje 4 MHz.
- EKL-1 má asi autorepeat: držená šipka přidává políčka (nejvýš jedno dopředu). Ověřit na skutečné klávesnici.
- Po Ctrl+C (konec hry do CP/M) se konzole CP/M může přepnout ze sériové linky na AND-1V (podle DCD při teplém
  startu). Pro nástroje na COM18 pak `load.py --reset serial --boot 3`.
