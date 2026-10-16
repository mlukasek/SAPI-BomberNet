/*
 * Tesla SAPI-1 platform layer (z88dk sccz80, +cpm target), set V.
 *
 *   screen    CGA-1V at C000h (RAM-1V MAP register 63h = C0h), EGA mode: 320 x 200, a byte is 4 pixels (high
 *             nibble, D7 leftmost) and an attribute (low nibble); a cell is 2 bytes x 8 lines, lines 80 bytes
 *             apart, cell rows 640 bytes apart. Cells are rendered in advance (tools/make_tables.py).
 *   time      MPH-1V 82C54 counter 2 (55930.4 Hz) in mode 2 sets F2 (STATUS 53h bit 7) once per game frame
 *   sound     MPH-1V YM3812 channel 0, the MZ tones; a tone plays while the game goes on (tone_poll)
 *   keys      Consul 262.3 or EKL-1 on JPR-1V ports 01h/02h: one code per key press, no releases. A press counts
 *             as held for a few frames (see kb_key). The Atari stick on the MPH-1V is the real game control.
 *
 * While the game runs the CGA hides the RAM from C000h on, CP/M is not called and the interrupts are off. The
 * program, its variables and the stack stay below C000h (REGISTER_SP in build.cmd). Ctrl+C returns to CP/M.
 * Hardware details as in SAPI-Bomberman (sapi/platform.asm, docs/technika.md).
 */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "game.h"
#include "tables.h"

#define MAPREG   0x63           /* RAM-1V MAP register */
#define MAP_CGA  0xc0           /* MAP1 = MAP2 = H: CGA-1V at C000h */
#define CGA      0xc000
#define CGA_CFG  (CGA + 0x3ffb) /* CONFIG: CPU page, shown page, mode */
#define CGA_PAL_ADDR (CGA + 0x3ffc)
#define CGA_PAL_DATA (CGA + 0x3ffd)
#define CGA_COLMASK  (CGA + 0x3ffe)

#define PIT2     0x52           /* 82C54 counter 2 */
#define PITCW    0x53           /* control word (write) */
#define MSTATUS  0x53           /* MPH-1V STATUS (read): D7 = F2 */
#define MIEN     0x54           /* MPH-1V IEN (write) */
#define JOY      0x54           /* stick K4 (read), active low: D4 fire, D3 left, D2 right, D1 up, D0 down */
#define MIACK    0x55           /* MPH-1V IACK (write) */
#define YMADDR   0x56
#define YMDATA   0x57

#define KSTB     0x01           /* P0: IN D0 = keyboard STROBE (active low), OUT D0 = ACK, D1 = buzzer off */
#define KDATA    0x02           /* P1: key code, inverted */

/* Game frame on counter 2: 55930.4 Hz. Alone 58.6 ms as the MZ (915 ticks of its 8253), in a network match
 * 59.9 ms, the pace of every machine in the room (three PAL TV frames, BomberNet plat_mz.c). */
#define FRAME_LOCAL 3278
#define FRAME_NET   3350
#define TONE_UNIT   53          /* one MZ beep unit (0.94 ms) in counter 2 ticks */
#define DELAY_TICKS 8390        /* plat_delay: 150 ms as the MZ monitor loop */

/* key presses held as frames */
#define HOLD_MOVE   4           /* one cell: the player moves one char every second frame, a cell is two chars */
#define HOLD_MOVE_MAX 8
#define HOLD_FIRE   1           /* one frame: enough for a bomb or a menu edge; longer, the SPACE that starts a
                                   match from the title would lay a bomb in its first frame */
#define HOLD_CHAR   3

const char *const plat_joy_names[PLAT_JOY_TYPES] = {"NONE    ", "MPH-1V  "};
const char *const plat_kbd_a_alt_name = "CURSOR AND CR   ";

const char *plat_input_name(uint8_t input) {
  switch (input) {
  case INPUT_KBD_A: return "CURSOR AND SPACE";
  case INPUT_KBD_B: return "WASD AND E      ";
  case INPUT_JOY1:  return "JOYSTICK MPH-1V ";
  case INPUT_JOY2:  return "JOYSTICK 2      ";
  }
  return "";
}

uint8_t plat_input_allowed(uint8_t input) {        /* one stick port on the MPH-1V */
  if (input == INPUT_JOY1) return joy_type != JOY_NONE;
  return input == INPUT_KBD_A || input == INPUT_KBD_B;
}

