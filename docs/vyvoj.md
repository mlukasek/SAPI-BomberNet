# Vývoj: překlad, emulátor, ověřování

## Co je potřeba

| Co | Kde (u autora) | Na co |
|---|---|---|
| z88dk, noční build | `E:\SAPI_GIT\Tools\z88dk-nightly` (2026-10-15, proměnná `Z88DK`) | překlad (`zcc +cpm`); **ne 2.4**, viz Pasti |
| Python 3 | | tabulky, skripty emulátoru |
| SAPIemu release | `E:\SAPI_GIT\SAPIemu-release` (0.6.0, karta DPI-1L) | běh a ověřování přes MCP |
| WSL s gcc | Ubuntu | PC simulátor BomberNetu (nahrávky) |
| znakový generátor MZ-700 | `..\SAPI-Bomberman-private\cgrom.bin` (mimo repo) | jen pro `tools/make_tables.py` |

Po klonování: `git submodule update --init` (BomberNet).

## Překlad

- `build.cmd` → `build\bombnet.com` (39 236 B s BomberNetem 0.3.0) a `build\bombnet.map` (symboly pro skripty).
- Ze submodulu se překládá `c/core`, `c/common/netdev_card.c` a `c/cpu/z80/loops.c` (do 0.2.0
  `c/common/z80_loops.c`). Po posunu submodulu zkontrolovat, jestli upstream nepřesunul soubory, a projít změny
  `c/core/platform.h` (co musí platforma nově umět).
- Optimalizace z88dk: proměnná `ZOPT` (výchozí `-O2`; `-O3` nic nezrychlí).
- Tabulky obrazovky po změně tabulek MZ v BomberNetu: `python tools/make_tables.py [--cgrom SOUBOR]`.

## Emulátor

- Bez okna, pro skripty: ve složce `SAPIemu-release`
  `sapiemu-cli --machine machines/sapi1v.sapi --mcp --mcp-port 8592` (na pozadí). Jiný port nebo GUI (8580):
  proměnná `SAPIEMU_MCP`.
- **CP/M v sestavě V naběhne volbou ECMONu 3** (s disky IDE). Volby 0–2 čekají na řadič disket, který sestava
  nemá (RPD-1 na 3Ch). `tools/emu/emu.py` to dělá sám a stav uloží jako `cpm` (v paměti emulátoru).
- Hra se nahraje do paměti (`load_binary` na 0100h, PC = 0100h), na disk se neukládá.
- **Síť v emulátoru:** od release 0.6.0 sestava `machines/sapi1v_BomberNet.sapi` s kartou DPI-1L (B0h/B1h,
  relay `ws://api.mzpico.com/net`). Skripty používají její kopii `tools/emu/sapi1v_bombernet_test.sapi`: RAM disk
  `nosave` a IDE jen pro čtení, aby si dvě instance nepřepisovaly `work/` release.
- **Dvě instance pro síťový zápas:** ve složce `SAPIemu-release`
  `sapiemu-cli --machine E:/SAPI_GIT/SAPI-BomberNet/tools/emu/sapi1v_bombernet_test.sapi --mcp --mcp-port 8593`
  a totéž s portem 8594 (na pozadí). Ostatní skripty pak s `SAPIEMU_MCP=http://127.0.0.1:8593/mcp`.

## Skripty `tools/emu`

