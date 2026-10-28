# Stav a další kroky

## Cíl

Síťový BomberNet na skutečném SAPI-1 s DPI-1L v jedné místnosti se SAPI v SAPIemu, webem mzpico.com (MZ-800),
skutečným MZ-800, ZX Spectrem, CPC, PC a kýmkoli dalším přes relay `ws://api.mzpico.com/net`.
Plán: `..\SAPI_DPI-firmware\docs\plan_faze2.md` (BomberNet na SAPI).

## Stav (2026-10-28)

**Hraje se: skutečné SAPI-1 s DPI-1L proti SAPIemu 0.6.0 přes produkční relay**, i víc zápasů po sobě, bez
desynchronizace (Martin: „teď to hraje“, ještě s verzí 0.2.0). Repo je veřejné: `github.com/mlukasek/SAPI-BomberNet`
(bez LICENSE). **Od 2026-10-28 je jádro BomberNet 0.3.0** (viz níže), na skutečném SAPI se ještě nehrálo.

| Co | Stav |
|---|---|
| Jádro | BomberNet `9961800` (v0.3.0 + jen dokumentace) jako submodul, verze 0.3.0, `BUILD_ID 0604h` (hraje s 0.2.0), beze změny |
| Platforma SAPI | `sapi/`: CGA-1V, 82C54, YM3812, Consul 262.3 a EKL-1, joystick MPH-1V, porty DPI-1L; `BOMBNET.COM` 39 241 B, konec BSS 9A49h |
| Determinismus | nahrávky z PC simulátoru 0.3.0: kooperace 1 hráč 447 snímků, deathmatch 2 hráči 993, deathmatch 4 hráči 1499, kooperace 4 hráči 819, **0 rozdílů** hashe |
| Rychlost | 4 MHz: medián 38 ms na snímek, 90 % do 52 ms (0.2.0: 46 a 58 ms). **2 MHz nehratelné** (medián 75 ms), TURBO nutné |
| Síť v emulátoru | dvě SAPIemu 0.6.0 (karta DPI-1L) s 0.3.0: celý zápas deathmatche (2203 snímků) bez desynchronizace; 0.3.0 × 0.2.0 v obou rolích bez desynchronizace (`tools/emu/netplay.py`) |
| Skutečné SAPI | s 0.2.0: host (klávesnice, TURBO) × SAPIemu (CLI i GUI): plynule 59 ms na snímek, 5 zápasů po sobě bez restartu |
| Ovládání | šipky po celých políčkách (i rychlé ťukání a zatáčení), joystick ve hře i v menu, ESC/BREAK opustí zápas |
| Titulek | „MZPICO+ML V0.3.0“: značka verze pro SAPI, kreslí ji platforma |

## Přechod na BomberNet 0.3.0 (2026-10-28)

Submodul posunut z `c6d40a0` (v0.2.0-16) na `9961800` (main 2026-10-25, tag v0.3.0 = `b8f0900`, za ním jen
návody k nastavení). Jádro `c/core` a `c/common` beze změny, `BUILD_ID` zůstal 0604h, takže 0.2.0 a 0.3.0 hrají
v jedné místnosti (ověřeno v emulátoru).

Co nového chce jádro od platformy (`c/core/platform.h`) a co na to SAPI:

| Změna v BomberNetu | SAPI (`sapi/plat_sapi.c`) |
|---|---|
| `plat_break()`: ESC/BREAK v každém herním snímku opustí zápas (místní i síťový) | stisk ESC, BREAK (84h/85h) z `kb_key`; klávesnice nehlásí puštění, proto se stisk spotřebuje |
| `plat_player_colour` s `PLAYER_FLASH`: hráč na jeden snímek v barvě bomb, když ji položí | modrá (atribut 3), modrý hráč 4 bíle (atribut 2), jako MZ; společné kreslení `colour_cell` |
| `plat_hud_colour()`: životy každého hráče ve stavovém řádku v jeho barvě (2 a víc hráčů) | buňka se překreslí jen při změně kódu nebo po smazání obrazovky (`screen_gen`), jako CPC |
| `composite_frame()` (začátek snímku, řádky 0–23 jsou kopie mapy) | asm z `c/cpu/z80/loops.c` (`PLAT_ASM_COMPOSITE`) |
| `flush_screen` ve hře smí smazat jen stavový řádek `draw_buf` | ve hře 40 B místo 1000 (asi 1,7 ms za snímek) |
| pořadí snímku: obraz (flush) před čekáním na snímek | beze změny kódu; `replay.py --bench` měří práci od konce čekání |
| `c/common/z80_loops.c` přesunut do `c/cpu/z80/loops.c` (navíc `print_num*` v asm) | `build.cmd`, `plat_config.h` |
| run-ahead (`PLAT_RUNAHEAD`, `plat_frame_idle`), binární řádky vstupu (`NET_BINARY_INPUT`) | nepoužito: run-ahead je pro rychlé stroje (PC, web, Amiga, ST), binární vstup jen pro `netdev_soft.c`; SAPI má kartu (`netdev_card.c`) jako MZ |
| zpoždění vstupu se mění během zápasu (od 1 do lobby), zvuky pro více kanálů na CPC | jen jádro; SAPI hraje tóny dál frontou na YM3812 |