/* ---- small port helpers ---- */

static uint16_t ctr2_read(void) __naked {         /* counter 2, latched */
  __asm
    ld   a,0x80             ; counter 2, latch
    out  (PITCW),a
    in   a,(PIT2)
    ld   l,a
    in   a,(PIT2)
    ld   h,a
    ret
  __endasm;
}

static uint16_t frame_div;

static void frame_timer(uint16_t div) {
  outp(PITCW, 0xb4);                              /* counter 2: LSB+MSB, mode 2 */
  outp(PIT2, (uint8_t)div);
  outp(PIT2, (uint8_t)(div >> 8));
  outp(MIACK, 0x80);                              /* clear F2 */
  frame_div = div;
}

/* ticks of counter 2 since *last (the counter runs frame_div..1 again and again); *last = now */
static uint16_t ticks_since(uint16_t *last) {
  uint16_t now = ctr2_read(), d = *last - now;
  if (*last < now) d += frame_div;
  *last = now;
  return d;
}

/* ---- sound: YM3812 channel 0 ---- */

static uint8_t ym_r, ym_v;

static void ym_write(void) __naked {              /* register ym_r = ym_v; the chip needs 3.3 us and 23.5 us */
  __asm
    ld   a,(_ym_r)
    out  (YMADDR),a
    ex   (sp),hl
    ex   (sp),hl
    ld   a,(_ym_v)
    out  (YMDATA),a
    push bc
    ld   b,7
ymw_wait:
    djnz ymw_wait
    pop  bc
    ret
  __endasm;
}

static void ym(uint8_t r, uint8_t v) { ym_r = r; ym_v = v; ym_write(); }

/* modulator with feedback and a carrier sustained while the key is on: buzzy like the MZ square wave */
static const uint8_t ym_init_tab[] = {
  0x01, 0x20, 0x08, 0x00, 0xbd, 0x00, 0x20, 0x21, 0x23, 0x21, 0x40, 0x1c, 0x43, 0x04, 0x60, 0xf0, 0x63, 0xf0,
  0x80, 0x0f, 0x83, 0x0f, 0xe0, 0x00, 0xe3, 0x00, 0xc0, 0x0c, 0xb0, 0x00,
};

/* Key on with the MZ tone 1108800 / ratio Hz. F-number = K / (ratio << block), K = 1108800 * 2^20 / 49716;
 * the block makes ratio << block > K >> 10 so that the F-number fits 10 bits (SAPI-Bomberman MSTA). */
static void ym_tone(uint16_t ratio) __z88dk_fastcall __naked {
  __asm
    ex   de,hl              ; DE = ratio
    ld   a,d
    or   e
    jr   nz,yt_nz
    dec  de                 ; 0 = 65536 on the 8253
yt_nz:
    ld   b,0                ; block
yt_blk:
    ld   hl,0x5936          ; K >> 10
    or   a
    sbc  hl,de
    jr   c,yt_div
    ld   a,b
    cp   7
    jr   z,yt_max
    inc  b
    ex   de,hl
    add  hl,hl
    ex   de,hl
    jr   yt_blk
yt_max:
    ld   hl,1023
    jr   yt_set
yt_div:                     ; HL = K / DE, 10 quotient bits; the low 10 bits of K are 1111100000b
    push ix
    ld   ix,0
    ld   hl,0x5936
    ld   c,10
yt_loop:
    add  ix,ix
    ld   a,c
    cp   6
    ccf                     ; CY = next bit of K (1 while c = 10..6)
    adc  hl,hl
    jr   c,yt_big
    or   a
    sbc  hl,de
    jr   nc,yt_one
    add  hl,de
    jr   yt_next
yt_big:
    or   a
    sbc  hl,de
yt_one:
    inc  ix
yt_next:
    dec  c
    jr   nz,yt_loop
    push ix
    pop  hl
    pop  ix
yt_set:
    ld   a,0xa0             ; F-number low
    ld   (_ym_r),a
    ld   a,l
    ld   (_ym_v),a
    push bc
    push hl
    call _ym_write
    pop  hl
    pop  bc
    ld   a,b                ; key on, block, F-number high
    add  a,a
    add  a,a
    or   h
    or   0x20
    ld   (_ym_v),a
    ld   a,0xb0
    ld   (_ym_r),a
    jp   _ym_write
  __endasm;
}

