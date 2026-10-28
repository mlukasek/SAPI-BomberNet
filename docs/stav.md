# Stav a další kroky

## Cíl

Síťový BomberNet na skutečném SAPI-1 s DPI-1L v jedné místnosti se SAPI v SAPIemu, webem mzpico.com (MZ-800),
skutečným MZ-800, ZX Spectrem, CPC, PC a kýmkoli dalším přes relay `ws://api.mzpico.com/net`.
Plán: `..\SAPI_DPI-firmware\docs\plan_faze2.md` (BomberNet na SAPI).

## Stav (2026-10-28)

**Hraje se: skutečné SAPI-1 s DPI-1L proti SAPIemu 0.6.0 přes produkční relay**, i víc zápasů po sobě, bez
desynchronizace (Martin: „teď to hraje“, ještě s verzí 0.2.0). Repo je veřejné: `github.com/mlukasek/SAPI-BomberNet`
(bez LICENSE). **Od 2026-10-28 je jádro BomberNet 0.3.0** (viz níže), **ověřené na skutečném SAPI-1** týž večer
(DPI-1, `BOMBNET.COM` na RAM disku ZRMD-1; Martin: „funguje to jako víno“).

| Co | Stav |
|---|---|
| Jádro | BomberNet `9961800` (v0.3.0 + jen dokumentace) jako submodul, verze 0.3.0, `BUILD_ID 0604h` (hraje s 0.2.0), beze změny |
| Platforma SAPI | `sapi/`: CGA-1V, 82C54, YM3812, Consul 262.3 a EKL-1, joystick MPH-1V, porty DPI-1L; `BOMBNET.COM` 39 236 B, konec BSS 9A44h |
| Determinismus | nahrávky z PC simulátoru 0.3.0: kooperace 1 hráč 447 snímků, deathmatch 2 hráči 993, deathmatch 4 hráči 1499, kooperace 4 hráči 819, **0 rozdílů** hashe |
| Rychlost | 4 MHz: medián 38 ms na snímek, 90 % do 52 ms (0.2.0: 46 a 58 ms). **2 MHz nehratelné** (medián 75 ms), TURBO nutné |
| Síť v emulátoru | dvě SAPIemu 0.6.0 (karta DPI-1L) s 0.3.0: celý zápas deathmatche (2203 snímků, po opravě klávesnice znovu 1597) bez desynchronizace; 0.3.0 × 0.2.0 v obou rolích bez desynchronizace (`tools/emu/netplay.py`) |
| Skutečné SAPI | 0.3.0 od 2026-10-28 na A: (ZRMD-1, sestava s DPI-1): Martin „funguje to jako víno“; s 0.2.0 dřív host (klávesnice, TURBO) × SAPIemu (CLI i GUI): plynule 59 ms na snímek, 5 zápasů po sobě bez restartu |
| Ovládání | šipky po celých políčkách (i rychlé ťukání a zatáčení), joystick ve hře i v menu, ESC/BREAK opustí zápas během hry (v síťovém zápase ne během hlášky na konci kola: chyba jádra, Otevřené otázky) |
| Titulek | „MZPICO+ML V0.3.0“: značka verze pro SAPI, kreslí ji platforma |

## Přechod na BomberNet 0.3.0 (2026-10-28)

Submodul posunut z `c6d40a0` (v0.2.0-16) na `9961800` (main 2026-10-25, tag v0.3.0 = `b8f0900`, za ním jen
návody k nastavení). Jádro `c/core` a `c/common` beze změny, `BUILD_ID` zůstal 0604h, takže 0.2.0 a 0.3.0 hrají
v jedné místnosti (ověřeno v emulátoru).

Co nového chce jádro od platformy (`c/core/platform.h`) a co na to SAPI:

| Změna v BomberNetu | SAPI (`sapi/plat_sapi.c`) |
|---|---|
| `plat_break()`: ESC/BREAK v každém herním snímku opustí zápas (místní i síťový) | stisk ESC, BREAK (84h/85h) zachycený ve hře od minulého herního snímku (`k_break`, oprava níže); klávesnice nehlásí puštění, proto se stisk spotřebuje |
| `plat_player_colour` s `PLAYER_FLASH`: hráč na jeden snímek v barvě bomb, když ji položí | modrá (atribut 3), modrý hráč 4 bíle (atribut 2), jako MZ; společné kreslení `colour_cell`; na titulku nic (oprava níže) |
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

## Opravy po kontrole portu 0.3.0 (2026-10-28)

