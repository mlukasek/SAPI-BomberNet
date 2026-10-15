@echo off
rem Build BOMBNET.COM for SAPI-1 (CP/M) with z88dk: the BomberNet core (submodule) + the SAPI platform layer.
rem   build.cmd            -> build\bombnet.com, build\bombnet.map
rem z88dk: set Z88DK to its folder (default E:\SAPI_GIT\Tools\z88dk).
setlocal
if "%Z88DK%"=="" set Z88DK=E:\SAPI_GIT\Tools\z88dk
set PATH=%Z88DK%\bin;%PATH%
set ZCCCFG=%Z88DK%\lib\config
set ROOT=%~dp0
if "%ZOPT%"=="" set ZOPT=-O2
set BN=%ROOT%BomberNet\c
if not exist "%BN%\core\game.h" (
  echo BomberNet submodule missing: git submodule update --init
  exit /b 1
)
if not exist "%ROOT%build" mkdir "%ROOT%build"
cd /d "%ROOT%build"

rem Link order is memory order (as BomberNet c/CMakeLists.txt). The stack is below the CGA-1V (C000h), the
rem program never prints through the C library.
zcc +cpm %ZOPT% -m --list -I"%BN%\core" -I"%BN%\common" -I"%ROOT%sapi" ^
  -pragma-define:REGISTER_SP=0xC000 -pragma-define:CRT_ENABLE_STDIO=0 -pragma-define:CLIB_OPEN_MAX=0 ^
  -o bombnet.com ^
  "%BN%\core\bomber.c" "%BN%\core\netplay.c" "%BN%\core\data.c" "%BN%\core\map.c" "%BN%\core\game.c" ^
  "%BN%\core\input.c" "%BN%\core\video.c" "%BN%\core\enemy.c" "%BN%\core\bomb.c" "%BN%\core\player.c" ^
  "%ROOT%sapi\plat_sapi.c" "%ROOT%sapi\uc_sapi.c" "%ROOT%sapi\tables.c" ^
  "%BN%\common\netdev_card.c" "%BN%\common\z80_loops.c"
if errorlevel 1 exit /b 1
for %%f in (bombnet.com) do echo build\bombnet.com: %%~zf bytes
