"""Start the game and run from symbol to symbol, printing where it gets (debugging the start).

  python tools/emu/trace.py SYMBOL...
"""
import sys

import emu
import sapimcp as mcp

g = emu.Game()
g.start()
for name in sys.argv[1:]:
    try:
        c = g.run_to(int(name, 16) if name[0].isdigit() else name, timeout=3000)
        r = mcp.call('get_registers')
        print(f'{name}: at {c / emu.HZ:.1f} ms, sp {r.get("sp")}')
    except AssertionError as e:
        r = mcp.call('get_registers')
        print(f'{name}: NOT reached, pc {r.get("pc")} sp {r.get("sp")} next {r.get("next_instruction")}')
        break
mcp.call('pause')
