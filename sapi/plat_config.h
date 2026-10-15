/* Tesla SAPI-1, set V: JPR-1V, RAM-1V, CGA-1V, MPH-1V, Consul 262.3 or EKL-1 keyboard. */
#ifndef PLAT_CONFIG_H
#define PLAT_CONFIG_H
#define PLAT_ROWS 25            /* 40 x 25 cells of 8 x 8 pixels: the status line has its own row */
#define PLAT_JOY_TYPES 2
#define JOY_MPH 1               /* the Atari stick on K4 of the MPH-1V (port 54h) */
#define PLAT_ASM_COMPOSITE 1    /* BomberNet/c/common/z80_loops.c */
#define PLAT_ASM_HASH 1
#define PLAT_ASM_TEXT 1         /* print_string, hud_text, title_text* in common/z80_loops.c */
#endif
