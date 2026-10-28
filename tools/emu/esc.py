"""ESC/BREAK and the other characters of the SAPI keyboard (plat_break, plat_key_char), and the title after a match
left while a player dies. The keyboard gives presses only, no releases: a press must count only where it was made.

  python tools/emu/esc.py [--trials 12] [--only B,GE,...] [--root DIR]

--root: a folder with build/bombnet.com and build/bombnet.map (default: this repo), e.g. an older build to compare.
Each check starts the game anew. ESC and BREAK (F3 = 84h on the Consul 262.3) through press_key.

  A    SPACE                                                   -> the local match runs
  B    ESC on the title, 8 frames, SPACE                        -> the match runs (an old ESC does not leave it)
  B1   ESC on the title, 1 frame, SPACE                         -> the match runs
  C    ESC, 5 cursor keys 8 frames apart, SPACE                 -> the match runs
  D    ESC, 30 frames without keys, SPACE                       -> the match runs
  E    in a match ESC, 3 frames, ESC, title, 10 frames, SPACE   -> the second match runs
  E1   in a match ESC, 1 frame, ESC, title, 4 frames, SPACE     -> the second match runs
  F    ESC or BREAK at random moments of a match                -> the title within 3 flushes, net_abort 7
  G0   room code entry (NETWORK JOIN, the relay is not needed)  -> reference picture of its box
  GW   W on the title, then the code entry                      -> the box as G0 (no old letter typed)
  GE   ESC and cursor keys on the title, then the code entry    -> it stays open (not cancelled at once)
  GT   letter B in the code entry                               -> typed
  GC   ESC in the code entry                                    -> back on the title
  GCM  then NETWORK OFF and SPACE                               -> the local match runs
  H    ESC while player 1 dies in a local deathmatch            -> the title's cells at that spot as the title draws them
"""
import argparse
import os
import random
import re

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('--root', default=emu.REPO)
ap.add_argument('--trials', type=int, default=12, help='presses in check F')
ap.add_argument('--only', default='', help='comma separated checks')
ap.add_argument('--seed', type=int, default=1)
a = ap.parse_args()
random.seed(a.seed)
ONLY = set(x for x in a.only.split(',') if x)
g = emu.Game(root=a.root)
S = g.sym
results = {}
NET_JOIN, NETDEV_NET, NET_ABORT_BREAK = 2, 3, 7
MENU_X, MENU_W, MENU_Y, MENU_H = 3, 34, 10, 10      # the menu frame of the title (BomberNet bomber.c)


def want(name):
    return not ONLY or name in ONLY


def b(name, n=1, off=0):
    return emu.read(S[name] + off, n)


def poke(name, vals):
    mcp.call('write_memory', address='%04X' % S[name], data=' '.join('%02X' % v for v in vals))


def kb_state():
    s = f"k_char {b('_k_char')[0]:02X} k_char_f {b('_k_char_f')[0]} kb_idle {b('_kb_idle')[0]}"
    if '_k_break' in S:
        s += f" k_break {b('_k_break')[0]}"
    return s


def wait_mode(mode, maxf=300):
    """flushes until title_mode == mode"""
    for i in range(maxf):
        if b('_title_mode')[0] == mode:
            return i
        g.frames(1)
    return None


def record(name, ok, msg):
    results[name] = ok
    print(('PASS ' if ok else 'FAIL ') + name + ': ' + msg, flush=True)


def start_match():
    mcp.call('type_text', text=' ')
    return wait_mode(0)


def runs_on(maxf=60):
    """flushes of the match until it is back on the title (None: it still runs)"""
    for i in range(maxf):
        g.frames(1)
        if b('_title_mode')[0] == 1:
            return i + 1
    return None


def verdict(back):
    return 'runs 60 frames' if back is None else f'LEFT after {back} flushes, net_abort {b("_net_abort")[0]}'


def old_esc(name, keys, idle, esc_frames=3):
    if not want(name):
        return
    g.start()
    g.frames(6)
    mcp.call('press_key', key='esc')
    g.frames(esc_frames)
    for k in keys:
        mcp.call('press_key', key=k)
        g.frames(8)
    g.frames(idle)
    st = kb_state()
    n = start_match()
    back = runs_on()
    record(name, back is None, f'before SPACE {st}; match after {n} title flushes, {verdict(back)}')


def double_esc(name, gap, wait):
    if not want(name):
        return
    g.start()
    g.frames(6)
    start_match()
    g.frames(30)
    mcp.call('press_key', key='esc')
    g.frames(gap)
    mcp.call('press_key', key='esc')
    n = wait_mode(1)
    g.frames(wait)
    st = kb_state()
    m = start_match()
    back = runs_on()
    record(name, back is None, f'title after {n} flushes, then {st}; second match after {m} flushes, {verdict(back)}')


if want('A'):
    g.start()
    g.frames(6)
    n = start_match()
    back = runs_on()
    record('A', back is None, f'match after {n} title flushes, {verdict(back)}')
old_esc('B', [], 5)
old_esc('B1', [], 0, esc_frames=1)
old_esc('C', ['down', 'up', 'down', 'up', 'down'], 0)
old_esc('D', [], 30)
double_esc('E', 3, 10)
double_esc('E1', 1, 4)

