# SAPI-BomberNet

Síťový Bomberman **[BomberNet](https://github.com/MZPico/BomberNet)** pro československý počítač
**Tesla SAPI-1**. Hraje se v jedné síťové místnosti se Sharpy MZ-800 (i ve webovém emulátoru na mzpico.com),
ZX Spectrem, Amstradem CPC a PC.

Port používá jádro hry BomberNetu beze změny (git submodul) a přidává vrstvu pro hardware SAPI-1. Síť zajišťuje
karta **[DPI-1L](https://github.com/mlukasek/SAPI_DPI-1L)** s firmwarem
[SAPI_DPI-firmware](https://github.com/mlukasek/SAPI_DPI-firmware) (Repository API a NET kompatibilní s MZPico
a Unicardem).

## Stav

Rozpracováno. Hra lokálně běží v emulátoru SAPIemu a počítá stejně jako ostatní platformy (ověřeno nahrávkami
z PC). Síťová hra čeká na emulaci DPI-1L v SAPIemu a na zkoušku na skutečném SAPI. Podrobnosti:
[docs/stav.md](docs/stav.md).

## Co je potřeba

- SAPI-1 v sestavě V: JPR-1V **s TURBO (4 MHz)**, RAM-1V, CGA-1V, MPH-1V, klávesnice Consul 262.3 nebo EKL-1,
  CP/M;
- joystick Atari na MPH-1V (doporučeno);
- pro síť karta DPI-1L s Wi-Fi.

## Ovládání

| | Klávesnice | Joystick |
|---|---|---|
| pohyb | šipky (sada A), W A S D (sada B) | páka |
| bomba, potvrzení | mezera (sada A), E (sada B) | palba |
| kód místnosti | písmena, BS/DEL maže, ESC/BREAK zruší | |
| konec do CP/M | Ctrl+C | |

Klávesnice SAPI hlásí jen stisky: jeden stisk šipky = jedno políčko. Na plynulé hraní je lepší joystick.

## Překlad

```
git clone --recurse-submodules ...
build.cmd
```

Výsledek je `build\bombnet.com` pro CP/M. Potřeba je z88dk, podrobnosti v [docs/vyvoj.md](docs/vyvoj.md).
Jak port funguje: [docs/technika.md](docs/technika.md).

## Poděkování

- BomberNet: Martin Matyáš (MZPico), podle hry Bomber Man © 1983 Hudson Soft.
- Hardwarová vrstva vychází z portu [SAPI-Bomberman](https://github.com/mlukasek/SAPI-Bomberman).
