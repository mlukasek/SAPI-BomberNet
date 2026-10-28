# Jak je port udělaný

Platforma SAPI-1 pro BomberNet: jádro hry v C (`BomberNet/c/core`, beze změny) a vrstva pro hardware sestavy V
v `sapi/`. Rozhraní, které jádro od platformy chce, je `BomberNet/c/core/platform.h`. Vzorem byla platforma
Amstrad CPC (`BomberNet/c/platform/cpc`) a hardwarová vrstva SAPI-Bombermana (`..\SAPI-Bomberman\sapi\platform.asm`).

## Hardware

- JPR-1V (Z80) **s TURBO, tedy CPU 4 MHz**. Při 2 MHz je hra pomalá (viz Rychlost).
- RAM-1V s registrem MAP na 63h a CP/M.
- CGA-1V na C000h při MAP1 = MAP2 = H (`OUT 63h,C0h`).
- MPH-1V na 50h: 82C54 (časování), YM3812 (zvuk), joystick Atari na K4.
- Klávesnice Consul 262.3 nebo EKL-1 na JPR-1V.
- Síť: DPI-1L, Repository API na B0h (příkaz a stav) a B1h (data).

## Paměť

| Adresa | Obsah |
|---|---|
| 0100–~8C69 | program a tabulky (`build\bombnet.map`) |
| ~8C6A–~9A43 | proměnné jádra i platformy (BSS je v souboru `.COM`), `draw_buf`, `map_layer`, `shadow_vram` |
| ~9A44–BFFF | zásobník (shora od C000h, `REGISTER_SP` v `build.cmd`) |
| C000–FFFF | během hry CGA-1V, RAM pod ní je skrytá (CCP a BDOS) |

- `BOMBNET.COM` má 39 236 B (BomberNet 0.3.0 s opravami klávesnice, 2026-10-28; s 0.2.0 38 150 B) a musí končit
  pod C000h.
- Během hry se nevolá CP/M (BDOS je pod CGA) a přerušení jsou zakázaná. Na tom stojí mazání obrazovky
  a `draw_buf` přes `PUSH` ve `flush_screen`.
- Ctrl+C vrátí do CP/M: opustí síťovou místnost, ztiší zvuk, vrátí RAM na C000h, obnoví přerušení a skončí
  (`exit`, teplý start CP/M).

## Obrazovka

- CGA-1V v režimu EGA: 320×200, bajt = 4 body (horní půlbajt, D7 vlevo) a atribut (dolní půlbajt). Barva bodu
  = paleta Bt476 [atribut × 2 + bod]. Atribut je tedy dvojice (pozadí, popředí).
- Buňka 8×8 = 2 bajty × 8 řádků, řádky po 80 bajtech, řádky buněk po 640 bajtech. 40×25 buněk zabere 16 000 B
  od C000h.
- **Tabulky** (`tools/make_tables.py` → `sapi/tables.c`):
  - z tabulek MZ v BomberNetu (`c/platform/mz/tables.c`: logický kód → kód znaku MZ a atribut) a ze znakového
    generátoru MZ-700 (v repu není, skript ho čte z `..\SAPI-Bomberman-private\cgrom.bin`);
  - **219 předkreslených buněk** po 16 bajtech, tabulka logický kód → buňka zvlášť pro hru a pro titulek;
  - **8 atributů**: barvy popředí MZ na černém pozadí (hra jiné pozadí nepoužívá);
  - pro barvy hráčů (`plat_player_colour`, `plat_hud_colour`) ještě 65 znaků a atributy hráčů (0 zelená,
    1 žlutá, 2 bílá, 3 modrá).
- **Barvy hráčů po `flush_screen`** (jádro 0.3.0, `players_colours` a `hud_colours`); `colour_cell` překreslí
  buňku podle `shadow_vram` daným atributem:
  - umírající hráč v barvě hráče (tabulka MZ má postavy umírání zelené);
  - **bliknutí bomby**: hráč, který právě položil bombu, je jeden snímek modrý jako bomby (`PLAYER_FLASH`), modrý
    hráč 4 bílý (jako MZ). Další snímek ho `flush_screen` překreslí normálně (jiný kód postavy);
  - **stavový řádek** (2 a víc hráčů): ikona a počet životů každého hráče v jeho barvě. Buňka se překreslí jen
    při změně kódu nebo po smazání obrazovky (`screen_gen`), jinak by to stálo čas v každém snímku (jako CPC).
  - **na titulku nic:** jádro volá `players_colours` i tam a hráč, který umíral, když se zápas opustil, by na
    titulku dostal přes jeho buňky znaky z herní tabulky (kus zeleného „B“ v logu). CPC, PC, web i MZ to mají
    také, SAPI to v `plat_player_colour` vynechá (`title_mode`).
