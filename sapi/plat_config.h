/* Tesla SAPI-1, set V: JPR-1V, RAM-1V, CGA-1V, MPH-1V, Consul 262.3 or EKL-1 keyboard. */
#ifndef PLAT_CONFIG_H
#define PLAT_CONFIG_H
#define PLAT_ROWS 25            /* 40 x 25 cells of 8 x 8 pixels: the status line has its own row */
#define PLAT_JOY_TYPES 2
#define JOY_MPH 1               /* the Atari stick on K4 of the MPH-1V (port 54h) */
#define PLAT_ASM_COMPOSITE 1    /* composite_map, composite_frame in BomberNet/c/cpu/z80/loops.c */
#define PLAT_ASM_HASH 1
#define PLAT_ASM_TEXT 1         /* print_string, hud_text, title_text*, print_num* in cpu/z80/loops.c */
/* No PLAT_RUNAHEAD: a Z80 at 4 MHz has no time for frames simulated again (as the MZ-800, CPC, Spectrum). The
 * network goes through the DPI-1L (common/netdev_card.c), so NET_BINARY_INPUT (netdev_soft.c) does not apply. */
#endif