| Skript | Co dělá |
|---|---|
| `title.py [OUT.png] [--slow]` | spustí hru a vyfotí titulek |
| `controls.py [OUT.png]` | start mezerou, chůze šipkami (Consul) a joystickem, poloha hráče, snímek |
| `replay.py NAHRÁVKA.bnr [--bench] [--slow] [--frames N]` | přehraje nahrávku z PC simulátoru a porovná hash stavu v každém snímku; `--bench` měří práci snímku (od konce čekání v `plat_frame_sync` po začátek dalšího) |
| `trace.py SYMBOL...` | spustí hru a běží od symbolu k symbolu (ladění startu) |
| `netplay.py [--seconds N] [--mode 0\|1] [--ports A,B] [--shots DIR]` | síťový zápas dvou instancí (A založí místnost, B se připojí kódem; výchozí porty 8593, 8594), náhodný pohyb joystickem, ve výpisu snímek a zpoždění; po konci zápasu hned přestane (dřív až 10 s náhodných kláves, které na titulku spustily hru nebo otevřely místnost); snímky v `build/netplay` |
| `join.py KÓD [--seconds N] [--idle]` | SAPI v emulátoru se připojí do místnosti (třeba ze skutečného SAPI), dá READY a hraje joystickem |
| `rematch.py [--used-hosts]` | zápas čerstvé instance (8593) proti instanci po předchozím zápase (8594): hledání desyncu mezi zápasy |
| `watch.py [--minutes N]` | jen čte paměť: při každém zápase seed, místa, zpoždění, pozice, hash každých 16 snímků, konec; i pro GUI (`SAPIEMU_MCP=…:8580`) |
| `taps.py [--taps N] [--fast]` | ťuká šipkami v náhodných okamžicích snímku a hlídá, že hráč skončí na celém políčku |
| `esc.py [--only B,GE,…] [--root DIR]` | ESC/BREAK a znaky: staré ESC z titulku nebo kódu místnosti neopustí další zápas, starý znak nezruší kód ani se do něj nezapíše, ESC/BREAK kdykoli ve snímku opustí zápas, titulek po zápase opuštěném při umírání (15 kontrol, popis v hlavičce; `--root` pro jiný build) |
| `emu.py`, `sapimcp.py` | společné: symboly, kontrolní bod CP/M, snímek obrazovky, klient MCP |

## Nasazení nové verze

**Skutečné SAPI s DPI-1 a ZRMD-1** (2026-10-28, tak se nasadila 0.3.0; bez resetu SAPI a bez konzole, CP/M musí
stát na `A>`, protože `bus run` přepíše TPA):

```
curl -X PUT -H "X-DPI: 1" --data-binary @build/bombnet.com "http://dpi1.local/api/v1/file?path=/BOMBNET.COM&overwrite=1"
# v konzoli DPI-1 (web Konzole, telnet 23 nebo MCP console):
ramdisk save /ZRMD/A_<datum>.BIN                       # záloha A: (ZRMD-1) před změnou
bus run /DPITEST/DPI.COM GET /BOMBNET.COM A:BOMBNET.COM
bus run /DPITEST/DPI.COM PUT A:BOMBNET.COM /BOMBNCHK.COM   # kontrola: stáhnout, prvních 39 236 B = build, zbytek 1Ah
```

`DPI GET` soubor na A: přepíše (`fopen "wb"`). Starou verzi na SD si napřed přejmenovat (`/api/v1/rename`).

**Skutečné SAPI** (DPI-1L, konzole CP/M na COM18, nástroje v `..\SAPI_DPI-firmware\tools`):

```
python tools/load.py --reset serial --boot 3 --com COM18      # CP/M s konzolí na COM18 (když na ní není)
python tools/cpm_run.py --port COM18 "ERA BOMBNET.COM"
python tools/xmodem_send.py ../SAPI-BomberNet/build/bombnet.com BOMBNET.COM --port COM18
python tools/dpi_console.py "zrd flush"                       # RAM disk hned na SD kartu
python tools/cpm_run.py --port COM18 --timeout 3 "BOMBNET"
```

- Na SD kartu DPI ještě `DPI PUT BOMBNET.COM` v CP/M. `sdput.py` s firmwarem 0.2 nefunguje (příkaz `fput`).
- Když COM18 neodpovídá ani po resetu SAPI (DSM-1 `received` v `cards` stojí): restart DPI
  (`load.py firmware --reset serial --boot 3 --com COM18`), `..\SAPI_DPI-firmware\docs\mereni.md`.

