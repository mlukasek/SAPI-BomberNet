"""Network match of two SAPIs in two emulators, through the relay of the DPI-1L card (SAPIemu 0.6.0 and later).

Two sapiemu-cli with the machine tools/emu/sapi1v_bombernet_test.sapi (DPI-1L, RAM disk not saved), on the MCP
ports 8593 (A, the host) and 8594 (B, joins with the room code). Both run in real time: A creates a room, B joins
it, both get ready, then they play with random joystick moves for --seconds. The relay compares the state hashes
(every 16 frames) and reports a desync, so a match that runs on proves both simulate alike.

  python tools/emu/netplay.py [--seconds 60] [--mode 0|1] [--shots DIR]
"""
import argparse
import os
import random
import time

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('--seconds', type=float, default=60)
ap.add_argument('--mode', type=int, default=1, help='0 co-op, 1 deathmatch')
ap.add_argument('--shots', default=os.path.join(emu.REPO, 'build', 'netplay'))
ap.add_argument('--ports', default='8593,8594')
a = ap.parse_args()
os.makedirs(a.shots, exist_ok=True)

NET_HOST, NET_JOIN = 1, 2
STATES = ['nolink', 'ready', 'in room', 'running', 'desync', 'dropped', 'spectator']


class Inst:
    def __init__(self, name, port):
        self.name, self.url = name, f'http://127.0.0.1:{port}/mcp'
        self.use()
        self.g = emu.Game()

    def use(self):
        mcp.URL = self.url
        return self

    def call(self, tool, **args):
        self.use()
        return mcp.call(tool, **args)

    def peek(self, name, n=1):
        self.use()
        return emu.read(self.g.sym[name], n)

    def poke(self, name, values):
        self.call('write_memory', address='%04X' % self.g.sym[name], data=' '.join('%02X' % v for v in values))

    def shot(self, tag):
        self.use()
        return emu.screenshot(os.path.join(a.shots, f'{self.name}_{tag}.png'))

    def status(self):
        fn = self.peek('_frame_no', 2)
        return (f'{self.name}: title {self.peek("_title_mode")[0]} net_active {self.peek("_net_active")[0]} '
                f'abort {self.peek("_net_abort")[0]} frame {fn[0] | fn[1] << 8} code {self.peek("_net_code", 4).decode()}')


pa, pb = a.ports.split(',')
A, B = Inst('A', pa), Inst('B', pb)
for i in (A, B):
    i.use()
    i.g.start(turbo=True)
    i.g.frames(4)
    i.poke('_menu_mode', [a.mode])
    i.poke('_menu_local', [1])
    i.poke('_menu_inputs', [3, 1, 2, 0])         # the local player on the joystick of the MPH-1V (INPUT_JOY1)
A.poke('_menu_net', [NET_HOST])
A.poke('_menu_players', [2])
B.poke('_menu_net', [NET_JOIN])
for i in (A, B):
    i.call('resume', speed_percent=100)

A.call('type_text', text=' ')                   # host: SPACE on the title creates the room
code = None
t0 = time.time()
while time.time() - t0 < 20:
    time.sleep(0.5)
    c = A.peek('_net_code', 4).decode(errors='replace')
    if A.peek('_net_slot')[0] == 0 and c != 'AAAA':
        code = c
        break
print(A.status())
A.shot('lobby')
assert code, 'no room code'
print('room', code)
B.poke('_net_code', list(code.encode()))
B.call('type_text', text=' ')                   # joiner: SPACE on the title opens the code entry
time.sleep(1.5)
B.shot('code')
B.call('type_text', text=' ')                   # SPACE joins with the code shown
time.sleep(4)
B.shot('lobby')
B.call('type_text', text=' ')                   # ready
time.sleep(1)
A.call('type_text', text=' ')                   # the host readies last
t0 = time.time()
while time.time() - t0 < 30:
    time.sleep(0.5)
    if A.peek('_net_active')[0] and B.peek('_net_active')[0]:
        break
print(A.status())
print(B.status())
assert A.peek('_net_active')[0] and B.peek('_net_active')[0], 'the match did not start'
print('match running')

dirs = ['left', 'right', 'up', 'down']
t0 = time.time()
n = 0
while time.time() - t0 < a.seconds:
    for i in (A, B):
        p = random.choice(dirs)
        i.call('joystick', port=0, pressed=[p] + (['fire1'] if random.random() < 0.15 else []))
    time.sleep(0.4)
    n += 1
    if n % 25 == 0:
        print(f'{time.time() - t0:5.1f} s  {A.status()} | {B.status()}')
        if A.peek('_net_abort')[0] or B.peek('_net_abort')[0] or not A.peek('_net_active')[0]:
            break
for i in (A, B):
    i.call('joystick', port=0, pressed=[])
A.shot('match')
B.shot('match')
print(A.status())
print(B.status())
for i in (A, B):
    i.call('pause')
