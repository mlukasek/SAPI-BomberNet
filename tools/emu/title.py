"""Start the game in the emulator and take a picture of the title screen.

  python tools/emu/title.py [OUT.png] [--frames N] [--slow]
"""
import argparse
import os

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('out', nargs='?', default=os.path.join(emu.REPO, 'build', 'title.png'))
ap.add_argument('--frames', type=int, default=40)
ap.add_argument('--slow', action='store_true', help='CPU 2 MHz')
a = ap.parse_args()

g = emu.Game()
g.start(turbo=not a.slow)
c0 = g.run_to('_flush_screen', timeout=10000)
print(f'first flush after {c0 / emu.HZ:.0f} ms of emulated time')
g.frames(a.frames)
print(emu.screenshot(a.out))
mcp.call('pause')