/* The MZ stood still while it beeped (len units of 0.94 ms). Here the tone plays while the game goes on and
 * tone_poll ends it; a beep during a tone waits in the queue, so the tones come in the same order. */
#define TQ_SIZE 8
static uint8_t tone_on, tq_n, tq_head;
static int16_t tone_left;                       /* counter 2 ticks */
static uint16_t tone_last;
static struct { uint16_t ratio; uint8_t len; } tq[TQ_SIZE];

static void tone_play(uint16_t ratio, uint8_t len) {
  ym_tone(ratio);
  tone_left += (int16_t)((uint16_t)len * TONE_UNIT);
}

void plat_tone(uint16_t ratio, uint8_t len) {
  if (!tone_on) {
    tone_left = 0;
    tone_play(ratio, len);
    tone_last = ctr2_read();
    tone_on = 1;
  } else if (tq_n < TQ_SIZE) {
    uint8_t i = (uint8_t)((tq_head + tq_n) % TQ_SIZE);
    tq[i].ratio = ratio;
    tq[i].len = len;
    tq_n++;
  }
}

static void tone_poll(void) {
  if (!tone_on) return;
  tone_left -= (int16_t)ticks_since(&tone_last);
  while (tone_left <= 0) {
    if (!tq_n) {
      tone_on = 0;
      ym(0xb0, 0);                              /* key off */
      return;
    }
    tone_play(tq[tq_head].ratio, tq[tq_head].len);
    tq_head = (uint8_t)((tq_head + 1) % TQ_SIZE);
    tq_n--;
  }
}

/* ---- keyboard ----
 * A press is caught by polling: STROBE (P0-IN0 = 0), the code (P1, inverted), ACK until STROBE goes away (at
 * most 256 reads), ACK off, as MikroMon. Consul 262.3 gives STROBE only as a 1 ms pulse, so the keyboard is polled
 * wherever the program waits. */
static uint8_t kd_a, kf_a, kp_a;                 /* key set A: direction mask, frames left, the next direction */
static uint8_t kd_b, kf_b, kp_b;                 /* key set B (W A S D) */
static uint8_t k_space, k_cr, k_fire_b;          /* frames left */
static uint8_t k_char, k_char_f;
/* A hold ages only in a frame in which the game read it: a press caught in the middle of a frame (while reading the
 * keys, or while the lockstep waits for the network) still gets all its frames, so a cursor key always walks a whole
 * cell. Holds the game does not read go away after KB_STALE frames without a key. */
#define S_A      0x01
#define S_B      0x02
#define S_SPACE  0x04
#define S_CR     0x08
#define S_FIRE_B 0x10
#define S_CHAR   0x20
#define KB_STALE 20
static uint8_t seen, kb_idle;

void plat_exit(void);

/* A cursor key walks whole cells: a hold is HOLD_MOVE frames per cell, so it must neither be cut short nor replaced
 * half way. The same key again adds a whole cell (or nothing when the limit is reached); another direction waits
 * until the cell being walked is done. */
static void hold_dir(uint8_t *dir, uint8_t *frames, uint8_t *next, uint8_t mask) {
  if (!*frames) {
    *dir = mask;
    *frames = HOLD_MOVE;
    *next = 0;
  } else if (*dir == mask) {
    if (*frames + HOLD_MOVE <= HOLD_MOVE_MAX) *frames += HOLD_MOVE;
  } else {
    *next = mask;
  }
}

static void hold_next(uint8_t *dir, uint8_t *frames, uint8_t *next) {
  if (!*frames && *next) {
    *dir = *next;
    *frames = HOLD_MOVE;
    *next = 0;
  }
}