**SAPIemu-release, sestava `sapi1v_BomberNet`** (RAM disk A: v `work\zrmd-1`, sdílí ho i `sapi1v.sapi`):
- GUI musí být zavřené, jinak by RAM disk při ukončení přepsalo.
- `sapiemu-cli --machine machines/sapi1v_BomberNet.sapi --mcp --mcp-port 8595`, pak přes MCP:
  1. power cycle, ECMON `3`, výzva `A>`;
  2. `load_binary` na 0100h, `ERA A:BOMBNET.COM`;
  3. **`SAVE n A:BOMBNET.COM` s n = ⌈velikost / 256⌉** (`SAVE 149` pro 38 150 B by uřízlo 6 B);
  4. `quit`: vypne stroj a uloží RAM disk.

## Nahrávky a determinismus

Hra v jedné síťové místnosti musí na každém počítači počítat úplně stejně. BomberNet to ověřuje nahrávkami:
PC simulátor zapíše stisky a hash stavu po každém snímku, port je přehraje a hashe porovná
(`BomberNet/tools/replay_cpc.py` pro CPC).

Simulátor ve WSL (příkaz z `BomberNet/tools/build_host.sh`, bez sanitizerů, výstup do `build/host`):

```
wsl -e sh -c "cd /mnt/e/SAPI_GIT/SAPI-BomberNet/BomberNet/c && mkdir -p ../../build/host && cc -O1 -g -DHOST \
  -Icore -Icommon -Iplatform/host -Iplatform/mz platform/host/sim.c platform/host/nettest.c platform/mz/tables.c \
  common/netdev_card.c core/video.c core/data.c core/game.c core/map.c core/enemy.c core/bomb.c core/player.c \
  core/bomber.c core/input.c core/netplay.c -o ../../build/host/sim"
```

Nahrávky (v `build/host`):

```
SIM_RECORD=coop.bnr ./sim 6000 4660
SIM_MODE=1 SIM_PLAYERS=2 SIM_SEED=0x1234 SIM_RECORD=dm2.bnr ./sim 1500 7
SIM_MODE=1 SIM_PLAYERS=4 SIM_SEED=0x4321 SIM_HASH=16 SIM_RECORD=dm4.bnr ./sim 1500 11
SIM_MODE=0 SIM_PLAYERS=4 SIM_SEED=0x0BB1 SIM_RECORD=coop4.bnr ./sim 1500 5
```

- `replay.py` přehrává jen první zápas nahrávky (po návratu na titulek skončí, jako `replay_cpc.py`).
- Po posunu submodulu simulátor přeložit znovu a nahrávky nahrát znovu: nahrávka platí pro verzi jádra, ze které
  je. `replay.py` jako `replay_cpc.py` od 0.3.0 předem zapíše `hit_x`, `hit_y` a `net_abort` (co zbývá po
  předchozím zápase), zápas na nich nesmí záviset. Build 0.2.0 s tím nahrávky 0.3.0 nepřehraje (rozdíl v 1. snímku).
- **Ověření 2026-10-28 (0.3.0, SAPIemu-release 0.6.0, 4 MHz):** coop 447 snímků, dm2 993, dm4 1499, coop4 819,
  všude 0 rozdílů. `--bench` dm4 600 snímků: medián 38,0 ms, 90 % 52,3 ms, 99 % 76,2 ms, přes 60 ms 26 snímků
  (začátky kol), `flush_screen` medián 9,6 ms. Při 2 MHz (300 snímků) medián 75,1 ms.
- **Po opravě klávesnice (2026-10-28, build `800a0d8f…`):** všechny čtyři nahrávky znovu 0 rozdílů, `--bench` dm4
  600 snímků beze změny (medián 38,0 ms, 90 % 52,3 ms, 99 % 76,3 ms, přes 60 ms 26 snímků, `flush_screen` 9,6 ms).
  Dále `title.py`, `controls.py`, `taps.py --taps 60 --fast` (0 mezipoloh), `esc.py` všech 15 kontrol (build před
  opravou jich 9 nesplní) a místní kontroly z kontroly za běhu: bliknutí bomby právě jeden snímek, bomba sama
  modrá, ESC i BREAK (F3) opustí zápas za 2 snímky, životy dvou hráčů zeleně a žlutě.

