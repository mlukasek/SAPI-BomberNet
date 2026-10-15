"""Shared helpers of the emulator scripts: symbols of the build, the CP/M checkpoint, the game in memory.

SAPIemu release (sapiemu-cli --machine machines/sapi1v.sapi --mcp --mcp-port 8592), see docs/vyvoj.md.
The game is build/bombnet.com, its symbols build/bombnet.map (build.cmd).
"""
import base64
import os
import re
import zlib

import sapimcp as mcp

REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
HZ = 4000   # emulator 'cycles' per ms: they count the 4 MHz clock also when the CPU runs at 2 MHz


def symbols(root=REPO):
    sym = {}
    for line in open(os.path.join(root, 'build', 'bombnet.map')):
        m = re.match(r'(\S+)\s+=\s+\$([0-9A-F]+)\s*;', line)
        if m:
            sym[m.group(1)] = int(m.group(2), 16)
    return sym


def read(addr, n):
    """n bytes from addr (read_memory gives at most 4096 per call)."""
    out = b''
    while len(out) < n:
        k = min(4096, n - len(out))
        h = mcp.call('read_memory', address='%04X' % (addr + len(out)), length=k, format='hex')
        b = bytes.fromhex(re.sub(r'[^0-9A-Fa-f]', '', h))
        assert len(b) == k, ('read_memory', addr, k, h[:80])
        out += b
    return out


def checkpoint():
    """The emulator state 'cpm' (CP/M on the A> prompt); booted and saved when missing. The state lives in the
    emulator's memory and is lost when it ends. ECMON choice 3: CP/M with the IDE disks (choices 0-2 wait for a
    floppy controller that the set V does not have)."""
    mcp.call('pause')
    try:
        mcp.call('load_state', name='cpm')
    except RuntimeError:
        mcp.call('power', state='cycle')
        mcp.call('resume')
        mcp.call('run_until', screen_text='Zadej 0-3', timeout_ms=20000)
        mcp.call('type_text', text='3')
        res = mcp.call('run_until', screen_text='A>', timeout_ms=30000)
        assert res.get('stopped') != 'timeout', 'CP/M did not start'
        mcp.call('pause')
        mcp.call('save_state', name='cpm')
    mcp.call('pause')


class Game:
    def __init__(self, root=REPO):
        self.root = root
        self.sym = symbols(root)

    def start(self, turbo=True):
        """CP/M checkpoint, the game at 0100h and started; CPU 4 MHz (turbo) or 2 MHz."""
        checkpoint()
        mcp.call('cpu_turbo', on=turbo)
        mcp.call('load_binary', address='0100', path=os.path.join(self.root, 'build', 'bombnet.com'))
        mcp.call('set_registers', pc='0100')

    def run_to(self, name, timeout=3000):
        """Run to the address (symbol or number), return the emulator cycles."""
        addr = self.sym[name] if isinstance(name, str) else name
        res = mcp.call('run_until', address='%04X' % addr, timeout_ms=timeout)
        assert res.get('stopped') != 'timeout', ('run_until', name, res)
        return res['cycles']

    def frames(self, n):
        for _ in range(n):
            self.run_to('_flush_screen')


def screenshot(path):
    """PNG of the CGA-1V, saved again with zlib (the emulator's PNG is not compressed)."""
    res = mcp.call('screenshot', display='CGA-1V')
    img = next(c for c in (res if isinstance(res, list) else [res]) if isinstance(c, dict) and c.get('data'))
    data = base64.b64decode(img['data'])
    open(path, 'wb').write(recompress(data))
    return path


def recompress(png):
    """Re-deflate the IDAT data of a PNG (level 9)."""
    out, pos, idat = png[:8], 8, b''
    chunks = []
    while pos < len(png):
        n = int.from_bytes(png[pos:pos + 4], 'big')
        kind = png[pos + 4:pos + 8]
        body = png[pos + 8:pos + 8 + n]
        pos += 12 + n
        if kind == b'IDAT':
            idat += body
        else:
            chunks.append((kind, body))
    raw = zlib.decompress(idat)
    for kind, body in chunks:
        if kind == b'IEND':
            out += chunk(b'IDAT', zlib.compress(raw, 9))
        out += chunk(kind, body)
    return out


def chunk(kind, body):
    return len(body).to_bytes(4, 'big') + kind + body + zlib.crc32(kind + body).to_bytes(4, 'big')