- **Značka portu na titulku:** za „MZPICO“ (řádek 23, sloupce 28–30) je „+ML“: tahle verze pro SAPI.
  Kreslí se přímo do CGA po `flush_screen` (`title_mark`), jen když je v `shadow_vram` text „MZPICO“ a za ním
  volno. Jádro ani `draw_buf` se nemění. Znak „+“ titulková tabulka MZ nemá: `make_tables.py` ho bere ze
  znakového generátoru (kód 6Ah).
- `flush_screen` (jako na CPC):
  - porovná všech 1000 buněk `draw_buf` se `shadow_vram` (rozvinutá smyčka, nezměněná buňka 36 taktů);
  - změněnou buňku zkopíruje z předkreslených dat;
  - po `clear_buffers` smaže celou obrazovku přes `PUSH`;
  - nakonec vyplní `draw_buf` mezerami: na titulku celý, ve hře jen stavový řádek (od jádra 0.3.0 začíná každý
    herní snímek `composite_frame`, která řádky 0–23 přepíše kopií mapy; `platform.h`).
- Pořadí snímku od jádra 0.3.0 (`present_frame`): `flush_screen`, barvy hráčů, pak teprve čekání
  v `plat_frame_sync`. Obraz jde ven hned po logice, ne až po čekání (kratší odezva kláves).

## Časování

- Snímek hry odměřuje čítač 2 obvodu 82C54 (55 930,4 Hz) v režimu 2. Na konci periody nastaví F2 (STATUS 53h
  bit 7), `plat_frame_sync` na něj čeká a nuluje ho (IACK 55h).
- **Sám 58,6 ms** (3278 tiků), jako MZ. **V síťovém zápase 59,9 ms** (3350 tiků): v místnosti jedou všechny
  počítače stejným tempem (tři snímky PAL, BomberNet `plat_mz.c`).
- `plat_delay` = 150 ms jako smyčka monitoru MZ.

## Zvuk

- Tóny MZ (`plat_tone(ratio, délka)`) hraje YM3812, kanál 0 (nastavení a výpočet F-number a bloku jako
  `MSTA` v SAPI-Bombermanovi).
- **Tón nezdržuje hru:** MZ během pípnutí stál, tady tón jen začne a `tone_poll` ho ukončí podle čítače 2
  (jednotka 53 tiků = 0,94 ms). Volá se při čekání na snímek a na začátku a konci `flush_screen`.
- Pípnutí během tónu čeká ve frontě (8 míst), pořadí tónů je tedy stejné jako na MZ.

## Ovládání

- **Joystick na MPH-1V** (port 54h, aktivní v 0: D4 palba, D3 vlevo, D2 vpravo, D1 nahoru, D0 dolů) je hlavní
  ovládání. V menu „JOYSTICK“ je MPH-1V (nastaví se při startu), hráč pak může mít „JOYSTICK MPH-1V“.
  Druhý joystick na SAPI není.
- **Klávesnice** dává jen kód při stisku, bez puštění (Consul 262.3 navíc jen pulz STROBE 1 ms). Program ji čte
  stejně jako MikroMon (STROBE, kód, ACK) všude, kde čeká: v `plat_frame_sync`, `plat_delay` a při čtení kláves.
  Stisk se bere jako držený několik snímků:
  - **šipka** (Consul C1–C4, EKL-1 kódy WordStar 05, 18, 04, 13) 4 snímky = jedno políčko. Hráč se pohne o znak
    každý druhý snímek, políčko má dva znaky. Další stisk téže šipky během pohybu přidá políčko (nejvýš 8 snímků).
  - **mezera** (palba sady A), **CR** (palba sady A pro druhého hráče na klávesnici), **E** (palba sady B):
    **jeden snímek**. Stačí na bombu i na hranu v menu. Delší držení by mezerou, která na titulku spouští zápas,
    položilo bombu v jeho prvním snímku.
  - sada B: **W A S D**;
  - písmena pro kód místnosti, BS nebo DEL = mazání, ESC nebo BREAK (84h/85h) = zrušit (BREAK v BomberNetu);
    od jádra 0.3.0 ESC/BREAK také **opustí zápas** (`plat_break` v každém herním snímku, místní i síťový zápas;
    v síti „MATCH LEFT“). Počítá se jen stisk zachycený ve hře (`title_mode` 0) od minulého herního snímku
    (`k_break`): to je na SAPI „klávesa je dole“ (MZ, CPC a ZX čtou, jestli je ESC právě stisknutá). ESC z titulku,
    lobby nebo kódu místnosti tak další zápas neopustí a ESC během hlášek mezi koly ho neopustí ani v dalším kole
    (v síťovém zápase ho tam ale může přečíst jádro při čekání na síť a hra zamrzne, `docs/stav.md`, Otevřené
    otázky). Stisk se v `plat_break` spotřebuje, menu po zápasu ho už nevidí;
  - **Ctrl+C** = konec do CP/M.
- Podržení (šipky, palba) stárne jen ve snímku, ve kterém ho hra přečetla (zachycené uprostřed snímku tak nepřijde
  o snímek). Jiný směr počká na dokončení rozdělaného políčka, další stisk téže šipky přidá jen celé políčko.
  Nečtená podržení zmizí po 20 snímcích bez klávesy.