## Ověření síťové hry (2026-10-28, 0.3.0)

Dvě instance SAPIemu-release 0.6.0 s `tools/emu/sapi1v_bombernet_test.sapi` (porty 8601 a 8602), relay
`ws://api.mzpico.com/net`:

- `netplay.py --ports 8601,8602 --seconds 300`: celý deathmatch do vítězství (2203 snímků, zpoždění 2) bez
  desynchronizace, `net_abort` 0 na obou stranách; `watch.py` na obou instancích: 50 společných hashů, 0 rozdílů.
- ESC na připojeném během zápasu: tam „MATCH LEFT“ (`net_abort` 7), u hostitele „CONNECTION LOST“ (5).
- Smíšená místnost (`emu.Game(root=…)` se starým buildem pro jednu instanci): 0.3.0 host × 0.2.0 (851 snímků)
  i 0.2.0 host × 0.3.0 (648 snímků) bez desynchronizace.
- **Po opravě klávesnice** (build `800a0d8f…`, porty 8604 a 8605): `netplay.py --seconds 300` celý deathmatch do
  vítězství (1597 snímků za 153 s, zpoždění 2) bez desynchronizace, hlídač hashů z kontroly za běhu (mimo repo,
  jako `watch.py`) na obou instancích: 100 společných bloků po 16 snímcích, 0 rozdílů. ESC na připojeném během hry: „MATCH LEFT“ (7) a u hostitele „CONNECTION LOST“
  (5) do 0,5 s, palba vrátí oba na titulek a místní zápas potom na žádném z nich neskončí (staré ESC). ESC na
  připojeném během hlášky na konci kola, když čeká na hostitele (ten na 2,5 s pozastavený): oba zamrznou, palba
  nepomůže (chyba jádra, `docs/stav.md`, Otevřené otázky).
- `SIM_DM=1` (scénář simulátoru) zapisuje přímo do stavu hry (posune hráče, prokope mapu). Taková nahrávka se
  jinde přehrát nedá.

## Pasti

- **C makra v inline asm z88dk:** makro se rozvine i se závorkami (`#define X (0xc000 + 0x3ffd)`), takže
  `ld de,X` je `ld de,(…)`, tedy načtení z paměti. V asm používat čísla nebo makra bez závorek.
- **CP/M sestavy V naběhne jen volbou ECMONu 3** (volby 0–2 čekají na řadič disket).

- **z88dk 2.4 (2025-10-02) přeloží špatně ternární operátor** s podmínkou `a && b && …` v `net_lockstep_poll`
  (`BomberNet/c/core/netplay.c`): výsledek podmínky uloží do HL, ale skočí podle příznaku C, který poslední test
  (`and a`) vynuloval. `players[].keys` pak v síťovém zápase vždy 0. Nahrávky to neodhalí (tuhle cestu nepoužívají).
  Noční build z88dk (2026-10-15) to překládá správně, BomberNet sám se překládá snapem z88dk z větve edge.

- **Zásobník musí být pod C000h** (`REGISTER_SP=0xC000`): z88dk pro CP/M jinak dá zásobník pod BDOS a ten je
  během hry pod CGA-1V.
- `run_until` v MCP vrací `stopped: timeout` jako výsledek, ne chybu. Skripty to kontrolují.
- `read_memory` vrací nejvýš 4096 bajtů (`emu.read` čte po částech). `cycles` počítá takty 4 MHz i při 2 MHz.
- Klávesnice dává jen stisky, ne puštění (`docs/technika.md`, Ovládání). Palba drží jen jeden snímek.
- Do submodulu `BomberNet` nic nezapisovat. Simulátor se proto překládá do `build/host`, ne do
  `BomberNet/c/build` jako `build_host.sh`.