Port na 0.3.0 prošly dvě nezávislé kontroly: kód (proti upstreamu a platformám MZ, CPC, ZX) a běh v emulátoru
(nahrávky, místní a síťové zápasy). Submodul, jádro, `BUILD_ID` a hashe sedí. Opraveno jen v platformě:

- **Staré ESC opustilo další zápas hned v prvním snímku.** `plat_break` bral jakýkoli nespotřebovaný stisk
  ESC/BREAK. Znak ale stárnul jen ve snímku, který ho přečetl, a titulek znaky nečte: ESC stisknuté na titulku,
  nebo ESC, kterým se zrušilo zadávání kódu místnosti či lobby, čekalo, dokud neprošlo 20 snímků bez klávesy
  (šipky v menu to počítání nulovaly). Mezera pak spustila zápas a ten hned skončil (`net_abort` 7), stejně tak
  po opuštění zápasu dvojitým ESC (nebo autorepeatem EKL-1). Teď `plat_break` počítá jen ESC/BREAK zachycené ve
  hře (`title_mode` 0) od minulého herního snímku (`k_break`), jako „klávesa je dole“ na MZ, CPC a ZX.
- **Starý znak v kódu místnosti** (už od 0.2.0): ESC z titulku zrušilo zadávání kódu hned po otevření a písmeno
  stisknuté jinde (třeba W ze sady B) se do kódu zapsalo. Znak teď stárne v každém snímku, přečtený nebo ne
  (3 snímky). Zadávání kódu ho čte v každém snímku, psaní funguje jako dřív.
- **Titulek po ESC během umírání hráče** (kosmetické): jádro volá `players_colours` i na titulku a umírající
  hráč z opuštěného zápasu dostal přes své místo na titulku znaky z herní tabulky (kus zeleného „B“ v logu).
  `plat_player_colour` na titulku nekreslí. Jádro to tak dělá na všech platformách (CPC, PC a web kreslí špatné
  znaky, MZ změní barvu), s ESC v 0.3.0 se to dá vyvolat i v místním zápase.
- **`tools/emu/netplay.py`** kontroloval konec zápasu jen každých 25 kroků a ještě až 10 s posílal náhodný
  joystick: na titulku hostitele pak začal místní zápas a připojený otevřel novou místnost. Teď hlídá konec
  v každém kroku.

Nový test `tools/emu/esc.py` (15 kontrol): build 0.3.0 před opravou (MD5 `7e372d1d…`) jich 9 nesplní (B, B1, C,
E, E1, GW, GE, GCM, H), opravený všechny. Opravený build: `BOMBNET.COM` 39 236 B, MD5
`800a0d8f4d9e17515311e83494cb3358`. Znovu ověřeno (`docs/vyvoj.md`): nahrávky 0 rozdílů, rychlost beze změny,
titulek, ovládání, `taps.py --fast`, bliknutí bomby a barvy životů, celý síťový deathmatch přes relay bez
desynchronizace, ESC v síťovém zápase.

## Kde je hra

- Skutečné SAPI (od 2026-10-28 verze **0.3.0**, MD5 800a0d8f…, 39 236 B): `BOMBNET.COM` na disku A: = fyzický
  RAM disk ZRMD-1 v sestavě s DPI-1 (záloha A: před nahráním `/ZRMD/A_1028.BIN` na SD DPI-1), a v kořeni SD karty
  DPI-1 (`DPI GET BOMBNET.COM`; předchozí verze tamtéž jako `BOMBN020.COM`) a na emulovaném RAM disku
  `/RAMDISK/RD60.BIN` na SD DPI-1 (`..\SAPI-Prince-of-Persia\tools\cpmdisk.py`, ověřeno zpětným čtením, CRC32
  obrazu B6C722D3). Na SD karty DPI-1L zatím 0.2.0 (hraje s 0.3.0 v jedné místnosti), vymění se, až bude v rámu.
- SAPIemu-release: na RAM disku sestavy `sapi1v_BomberNet` 0.3.0 (A:, ECMON volba **3**, pak `BOMBNET`).
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

