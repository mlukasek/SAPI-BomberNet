"""Check the controls in the emulator: start a match with SPACE, walk with the cursor keys (Consul 262.3), then
with the joystick of the MPH-1V, and print where player 1 stands.

  python tools/emu/controls.py [OUT.png]
"""
import os
import sys

import emu
import sapimcp as mcp

g = emu.Game()
g.start()
g.frames(4)
P = g.sym['_players']                           # player_t: active, input, keys, x, y, ...


def pos():
    p = emu.read(P, 5)
    return p[3], p[4]


mcp.call('type_text', text=' ')                 # SPACE: start (player 1 = cursor keys and SPACE)
while emu.read(g.sym['_title_mode'], 1)[0]:
    g.frames(1)
g.frames(30)                                    # the stage is drawn
print('start', pos())
for key in ('right', 'right', 'down', 'down'):
    mcp.call('press_key', key=key)
    g.frames(8)
    print(f'{key:6} {pos()}')
poke = lambda name, v: mcp.call('write_memory', address='%04X' % g.sym[name], data='%02X' % v)
mcp.call('write_memory', address='%04X' % (P + 1), data='03')   # player 1 input: JOYSTICK 1 (INPUT_JOY1)
for d in ('left', 'up'):
    mcp.call('joystick', port=0, pressed=[d])
    g.frames(8)
    mcp.call('joystick', port=0, pressed=[])
    g.frames(2)
    print(f'joy {d:5} {pos()}')
mcp.call('joystick', port=0, pressed=['fire1'])
g.frames(3)
mcp.call('joystick', port=0, pressed=[])
g.frames(3)
print(emu.screenshot(sys.argv[1] if len(sys.argv) > 1 else os.path.join(emu.REPO, 'build', 'controls.png')))
mcp.call('pause')