if want('F'):
    g.start()
    g.frames(6)
    counts, bad = [], []
    for t in range(a.trials):
        key = 'f3' if t % 3 == 2 else 'esc'
        start_match()
        g.frames(5 + random.randint(0, 10))
        mcp.call('run_for', ms=random.uniform(0, 60))       # anywhere in the frame
        mcp.call('press_key', key=key)
        n = wait_mode(1, 20)
        ab = b('_net_abort')[0]
        counts.append(n)
        if n is None or n > 3 or ab != NET_ABORT_BREAK:
            bad.append((t, key, n, ab))
        g.frames(4)
    record('F', not bad, f'{a.trials} presses (ESC, F3): flushes to the title {counts}, bad {bad}')


def box():
    return b''.join(b('_shadow_vram', MENU_W, r * 40 + MENU_X) for r in range(MENU_Y, MENU_Y + MENU_H))


def in_lobby():
    return b('_menu_locked')[0] == 1          # set for the title frame of a lobby frame, read at its flush


def open_code(pre):
    """start, NETWORK JOIN, pre() on the title, SPACE: flushes until the code entry shows (None: never)"""
    g.start()
    g.frames(6)
    if b('_net_device')[0] != NETDEV_NET:
        print('  no network card found (net_device %d): the machine needs the DPI-1L' % b('_net_device')[0])
        return None
    poke('_menu_net', [NET_JOIN])
    g.frames(2)
    pre()
    mcp.call('type_text', text=' ')
    for i in range(30):
        g.frames(1)
        if in_lobby():
            g.frames(3)
            return i + 1
    return None


def closes(n):
    """flushes until the code entry is gone (None: still open after n)"""
    for i in range(n):
        g.frames(1)
        if not in_lobby():
            return i + 1
    return None


def pre_w():
    mcp.call('type_text', text='W')
    g.frames(8)


def pre_esc():
    mcp.call('press_key', key='esc')
    g.frames(3)
    for k in ('down', 'up', 'down'):
        mcp.call('press_key', key=k)
        g.frames(8)


ref = None
if want('G0') or want('GW') or want('GT'):
    n = open_code(lambda: None)
    shut = closes(10) if n is not None else 0
    ref = box()
    record('G0', n is not None and shut is None, f'code entry after {n} flushes, its box is the reference')
if want('GW'):
    n = open_code(pre_w)
    shut = closes(10) if n is not None else 0
    same = box() == ref
    record('GW', n is not None and shut is None and same,
           f'code entry after {n} flushes, box {"as G0" if same else "DIFFERS from G0 (an old letter typed)"}')
if want('GE'):
    n = open_code(pre_esc)
    shut = closes(30) if n is not None else 0
    record('GE', n is not None and shut is None, 'code entry ' + (
        'never opened' if n is None else f'after {n} flushes, ' +
        ('open 30 flushes' if shut is None else f'CANCELLED after {shut} flushes')))
if want('GT') or want('GC') or want('GCM'):
    n = open_code(lambda: None)
    mcp.call('type_text', text='B')
    g.frames(6)
    if want('GT'):
        record('GT', n is not None and in_lobby() and box() != ref, 'letter B in the code entry')
    mcp.call('press_key', key='esc')
    shut = closes(10)
    g.frames(10)
    if want('GC'):
        record('GC', shut is not None and shut <= 3 and not in_lobby(), f'ESC: the entry closed after {shut} flushes')
    if want('GCM'):
        poke('_menu_net', [0])
        g.frames(5)
        st = kb_state()
        m = start_match()
        back = runs_on()
        record('GCM', back is None, f'NETWORK OFF, {st}; local match after {m} flushes, {verdict(back)}')

if want('H'):
    src = open(os.path.join(emu.REPO, 'sapi', 'tables.c')).read()

    def carr(name):
        i = src.index('{', src.index(name + '['))
        return bytes(int(x, 16) for x in re.findall(r'0x([0-9a-fA-F]{2})', src[i:src.index('};', i)]))

    cells, title_idx = carr('sapi_cells'), carr('sapi_title_idx')

    def player(i):
        p = emu.read(S['_players'] + 16 * i, 16)
        return dict(x=p[3], y=p[4], state=p[5], life_lost=p[8])

    def cga_cell(x, y):
        raw = emu.read(0xC000 + y * 640 + 2 * x, 7 * 80 + 2)
        return bytes(v for k in range(8) for v in (raw[k * 80], raw[k * 80 + 1]))

    g.start()
    g.frames(6)
    poke('_menu_mode', [1])                     # deathmatch, 2 players: set A and set B
    poke('_menu_players', [2])
    poke('_menu_inputs', [1, 2, 3, 4])
    g.frames(2)
    start_match()
    g.frames(25)
    mcp.call('type_text', text=' ')              # player 1 drops a bomb and stays on it
    for f in range(300):
        g.frames(1)
        if player(0)['state'] >= 6:
            break
    dying = player(0)
    g.frames(4)
    mcp.call('press_key', key='esc')
    wait_mode(1, 30)
    g.frames(8)
    p0 = player(0)
    wrong = 0
    for dy in (0, 1):
        for dx in (0, 1):
            x, y = p0['x'] + dx, p0['y'] + dy
            k = title_idx[b('_shadow_vram', 1, y * 40 + x)[0]]
            wrong += cga_cell(x, y) != cells[k * 16:k * 16 + 16]
    record('H', dying['state'] >= 6 and wrong == 0,
           f'player 1 dying at {dying["x"]},{dying["y"]}; on the title {wrong} of its 4 cells wrong')

mcp.call('pause')
print('RESULT', ' '.join(f'{k} {"ok" if v else "FAIL"}' for k, v in results.items()))