1. ✔ **0.3.0 nasazená a ověřená na skutečném SAPI-1** (2026-10-28 večer): na A: (ZRMD-1, sestava s DPI-1) a v kořeni
   SD karty DPI-1, ověřeno bajt po bajtu proti `build\bombnet.com` (MD5 800a0d8f…), Martin: „funguje to jako víno“.
   Postup `docs/vyvoj.md`, Nasazení (DPI-1: `bus run` s `DPI.COM GET`, bez resetu a bez konzole). Na RAM disku sestavy
   `sapi1v_BomberNet` v SAPIemu-release je tatáž 0.3.0; vývojový SAPIemu má herní sestavu `sapi1v_BomberNet`
   s vlastním RAM diskem `media/zrmd-1/bombernet.bin` (`tools/make_hry_disk.py --bombernet`). Případně ještě
   jednotlivě: ESC/BREAK v zápase s EKL-1 (i držené ESC s autorepeatem). SD karta DPI-1L má zatím 0.2.0
   (emulovaný `RD60.BIN` na DPI-1 už 0.3.0).
2. **Nahlásit do MZPico/BomberNet** zamrznutí síťového zápasu přerušeného během hlášky na konci kola (Otevřené
   otázky), případně i barvy umírajícího hráče na titulku (`players_colours` běží i na titulku). Upstream zatím
   nemá žádné issue (2026-10-28).
3. Proti webu mzpico.com (MZ-800) a dalším platformám, hra s joystickem na skutečném SAPI.
4. Firmware DPI: SD karta dvakrát za běhu přestala odpovídat (zotavení po chybě, SPI 12,5 MHz), druhý USB port
   (COM18) jednou přestal přenášet (`..\SAPI_DPI-firmware\docs\mereni.md`).
5. Zrychlit porovnání buněk ve `flush_screen` (asi 8 ms), pokud to bude potřeba.

## Otevřené otázky

- **Síťový zápas zamrzne, když se přeruší během hlášky na konci kola** (chyba jádra, stejně s 0.2.0; našla ji
  kontrola za běhu 2026-10-28). Hláška deathmatche „DRAW / PRESS FIRE“ nebo „PLAYER n WINS THE ROUND/MATCH“
  (`show_message`) čeká na palbu ze síťových kláves. Přerušení (ESC, které jádro přečte při čekání na síť, nebo
  odpojení druhé strany) nastaví `net_abort`, `net_lockstep_poll` pak všechny klávesy nuluje a místní klávesy
  `show_message` bere jen při `net_active` 0, které nuluje až `net_match_end` po zápase. Stroj stojí na hlášce
  a palba nepomůže; druhá strana čeká, a když se první ukončí Ctrl+C, zamrzne na hlášce také. Ven jen Ctrl+C (do
  CP/M). Platforma to opravit nemůže (jádro beze změny). Návrh pro upstream: v `show_message` při `net_abort`
  skončit (zápas pak ukáže „MATCH LEFT“ nebo „CONNECTION LOST“). Na SAPI ESC během hlášky jindy nic neudělá
  (jádro ho čte jen při čekání na síť) a od opravy klávesnice platí znak jen 3 snímky.
- **Desync jednou** (SAPI host po předchozím zápase, GUI SAPIemu čerstvě JOIN, mapy se lišily od začátku).
  Nezopakoval se: v emulátorech v obou pořadích (čerstvý × použitý) ani v 5 zápasech SAPI × GUI po sobě
  (`tools/emu/watch.py`). Při dalším výskytu porovnat záznam `watch.py` (seed, místa, hashe) z obou stran.
  Možná příčina, opravená v jádře 0.3.0: `run_match` teď nuluje `hit_x`, `hit_y` (patří do hashe) a `run_game`
  nuluje `net_abort`, „co zbylo po předchozím zápase“. Potvrdit to jde jen dalším hraním (SAPI s 0.3.0).
- Síťový zápas dvou SAPIemu s 0.3.0: během hry medián 60,2 ms na snímek (tempo místnosti je 59,9 ms), s pauzami
  mezi koly (3,5–8,3 s) celkem 96–103 ms na snímek (kontroly 2026-10-28; celkové tempo 0.2.0 bylo stejné).
  Zpoždění zůstalo 2 snímky, na 1 nekleslo (to chce zpáteční cestu nejvýš 2 snímky: LAN, místní relay). Na
  skutečném SAPI proti SAPIemu bylo 59 ms na snímek.
- Na autorově JPR-1V je TURBO normálně rozpojené (2 MHz). BomberNet potřebuje 4 MHz.
- EKL-1 má asi autorepeat: držená šipka přidává políčka (nejvýš jedno dopředu). Ověřit na skutečné klávesnici.
- Po Ctrl+C (konec hry do CP/M) se konzole CP/M může přepnout ze sériové linky na AND-1V (podle DCD při teplém
  startu). Pro nástroje na COM18 pak `load.py --reset serial --boot 3`.