static void kb_key(uint8_t c) {
  uint8_t u = (c >= 'a' && c <= 'z') ? (uint8_t)(c - 32) : c;
  kb_idle = 0;
  switch (c) {
  case 0xc1: case 0x05: hold_dir(&kd_a, &kf_a, &kp_a, KEY_UP); return;        /* Consul C1-C4, EKL-1 WordStar */
  case 0xc2: case 0x18: hold_dir(&kd_a, &kf_a, &kp_a, KEY_DOWN); return;
  case 0xc3: case 0x04: hold_dir(&kd_a, &kf_a, &kp_a, KEY_RIGHT); return;
  case 0xc4: case 0x13: hold_dir(&kd_a, &kf_a, &kp_a, KEY_LEFT); return;
  case ' ': k_space = HOLD_FIRE; return;
  case 0x0d: k_cr = HOLD_FIRE; return;
  case 0x03: plat_exit(); return;                                       /* Ctrl+C: back to CP/M */
  case 0x1b: case 0x84: case 0x85: k_char = 0x1b; k_char_f = HOLD_CHAR; return;   /* ESC, BREAK */
  case 0x08: case 0x7f: k_char = 8; k_char_f = HOLD_CHAR; return;
  }
  if (u < 'A' || u > 'Z') return;
  k_char = u;
  k_char_f = HOLD_CHAR;
  switch (u) {
  case 'W': hold_dir(&kd_b, &kf_b, &kp_b, KEY_UP); break;
  case 'S': hold_dir(&kd_b, &kf_b, &kp_b, KEY_DOWN); break;
  case 'D': hold_dir(&kd_b, &kf_b, &kp_b, KEY_RIGHT); break;
  case 'A': hold_dir(&kd_b, &kf_b, &kp_b, KEY_LEFT); break;
  case 'E': k_fire_b = HOLD_FIRE; break;
  }
}

static void kb_poll(void) {
  uint8_t c, n = 0;
  if (inp(KSTB) & 1) return;                    /* STROBE inactive */
  c = (uint8_t)~inp(KDATA);
  outp(KSTB, 0x03);                             /* ACK, buzzer off */
  while (!(inp(KSTB) & 1) && --n) ;
  outp(KSTB, 0x02);                             /* ACK off */
  kb_key(c);
}

static void kb_age(void) {                      /* once per game frame, before its wait */
  if (++kb_idle > KB_STALE) {                   /* nothing pressed for a while: no hold is left */
    kb_idle = KB_STALE;
    kf_a = kf_b = kp_a = kp_b = k_space = k_cr = k_fire_b = k_char_f = k_char = 0;
  }
  if ((seen & S_A) && kf_a) kf_a--;
  if ((seen & S_B) && kf_b) kf_b--;
  hold_next(&kd_a, &kf_a, &kp_a);
  hold_next(&kd_b, &kf_b, &kp_b);
  if ((seen & S_SPACE) && k_space) k_space--;
  if ((seen & S_CR) && k_cr) k_cr--;
  if ((seen & S_FIRE_B) && k_fire_b) k_fire_b--;
  if ((seen & S_CHAR) && k_char_f && !--k_char_f) k_char = 0;
  seen = 0;
}

/* The stick also counts as key set A (menus, lobby, room code, messages), except in a match where one local player
 * has the keyboard and another one the stick: then each keeps its own. */
static uint8_t joy_as_keys(void) {
  uint8_t i, n, kbd = 0, joy = 0;
  if (joy_type == JOY_NONE) return 0;
  if (!title_mode) {
    n = menu_net != NET_OFF ? menu_local : menu_players;
    for (i = 0; i < n && i < MAX_PLAYERS; i++) {
      if (menu_inputs[i] == INPUT_KBD_A) kbd = 1;
      if (menu_inputs[i] == INPUT_JOY1) joy = 1;
    }
    if (kbd && joy) return 0;
  }
  return plat_joy(0);
}

uint8_t plat_keys_a(void) {
  uint8_t k = joy_as_keys();
  kb_poll();
  if (kf_a) { k |= kd_a; seen |= S_A; }
  if (kbd_alt_fire) {
    if (k_cr) { k |= KEY_SPACE; seen |= S_CR; }
  } else if (k_space) {
    k |= KEY_SPACE;
    seen |= S_SPACE;
  }
  return k;
}

uint8_t plat_keys_b(void) {
  uint8_t k = 0;
  kb_poll();
  if (kf_b) { k = kd_b; seen |= S_B; }
  if (k_fire_b) { k |= KEY_SPACE; seen |= S_FIRE_B; }
  return k;
}

uint8_t plat_key_char(void) {
  kb_poll();
  if (k_char_f) seen |= S_CHAR;
  return k_char;
}

uint8_t plat_joy(uint8_t n) {
  uint8_t k = 0, r;
  if (joy_type == JOY_NONE || n) return 0;
  r = (uint8_t)~inp(JOY);
  if (r & 0x02) k |= KEY_UP;
  if (r & 0x01) k |= KEY_DOWN;
  if (r & 0x08) k |= KEY_LEFT;
  if (r & 0x04) k |= KEY_RIGHT;
  if (r & 0x10) k |= KEY_SPACE;
  return k;
}