- **Znak** (písmeno, BS, ESC) stárne v každém snímku, přečtený nebo ne (3 snímky). Znaky čte jen lobby, kód
  místnosti a dlouhé čekání na síť, takže písmeno nebo ESC stisknuté jinde (titulek, zápas, W A S D sady B)
  nezruší pozdější zadávání kódu ani se do něj nezapíše. Kód místnosti čte znak v každém snímku, psaní je stejné
  jako dřív.
- **Joystick platí i jako sada A** (menu, lobby, kód místnosti, hlášky), kromě zápasu, kde má jeden místní hráč
  klávesnici a druhý joystick.

## Síť

- `sapi/uc_sapi.c` = `BomberNet/c/platform/mz/uc_mz.c` s porty B0h/B1h místo 50h/51h (50h je na SAPI MPH-1V).
- `BomberNet/c/common/netdev_card.c` beze změny. Kartu pozná podle REVD (stav `02 06 04`) a INFO (bajt 3
  bit 08h). DPI-1L odpovídá stejně jako MZPico a Unicard (`..\SAPI_DPI-firmware\docs\sapiemu_dpi.md`).
- Bez karty (nebo bez sítě) je v menu řádek NETWORK zašedlý.
- Jádro 0.3.0 mění zpoždění vstupu během zápasu (hostitel podle hlášení ostatních, 1 až hodnota z lobby). To je
  celé v jádře, platforma nic nedělá. Run-ahead (`PLAT_RUNAHEAD`) SAPI nepoužívá: je pro rychlé stroje, které
  stihnou snímky simulovat znovu (PC, web, Amiga, ST); MZ-800, CPC a Spectrum ho také nemají.

## Rychlost (SAPIemu 0.6.0, 2026-10-28, BomberNet 0.3.0)

Práce snímku = od konce čekání v `plat_frame_sync` po začátek dalšího (logika, `flush_screen`, barvy;
`tools/emu/replay.py --bench`). Snímek má 60 ms.

| Nahrávka | CPU | medián | 90 % | 99 % | snímků přes 60 ms | z toho `flush_screen` (medián) |
|---|---|---|---|---|---|---|
| deathmatch 4 hráči, hash po 16 snímcích (jako v síti), 600 snímků | 4 MHz | 38,0 ms | 52,3 ms | 76,2 ms | 4 % | 9,6 ms |
| totéž, 300 snímků | 2 MHz | 75,1 ms | 100,1 ms | 131,0 ms | 88 % | 19,1 ms |

Proti 0.2.0 (tabulka níže) asi o 8 ms méně: jádro 0.3.0 kopíruje mapu do `draw_buf` přes `LDI`
(`composite_frame`), čísla píše v asm, hash po částech bez dělení; platforma maže ve hře jen stavový řádek.

### Měření s BomberNetem 0.2.0 (SAPIemu 0.5.0, 2026-10-16)

Práce snímku = od `flush_screen` po další `plat_frame_sync` (tehdy flush po čekání, totéž měřeno jinak).

| Nahrávka | CPU | medián | 90 % | 99 % | snímků přes 60 ms | z toho `flush_screen` (medián) |
|---|---|---|---|---|---|---|
| deathmatch 4 hráči, hash po 16 snímcích (jako v síti), 600 snímků | 4 MHz | 46,2 ms | 58,1 ms | 83,2 ms | 8 % | 11,2 ms |
| totéž, 300 snímků | 2 MHz | 90,6 ms | 112,4 ms | 140,2 ms | 97 % | 22,5 ms |
| deathmatch 2 hráči, hash každý snímek | 4 MHz | 66,8 ms | 76,8 ms | 89,3 ms | 52 % | |
| kooperace 4 hráči, hash každý snímek | 4 MHz | 75,0 ms | 93,8 ms | 112,4 ms | 99 % | |

- Většinu času zabere logika jádra v C, kterou měnit nejde (hashe). Stejné je to na CPC: při čistých 4 MHz
  medián 38,9 ms a 90 % 53,9 ms, skutečné CPC asi o 20 % víc (`BomberNet/docs/port-amstrad-cpc.md`). SAPI při
  4 MHz je na tom podobně jako skutečné CPC.
- Hash v každém snímku je jen pro testy, v síťové hře se počítá po 16 snímcích.
- `-O3` místo výchozí optimalizace z88dk nepomohla.
- **Při 2 MHz** by SAPI zpomalilo celou místnost asi na dvě třetiny (lockstep čeká na nejpomalejšího).
  Na autorově JPR-1V je TURBO rozpojené (2 MHz), pro BomberNet je potřeba ho zapnout.
- Co by šlo zrychlit v platformě: porovnání 1000 buněk ve `flush_screen` (asi 8 ms). Ve hře by šlo porovnávat
  jen buňky, které se mohly změnit, ale to by potřebovalo vědět víc o jádru.
