#!/usr/bin/env python3
"""Encrypt / decrypt Cisco Packet Tracer .pkt/.pka files (PT 5.x - 8.x format).

Format (ported from mircodz/pka2xml):
  decrypt: reverse-XOR obfuscation -> Twofish-EAX (key 137*16, iv 16*16) -> XOR -> zlib (4-byte BE length prefix)
  encrypt: the reverse.

usage: ptcrypto.py -d in.pkt out.xml
       ptcrypto.py -e in.xml out.pkt
       ptcrypto.py -logs pt_*.log        (PT log files: base64 + Twofish-EAX key 186*16 / iv 190*16)

Requires the `twofish` pip package (see setup.sh - it needs a one-line patch on Python >= 3.12).
"""
import zlib, sys, struct, base64
import twofish

def _xor(a, b): return bytes(x ^ y for x, y in zip(a, b))

def _dbl(b):
    n = int.from_bytes(b, 'big') << 1
    if b[0] & 0x80: n ^= 0x87
    return (n & ((1 << 128) - 1)).to_bytes(16, 'big')

class EAX:
    """Minimal EAX mode (CMAC/OMAC + CTR) on top of a 16-byte block cipher, 16-byte tag appended."""
    def __init__(self, key):
        self.c = twofish.Twofish(key)
        L = self.c.encrypt(bytes(16))
        self.k1 = _dbl(L); self.k2 = _dbl(self.k1)

    def cmac(self, m):
        n = (len(m) + 15) // 16 if m else 1
        blocks = [m[i*16:(i+1)*16] for i in range(n)]
        last = blocks[-1]
        if len(last) == 16 and len(m) > 0:
            last = _xor(last, self.k1)
        else:
            last = _xor(last + b'\x80' + bytes(15 - len(last)), self.k2)
        blocks[-1] = last
        x = bytes(16)
        for b in blocks:
            x = self.c.encrypt(_xor(x, b))
        return x

    def omac(self, t, m): return self.cmac(bytes(15) + bytes([t]) + m)

    def ctr(self, n, m):
        out = bytearray()
        ctr = int.from_bytes(n, 'big')
        for i in range(0, len(m), 16):
            ks = self.c.encrypt(((ctr + i // 16) & ((1 << 128) - 1)).to_bytes(16, 'big'))
            out += _xor(m[i:i+16], ks)
        return bytes(out)

    def encrypt(self, nonce, m, hdr=b''):
        N = self.omac(0, nonce); H = self.omac(1, hdr)
        C = self.ctr(N, m)
        return C + _xor(_xor(N, self.omac(2, C)), H)

    def decrypt(self, nonce, data, hdr=b''):
        C, tag = data[:-16], data[-16:]
        N = self.omac(0, nonce); H = self.omac(1, hdr)
        if _xor(_xor(N, self.omac(2, C)), H) != tag:
            raise ValueError('EAX tag mismatch (not a PT 7/8 file, or different key)')
        return self.ctr(N, C)

KEY = bytes([137] * 16); IV = bytes([16] * 16)

def decrypt_pkt(data: bytes) -> bytes:
    L = len(data)
    s1 = bytes(data[L + ~i] ^ ((L - i * L) & 0xff) for i in range(L))
    s2 = EAX(KEY).decrypt(IV, s1)
    L2 = len(s2)
    s3 = bytes(s2[i] ^ ((L2 - i) & 0xff) for i in range(L2))
    (ulen,) = struct.unpack('>I', s3[:4])
    return zlib.decompress(s3[4:])

def encrypt_pkt(xml: bytes) -> bytes:
    comp = struct.pack('>I', len(xml)) + zlib.compress(xml)
    L1 = len(comp)
    s2 = bytes(comp[i] ^ ((L1 - i) & 0xff) for i in range(L1))
    enc = EAX(KEY).encrypt(IV, s2)
    L = len(enc)
    out = bytearray(L)
    for i in range(L):
        out[L + ~i] = enc[i] ^ ((L - i * L) & 0xff)
    return bytes(out)

def decrypt_log(data: bytes) -> bytes:
    raw = base64.b64decode(data)
    L = len(raw)
    s1 = bytes(raw[L + ~i] ^ ((L - i * L) & 0xff) for i in range(L))
    return EAX(bytes([186] * 16)).decrypt(bytes([190] * 16), s1)

if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '-logs':
        sys.stdout.write(decrypt_log(open(sys.argv[2], 'rb').read()).decode('utf-8', 'replace'))
        sys.exit()
    if len(sys.argv) != 4 or sys.argv[1] not in ('-d', '-e'):
        sys.exit(__doc__)
    mode, inp, outp = sys.argv[1:4]
    d = open(inp, 'rb').read()
    open(outp, 'wb').write(decrypt_pkt(d) if mode == '-d' else encrypt_pkt(d))
