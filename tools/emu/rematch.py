"""Rematch test: one emulator is started fresh, the other one plays as it is, after an earlier match (its program is
not loaded again). A desync means that some state of the earlier match stays and changes the next one.

  python tools/emu/rematch.py [--used-hosts] [--seconds 40] [--mode 0|1]

Fresh = port 8593, used = port 8594. By default the fresh one hosts; --used-hosts swaps the roles. A match still
running on the used one is left first (net_abort = 7, the end message is confirmed with fire).
"""
import argparse
import os
import random
import time

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('--seconds', type=float, default=40)
ap.add_argument('--mode', type=int, default=0)
ap.add_argument('--used-hosts', action='store_true')
a = ap.parse_args()


class Inst:
    def __init__(self, name, port):
        self.name, self.url = name, f'http://127.0.0.1:{port}/mcp'
        mcp.URL = self.url
        self.g = emu.Game()

    def call(self, tool, **args):
        mcp.URL = self.url
        return mcp.call(tool, **args)

    def peek(self, name, n=1):
        mcp.URL = self.url
        return emu.read(self.g.sym[name], n)

    def poke(self, name, values):
        self.call('write_memory', address='%04X' % self.g.sym[name], data=' '.join('%02X' % v for v in values))

    def st(self):
        fn = self.peek('_frame_no', 2)
        return (f'{self.name}: title {self.peek("_title_mode")[0]} active {self.peek("_net_active")[0]} '
                f'abort {self.peek("_net_abort")[0]} frame {fn[0] | fn[1] << 8} '
                f'seed {int.from_bytes(self.peek("_match_seed", 2), "little"):04x} '
                f'hash {int.from_bytes(self.peek("_state_hash", 2), "little"):04x} stage {self.peek("_stage")[0]}')


F, U = Inst('fresh', 8593), Inst('used', 8594)
U.call('resume', speed_percent=100)
if U.peek('_net_active')[0]:                    # leave the running match, confirm the message, back on the title
    U.poke('_net_abort', [7])
    for _ in range(40):
        time.sleep(0.5)
        if not U.peek('_net_active')[0]:
            break
for _ in range(20):
    if U.peek('_title_mode')[0]:
        break
    U.call('joystick', port=0, pressed=['fire1'])
    time.sleep(0.3)
    U.call('joystick', port=0, pressed=[])
    time.sleep(0.7)
print(U.st())
mcp.URL = F.url
F.g.start(turbo=True)
F.g.frames(4)
host, joiner = (U, F) if a.used_hosts else (F, U)
for i in (F, U):
    i.call('pause')
    i.poke('_menu_mode', [a.mode])
    i.poke('_menu_local', [1])
    i.poke('_menu_inputs', [3, 1, 2, 0])
host.poke('_menu_net', [1])
host.poke('_menu_players', [2])
joiner.poke('_menu_net', [2])
old = host.peek('_net_code', 4)
for i in (F, U):
    i.call('resume', speed_percent=100)
host.call('type_text', text=' ')
code = None
for _ in range(40):
    time.sleep(0.5)
    c = host.peek('_net_code', 4)
    if host.peek('_net_slot')[0] == 0 and c != old and c != b'AAAA':
        code = c.decode()
        break
print('room', code, 'host', host.name)
assert code
joiner.poke('_net_code', list(code.encode()))
joiner.call('type_text', text=' ')
time.sleep(1.5)
joiner.call('type_text', text=' ')
time.sleep(4)
joiner.call('type_text', text=' ')
time.sleep(1)
host.call('type_text', text=' ')
for _ in range(60):
    time.sleep(0.5)
    if F.peek('_net_active')[0] and U.peek('_net_active')[0]:
        break
print(F.st())
print(U.st())
t0 = time.time()
while time.time() - t0 < a.seconds:
    for i in (F, U):
        i.call('joystick', port=0, pressed=[random.choice(['left', 'right', 'up', 'down'])])
    time.sleep(0.5)
    if F.peek('_net_abort')[0] or U.peek('_net_abort')[0]:
        break
for i in (F, U):
    i.call('joystick', port=0, pressed=[])
print(F.st())
print(U.st())
for i in (F, U):
    mcp.URL = i.url
    emu.screenshot(os.path.join(emu.REPO, 'build', 'join', f'rematch_{i.name}.png'))