/* ---- time ---- */

void plat_frame_sync(void) {
  uint16_t div = net_active ? FRAME_NET : FRAME_LOCAL;
  if (div != frame_div) frame_timer(div);
  kb_age();
  do {
    kb_poll();
    tone_poll();
  } while (!(inp(MSTATUS) & 0x80));
  outp(MIACK, 0x80);                            /* clear F2 */
}

void plat_delay(void) {
  uint16_t last = ctr2_read(), t = 0;
  while (t < DELAY_TICKS) {
    kb_poll();
    tone_poll();
    t += ticks_since(&last);
  }
}

/* ---- the machine ---- */

static uint8_t saved_iff;

static uint8_t di_save(void) __naked {          /* L = 1 if the interrupts were on; then DI */
  __asm
    ld   a,i                ; P/V = IFF2
    di
    ld   hl,0
    ret  po
    inc  l
    ret
  __endasm;
}

static void ei_now(void) __naked {
  __asm
    ei
    ret
  __endasm;
}

/* Bt476 colours 0..31, fast enough for the vertical blanking. Plain numbers here: the C macros expand to
 * "(0xc000 + ...)", and "ld de,(...)" would load DE from memory. */
static void pal_load(void) __naked {
  __asm
    xor  a
    ld   (0xfffc),a         ; CGA_PAL_ADDR
    ld   hl,_sapi_palette
    ld   de,0xfffd          ; CGA_PAL_DATA
    ld   b,96
pl_loop:
    ld   a,(hl)
    ld   (de),a
    inc  hl
    djnz pl_loop
    ret
  __endasm;
}

static void cga_clear(void) {                   /* the CPU page: 16000 bytes, black */
  memset((void *)CGA, 0, 16000);
}

void plat_init(void) {
  uint8_t i;
  saved_iff = di_save();
  outp(MAPREG, MAP_CGA);
  *(volatile uint8_t *)CGA_CFG = 0x02;          /* CPU page B, show A, EGA mode, no interrupt */
  cga_clear();
  *(volatile uint8_t *)CGA_CFG = 0x00;          /* CPU page A */
  cga_clear();
  /* the palette in the vertical blanking: written while the picture is shown, the Bt476 shows disturbed dots.
   * STATUS D7 is a flip-flop set at the start of the blanking and cleared by CONFIG with D7 = 1. */
  *(volatile uint8_t *)CGA_CFG = 0x80;          /* clear it (CPU page A, EGA, no interrupt) */
  while (!(*(volatile uint8_t *)CGA_CFG & 0x80)) ;
  pal_load();
  *(volatile uint8_t *)CGA_COLMASK = 0x1f;      /* index = attribute, pixel */
  outp(MIEN, 0x28);                             /* gates G2 and G0, no interrupts */
  outp(MIACK, 0xc0);
  frame_timer(FRAME_LOCAL);
  for (i = 0; i < sizeof(ym_init_tab); i += 2) ym(ym_init_tab[i], ym_init_tab[i + 1]);
  outp(KSTB, 0x02);                             /* keyboard ACK off, buzzer off */
  joy_type = JOY_MPH;                           /* the set V has the MPH-1V */
}

/* Ctrl+C: leave a network room, silence, the RAM back at C000h, interrupts as they were, CP/M warm boot */
void plat_exit(void) {
  if (net_device == NETDEV_NET) net_leave();
  ym(0xb0, 0);
  outp(MAPREG, 0);
  if (saved_iff) ei_now();
  exit(0);
}

/* ---- screen ---- */

uint8_t cd_x, cd_y, cd_code;                    /* sapi_cell: the cell to draw */

