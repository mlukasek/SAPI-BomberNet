"""Follow a network match in an emulator (only reads memory): at the start the seed, the seats, the delay, the player
positions and a picture; every hash frame the state hash; at the end the reason. For comparing two machines.

  python tools/emu/watch.py [--minutes 15]     (SAPIEMU_MCP selects the emulator, the GUI listens on 8580)
"""
import argparse
import os
import time

import emu
import sapimcp as mcp

ap = argparse.ArgumentParser()
ap.add_argument('--minutes', type=float, default=15)
a = ap.parse_args()
g = emu.Game()
r = lambda n, k=1: emu.read(g.sym[n], k)
w = lambda n: int.from_bytes(r(n, 2), 'little')
shots = os.path.join(emu.REPO, 'build', 'watch')
os.makedirs(shots, exist_ok=True)
t_end = time.time() + a.minutes * 60
matches = 0
while time.time() < t_end:
    while time.time() < t_end and not r('_net_active')[0]:
        time.sleep(0.2)
    if not r('_net_active')[0]:
        break
    matches += 1
    print(f'match {matches}: seed {w("_match_seed"):04x} mode {r("_game_mode")[0]} players {r("_player_count")[0]} '
          f'net_total {r("_net_total")[0]} slot {r("_net_slot")[0]} table {list(r("_net_table", 4))} '
          f'delay {r("_net_delay")[0]} stage {r("_stage")[0]}', flush=True)
    p = r('_players', 64)
    print('  players (active x y):', [(p[i * 16], p[i * 16 + 3], p[i * 16 + 4]) for i in range(4)], flush=True)
    time.sleep(1.5)
    emu.screenshot(os.path.join(shots, f'match{matches}_start.png'))
    last = -1
    while r('_net_active')[0]:
        f = w('_frame_no')
        if f // 16 != last:
            last = f // 16
            print(f'  frame {f} hash {w("_state_hash"):04x} abort {r("_net_abort")[0]}', flush=True)
        if r('_net_abort')[0]:
            break
        time.sleep(0.1)
    print(f'  end: frame {w("_frame_no")} abort {r("_net_abort")[0]}', flush=True)
    emu.screenshot(os.path.join(shots, f'match{matches}_end.png'))
    while r('_net_active')[0]:
        time.sleep(0.2)
