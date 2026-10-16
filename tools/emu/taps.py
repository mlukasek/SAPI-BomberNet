"""Cursor key taps at random moments of the frame (Consul 262.3): after each tap the player must stand on a whole
cell again (odd coordinate on the axis of the move), never half way.

  python tools/emu/taps.py [--taps 40]
"""
import argparse
import random

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('--taps', type=int, default=40)
ap.add_argument('--fast', action='store_true', help='taps 0-300 ms apart (the cell is checked after a pause)')
a = ap.parse_args()
g = emu.Game()
g.start()
g.frames(4)
P = g.sym['_players']
mcp.call('type_text', text=' ')
while emu.read(g.sym['_title_mode'], 1)[0]:
    g.frames(1)
g.frames(30)
mcp.call('write_memory', address='%04X' % g.sym['_enemies'], data=' '.join(['00'] * 48))   # no enemies in the test
half = moves = 0
x0, y0 = emu.read(P, 5)[3:5]
print('start', x0, y0)
for t in range(a.taps):
    mcp.call('run_for', ms=random.uniform(0, 60))            # anywhere in the frame
    d = random.choice(['left', 'right', 'up', 'down'])
    mcp.call('press_key', key=d)
    if a.fast and random.random() < 0.7:
        mcp.call('run_for', ms=random.uniform(0, 300))  # the next tap soon, maybe in the middle of a cell
        continue
    mcp.call('run_for', ms=900)
    p = emu.read(P, 6)
    x, y, state = p[3], p[4], p[5]
    if state >= 6:
        print('the player died, stop')
        break
    moved = (x, y) != (x0, y0)
    moves += moved
    if x % 2 == 0 or y % 2 == 0:
        half += 1
        print(f'tap {t} {d}: HALF WAY at {x},{y}')
    x0, y0 = x, y
print(f'{moves} moves, {half} half way')
mcp.call('pause')
