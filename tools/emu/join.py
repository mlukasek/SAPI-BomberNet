"""SAPI in the emulator joins a network room (opened on another machine, e.g. the real SAPI or the web), gets
ready and plays with random joystick moves until the match ends or --seconds pass.

  python tools/emu/join.py CODE [--seconds 300] [--idle]

Needs a sapiemu-cli with the DPI-1L (SAPIEMU_MCP, default port 8592; tools/emu/sapi1v_bombernet_test.sapi).
"""
import argparse
import os
import random
import time

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('code')
ap.add_argument('--seconds', type=float, default=300)
ap.add_argument('--idle', action='store_true', help='do not move (only follow the match)')
a = ap.parse_args()
code = a.code.upper()
assert len(code) == 4, 'the room code has 4 letters'

g = emu.Game()


def peek(name, n=1):
    return emu.read(g.sym[name], n)


def poke(name, values):
    mcp.call('write_memory', address='%04X' % g.sym[name], data=' '.join('%02X' % v for v in values))


def status():
    fn = peek('_frame_no', 2)
    return (f'title {peek("_title_mode")[0]} net_active {peek("_net_active")[0]} abort {peek("_net_abort")[0]} '
            f'frame {fn[0] | fn[1] << 8} slot {peek("_net_slot")[0]}')


g.start(turbo=True)
g.frames(4)
poke('_menu_net', [2])                          # NET_JOIN
poke('_menu_local', [1])
poke('_menu_inputs', [3, 1, 2, 0])              # the local player on the joystick
poke('_net_code', list(code.encode()))
mcp.call('resume', speed_percent=100)
mcp.call('type_text', text=' ')                 # title: the code entry
time.sleep(1.5)
mcp.call('type_text', text=' ')                 # join with the code shown
time.sleep(4)
shots = os.path.join(emu.REPO, 'build', 'join')
os.makedirs(shots, exist_ok=True)
emu.screenshot(os.path.join(shots, 'lobby.png'))
print('joined?', status())
mcp.call('type_text', text=' ')                 # ready
t0 = time.time()
while time.time() - t0 < 900 and not peek('_net_active')[0]:
    time.sleep(1)
print('match' if peek('_net_active')[0] else 'no match yet', status())
t0 = time.time()
n = 0
while time.time() - t0 < a.seconds and peek('_net_active')[0]:
    if not a.idle:
        d = random.choice(['left', 'right', 'up', 'down'])
        mcp.call('joystick', port=0, pressed=[d] + (['fire1'] if random.random() < 0.1 else []))
    time.sleep(0.5)
    n += 1
    if n % 20 == 0:
        print(f'{time.time() - t0:5.0f} s  {status()}')
mcp.call('joystick', port=0, pressed=[])
emu.screenshot(os.path.join(shots, 'end.png'))
print('end', status())
