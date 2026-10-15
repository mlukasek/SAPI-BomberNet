# Vývoj: překlad, emulátor, ověřování

## Co je potřeba

| Co | Kde (u autora) | Na co |
|---|---|---|
| z88dk 2.4 | `E:\SAPI_GIT\Tools\z88dk` (proměnná `Z88DK`) | překlad (`zcc +cpm`) |
| Python 3 | | tabulky, skripty emulátoru |
| SAPIemu release | `E:\SAPI_GIT\SAPIemu-release` (0.5.0) | běh a ověřování přes MCP |
| WSL s gcc | Ubuntu | PC simulátor BomberNetu (nahrávky) |
| znakový generátor MZ-700 | `..\SAPI-Bomberman-private\cgrom.bin` (mimo repo) | jen pro `tools/make_tables.py` |

Po klonování: `git submodule update --init` (BomberNet).

## Překlad

- `build.cmd` → `build\bombnet.com` (asi 37 KB) a `build\bombnet.map` (symboly pro skripty).
- Optimalizace z88dk: proměnná `ZOPT` (výchozí `-O2`; `-O3` nic nezrychlí).
- Tabulky obrazovky po změně tabulek MZ v BomberNetu: `python tools/make_tables.py [--cgrom SOUBOR]`.

## Emulátor

- Bez okna, pro skripty: ve složce `SAPIemu-release`
  `sapiemu-cli --machine machines/sapi1v.sapi --mcp --mcp-port 8592` (na pozadí). Jiný port nebo GUI (8580):
  proměnná `SAPIEMU_MCP`.
- **CP/M v sestavě V naběhne volbou ECMONu 3** (s disky IDE). Volby 0–2 čekají na řadič disket, který sestava
  nemá (RPD-1 na 3Ch). `tools/emu/emu.py` to dělá sám a stav uloží jako `cpm` (v paměti emulátoru).
- Hra se nahraje do paměti (`load_binary` na 0100h, PC = 0100h), na disk se neukládá.
- **Síť v emulátoru:** release 0.5.0 nemá kartu DPI-1L, menu NETWORK je zašedlé. Kartu dělá Claude SAPIemu
  podle `..\SAPI_DPI-firmware\docs\sapiemu_dpi.md`, pro síťové zkoušky je potřeba nový release.

## Skripty `tools/emu`

| Skript | Co dělá |
|---|---|
| `title.py [OUT.png] [--slow]` | spustí hru a vyfotí titulek |
| `controls.py [OUT.png]` | start mezerou, chůze šipkami (Consul) a joystickem, poloha hráče, snímek |
| `replay.py NAHRÁVKA.bnr [--bench] [--slow] [--frames N]` | přehraje nahrávku z PC simulátoru a porovná hash stavu v každém snímku; `--bench` měří práci snímku |
| `trace.py SYMBOL...` | spustí hru a běží od symbolu k symbolu (ladění startu) |
| `emu.py`, `sapimcp.py` | společné: symboly, kontrolní bod CP/M, snímek obrazovky, klient MCP |

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
- `SIM_DM=1` (scénář simulátoru) zapisuje přímo do stavu hry (posune hráče, prokope mapu). Taková nahrávka se
  jinde přehrát nedá.

## Pasti

- **Zásobník musí být pod C000h** (`REGISTER_SP=0xC000`): z88dk pro CP/M jinak dá zásobník pod BDOS a ten je
  během hry pod CGA-1V.
- `run_until` v MCP vrací `stopped: timeout` jako výsledek, ne chybu. Skripty to kontrolují.
- `read_memory` vrací nejvýš 4096 bajtů (`emu.read` čte po částech). `cycles` počítá takty 4 MHz i při 2 MHz.
- Klávesnice dává jen stisky, ne puštění (`docs/technika.md`, Ovládání). Palba drží jen jeden snímek.
- Do submodulu `BomberNet` nic nezapisovat. Simulátor se proto překládá do `build/host`, ne do
  `BomberNet/c/build` jako `build_host.sh`.
