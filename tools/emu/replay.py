"""Replay a .bnr recording (from the BomberNet host simulator) on the SAPI build and compare the state hash frame
by frame, as BomberNet tools/replay_cpc.py does for the CPC. A recording that replays with the same hashes proves
that SAPI simulates exactly like the other machines, so it can play with them in one network room.

  python tools/emu/replay.py build/host/coop.bnr [--slow] [--frames N] [--bench]

--bench also measures the work of every game frame: from the end of the wait in plat_frame_sync to the start of the
next one (the logic, then flush_screen and the colours: since BomberNet 0.3.0 the picture goes out before the wait).
The frame has 60 ms; the rest is waiting. Recordings: build/host/sim with SIM_RECORD (docs/vyvoj.md).
"""
import argparse

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('bnr')
ap.add_argument('--slow', action='store_true', help='CPU 2 MHz')
ap.add_argument('--frames', type=int, default=0, help='compare only the first N frames')
ap.add_argument('--bench', action='store_true', help='also measure the work of each frame')
a = ap.parse_args()

data = open(a.bnr, 'rb').read()
assert data[:4] == b'BNR1', 'not a BNR1 file'
seed = data[4] | data[5] << 8
mode, nplayers, inputs, hash_period = data[6], data[7], data[8:12], data[12]
records = [data[16 + i * 6:22 + i * 6] for i in range((len(data) - 16) // 6)]
if a.frames:
    records = records[:a.frames]
print(f'{a.bnr}: seed {seed:04x} mode {mode} players {nplayers} hash every {hash_period}, {len(records)} frames, '
      f'CPU {"2" if a.slow else "4"} MHz')


def poke(name, values):
    mcp.call('write_memory', address='%04X' % g.sym[name], data=' '.join('%02X' % v for v in values))


g = emu.Game()
g.start(turbo=not a.slow)
g.frames(4)
poke('_menu_mode', [mode])
poke('_menu_players', [nplayers])
poke('_menu_inputs', inputs)
poke('_match_seed', [seed & 0xff, seed >> 8])
poke('_hash_period', [hash_period])
poke('_replay_active', [1])
# what an earlier match leaves behind (a hit spot, a network abort): the next match must not depend on it (as
# BomberNet tools/replay_cpc.py)
poke('_hit_x', [9])
poke('_hit_y', [5])
poke('_net_abort', [7])
mcp.call('type_text', text=' ')                 # SPACE starts the match (held for a few frames)
TM, SH = g.sym['_title_mode'], g.sym['_state_hash']
k = mismatches = 0
started = False
work, flush = [], []
c0 = None
wait_end = None                                 # cycles at the end of the previous frame's wait
while k < len(records):
    c = g.run_to('_flush_screen', timeout=20000) if c0 is None else c0
    c0 = None
    st = emu.read(SH, 2)
    if emu.read(TM, 1)[0]:
        if started:
            break                               # the match is over: back on the title
        continue
    started = True                              # the first game flush = record 0
    h = st[0] | st[1] << 8
    rec = records[k]
    fh = rec[4] | rec[5] << 8
    if h != fh:
        mismatches += 1
        if mismatches <= 10:
            print(f'HASH MISMATCH at game frame {k}: file {fh:04x}, sapi {h:04x}')
    poke('_replay_keys', rec[:4])
    if a.bench:
        sp = int(mcp.call('get_registers')['sp'], 16)
        ret = emu.read(sp, 2)
        cf = g.run_to(ret[0] | ret[1] << 8, timeout=20000)      # back from flush_screen
        c1 = g.run_to('_plat_frame_sync', timeout=20000)          # the wait starts
        if wait_end is not None:
            work.append((c1 - wait_end) / emu.HZ)
        flush.append((cf - c) / emu.HZ)
        sp = int(mcp.call('get_registers')['sp'], 16)
        ret = emu.read(sp, 2)
        wait_end = g.run_to(ret[0] | ret[1] << 8, timeout=20000)  # the wait is over
    k += 1
    if k % 500 == 0:
        print(f'  {k} frames')
print(f'done: {k} frames compared, {mismatches} mismatches')
if work:
    s = sorted(work)
    over = sum(1 for w in work if w > 60)
    print(f'work per frame (ms): median {s[len(s) // 2]:.1f}, 90 % {s[len(s) * 9 // 10]:.1f}, '
          f'99 % {s[len(s) * 99 // 100]:.1f}, max {s[-1]:.1f}; over 60 ms: {over} of {len(work)} frames')
    s = sorted(flush)
    print(f'  of it flush_screen: median {s[len(s) // 2]:.1f}, 90 % {s[len(s) * 9 // 10]:.1f}, max {s[-1]:.1f}')
mcp.call('pause')
raise SystemExit(1 if mismatches or k == 0 else 0)
