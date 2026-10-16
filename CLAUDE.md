# SAPI-BomberNet – kontext projektu

Síťový Bomberman **BomberNet** na Tesla SAPI-1, sestava V (JPR-1V, RAM-1V, CGA-1V, MPH-1V), jako CP/M
`BOMBNET.COM`. Síť přes kartu **DPI-1L** (Repository API a NET na B0h/B1h). Hraje se v jedné místnosti s MZ-800
(web mzpico.com, MZPico, Unicard), ZX Spectrem, CPC a PC přes relay `ws://api.mzpico.com/net`.
Autor: Martin Lukášek (mlukasek). Komunikace s autorem **česky**, tykat.

## Kde co je

- **Začni tady:** `docs/stav.md` (stav, další kroky).
- `docs/technika.md`: jak je port udělaný (paměť, porty, obrazovka, klávesnice, časování, zvuk).
- `docs/vyvoj.md`: překlad, emulátor, skripty, přehrávání nahrávek, pasti.
- **BomberNet** je git submodul `BomberNet/` (repo Martina Matyáše, `github.com/MZPico/BomberNet`).
  - Jádro hry `BomberNet/c/core` a `c/common` se používá **beze změny**: stejný `BUILD_ID` a stejné hashe jsou
    podmínkou hry v jedné místnosti.
  - Do submodulu ani do `..\BomberNet` nic nezapisovat. Submodul posouvat jen na pokyn (nový build = nové hashe,
    přeložit, přehrát nahrávky).
- **Platforma SAPI:** `sapi/plat_sapi.c` (HW vrstva), `sapi/uc_sapi.c` (porty DPI-1L), `sapi/plat_config.h`,
  `sapi/tables.[ch]` (generuje `tools/make_tables.py`, needitovat).
- HW vrstva vychází z `..\SAPI-Bomberman\sapi\platform.asm` (port originálu pro jednoho hráče), síťová karta
  z `..\SAPI_DPI-firmware` (`docs/net.md`, `docs/sapiemu_dpi.md`).

## Pravidla

- **Jazyk:** kód, komentáře a skripty **anglicky**, dokumentace **česky**.
- **Emulátor:** jen release SAPIemu (`..\SAPIemu-release`). **Vývojový `..\SAPIemu` nepoužívat ani neměnit**,
  vyvíjí ho jiná session. Síťovou kartu DPI-1L do SAPIemu dělá Claude SAPIemu podle
  `..\SAPI_DPI-firmware\docs\sapiemu_dpi.md`.
- **Autorská práva:** znakový generátor MZ-700 (`cgrom.bin`, © Sharp) do repa nepatří. `sapi/tables.c` z něj
  obsahuje vykreslené dlaždice (stejně jako `cpc/tables.c` v BomberNetu a `tables.asm` v SAPI-Bomberman).
- **Licence:** bez souboru LICENSE (autor 2026-10-16, stejně jako SAPI-Bomberman): originál je Hudson Soft 1983,
  BomberNet nemá licenční soubor. Repo je veřejné, `github.com/mlukasek/SAPI-BomberNet`.
- **Git:** lokální commity průběžně, push jen na výslovné vyžádání. Na konec commitu patří řádek Co-Authored-By.
- **Zápis poznatků:** důležité věci do `docs/`, stav do `docs/stav.md`.
- **Reálný HW:** autor ho má (sestava a DPI-1L v `..\SAPI_DPI-firmware\docs\pracoviste.md`). Před akcí na
  hardwaru říct, co se stane.