/* sapi_cell: cell (cd_x, cd_y) shows logical code cd_code, a copy of its rendered cell */
static void sapi_cell(void) __naked {
  __asm
    ld   a,(_cd_y)          ; DE = C000h + 640 * y + 2 * x
    add  a,a
    ld   l,a
    ld   h,0
    ld   de,sc_rowtab
    add  hl,de
    ld   e,(hl)
    inc  hl
    ld   d,(hl)
    ld   a,(_cd_x)
    add  a,a
    add  a,e
    ld   e,a
    ld   a,d
    adc  a,0
    ld   d,a
    ld   hl,_sapi_game_idx
    ld   a,(_title_mode)
    or   a
    jr   z,sc_t
    ld   hl,_sapi_title_idx
sc_t:
    ld   a,(_cd_code)
    ld   c,a
    ld   b,0
    add  hl,bc
    ld   l,(hl)             ; cell number -> 16 bytes
    ld   h,b
    add  hl,hl
    add  hl,hl
    add  hl,hl
    add  hl,hl
    ld   bc,_sapi_cells
    add  hl,bc
    ld   bc,79
    REPT 8
    ld   a,(hl)             ; left byte (a cell starts at an even address)
    ld   (de),a
    inc  hl
    inc  e
    ld   a,(hl)             ; right byte
    ld   (de),a
    inc  hl
    ex   de,hl              ; next pixel line: +80
    add  hl,bc
    ex   de,hl
    ENDR
    ret

sc_rowtab:
    defw 0xc000, 0xc280, 0xc500, 0xc780, 0xca00, 0xcc80, 0xcf00, 0xd180
    defw 0xd400, 0xd680, 0xd900, 0xdb80, 0xde00, 0xe080, 0xe300, 0xe580
    defw 0xe800, 0xea80, 0xed00, 0xef80, 0xf200, 0xf480, 0xf700, 0xf980
    defw 0xfc00
  __endasm;
}

/* after the flush: a cell in the player's colour (the shared death frames) */
void plat_player_colour(uint8_t x, uint8_t y, uint8_t player) {
  const uint8_t *g;
  uint8_t *s, at, i;
  if (y >= SCREEN_H) return;
  g = sapi_glyphs + (uint16_t)sapi_game_glyph[shadow_vram[row_off[y] + x]] * 8;
  at = sapi_player_attr[player];
  s = (uint8_t *)(CGA + (uint16_t)y * 640 + x * 2);
  for (i = 0; i < 8; i++, s += 80) {
    s[0] = (uint8_t)((g[i] & 0xf0) | at);
    s[1] = (uint8_t)((g[i] << 4) | at);
  }
}

/* flush_screen: draw_buf -> screen, changed cells only; clears draw_buf. After clear_buffers the screen is wiped
 * in one pass and only the cells that are not blank are drawn. The interrupts are off (plat_init): the wipe and
 * the clear push with SP. */
void flush_screen(void) __naked {
  __asm
    call _tone_poll
    ld   a,(_screen_cleared)
    or   a
    jr   z,fs_scan
    xor  a
    ld   (_screen_cleared),a
    ld   (fs_sp),sp
    ld   sp,0xc000+16000    ; the CPU page, pushed from the top down
    ld   hl,0
    ld   b,250
fs_wipe:
    REPT 32
    push hl
    ENDR
    djnz fs_wipe
    ld   sp,(fs_sp)
    ld   hl,_shadow_vram    ; the screen now shows blanks
    ld   de,_shadow_vram+1
    ld   bc,999
    ld   (hl),0x20
    ldir
fs_scan:                    ; 40 compares per row, unrolled: an unchanged cell costs 36 T-states
    ld   de,_draw_buf
    ld   hl,_shadow_vram
    xor  a
    ld   (_cd_y),a
fs_row:
    ld   (fs_rowst),hl
    REPT 40
    ld   a,(de)
    cp   (hl)
    call nz,fs_chg
    inc  hl
    inc  de
    ENDR
    ld   a,(_cd_y)
    inc  a
    ld   (_cd_y),a
    cp   25
    jp   nz,fs_row

    ld   (fs_sp),sp         ; the draw buffer starts every frame empty
    ld   sp,_draw_buf+1000
    ld   hl,0x2020
    ld   b,125
fs_clr:
    push hl
    push hl
    push hl
    push hl
    djnz fs_clr
    ld   sp,(fs_sp)
    jp   _tone_poll

fs_chg:                     ; A = new code, HL = shadow, DE = draw buffer
    ld   (hl),a             ; shadow = new code
    ld   (_cd_code),a
    push hl
    push de
    ld   de,(fs_rowst)
    or   a
    sbc  hl,de
    ld   a,l
    ld   (_cd_x),a          ; column = offset in the row
    call _sapi_cell
    pop  de
    pop  hl
    ret

fs_rowst: defw 0
fs_sp: defw 0
  __endasm;
}