Ověřeno v SAPIemu-release 0.6.0 (`docs/vyvoj.md`): titulek, nahrávky, místní zápas (šipky, joystick, `taps.py
--fast` 0 mezipoloh), bliknutí bomby a barvy stavového řádku, ESC v místním i síťovém zápase („MATCH LEFT“, druhá
strana „CONNECTION LOST“), síťové zápasy přes produkční relay.

## Kde je hra

- Skutečné SAPI: `BOMBNET.COM` na disku A: (emulovaný RAM disk DPI, `/RAMDISK/RD60.BIN`) a v kořeni SD karty DPI
  (`DPI GET BOMBNET.COM`).
- SAPIemu-release: na RAM disku sestavy `sapi1v_BomberNet` (A:, ECMON volba **3**, pak `BOMBNET`).
- Na obou místech je zatím verze 0.2.0, 0.3.0 je jen v `build\bombnet.com` (Další kroky).
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

1. **Nasadit 0.3.0** (`docs/vyvoj.md`, Nasazení): na skutečné SAPI (RAM disk DPI a SD karta) a na RAM disk sestavy
   `sapi1v_BomberNet` v SAPIemu-release. Zatím je na obou 0.2.0 (hraje s 0.3.0 v jedné místnosti).
   Na skutečném SAPI vyzkoušet ESC/BREAK v zápase (Consul 262.3 i EKL-1), bliknutí bomby a barvy životů.
2. Proti webu mzpico.com (MZ-800) a dalším platformám, hra s joystickem na skutečném SAPI.
3. Firmware DPI: SD karta dvakrát za běhu přestala odpovídat (zotavení po chybě, SPI 12,5 MHz), druhý USB port
   (COM18) jednou přestal přenášet (`..\SAPI_DPI-firmware\docs\mereni.md`).
4. Zrychlit porovnání buněk ve `flush_screen` (asi 8 ms), pokud to bude potřeba.

## Otevřené otázky

- **Desync jednou** (SAPI host po předchozím zápase, GUI SAPIemu čerstvě JOIN, mapy se lišily od začátku).
  Nezopakoval se: v emulátorech v obou pořadích (čerstvý × použitý) ani v 5 zápasech SAPI × GUI po sobě
  (`tools/emu/watch.py`). Při dalším výskytu porovnat záznam `watch.py` (seed, místa, hashe) z obou stran.
  Možná příčina, opravená v jádře 0.3.0: `run_match` teď nuluje `hit_x`, `hit_y` (patří do hashe) a `run_game`
  nuluje `net_abort`, „co zbylo po předchozím zápase“. Potvrdit to jde jen dalším hraním (SAPI s 0.3.0).
- Síťový zápas dvou SAPIemu běžel v testech v průměru asi 80–90 ms na snímek včetně přestávek mezi koly (0.2.0
  stejně, 619 snímků za 58 s proti 698 u 0.3.0). Zpoždění zůstalo 2 snímky, na 1 nekleslo. Na skutečném SAPI
  proti SAPIemu bylo 59 ms na snímek; čistý čas snímku ve dvou emulátorech zvlášť neměřen.
- Na autorově JPR-1V je TURBO normálně rozpojené (2 MHz). BomberNet potřebuje 4 MHz.
- EKL-1 má asi autorepeat: držená šipka přidává políčka (nejvýš jedno dopředu). Ověřit na skutečné klávesnici.
- Po Ctrl+C (konec hry do CP/M) se konzole CP/M může přepnout ze sériové linky na AND-1V (podle DCD při teplém
  startu). Pro nástroje na COM18 pak `load.py --reset serial --boot 3`.
