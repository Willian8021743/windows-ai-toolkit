import sys, time
from Xlib import X, display
from Xlib.ext import xtest
d = display.Display(':0')
def move(x, y): d.screen().root.warp_pointer(x, y); d.sync()
def click(x, y, btn=1, n=1):
    move(x, y); time.sleep(0.15)
    for _ in range(n):
        xtest.fake_input(d, X.ButtonPress, btn); d.sync(); time.sleep(0.08)
        xtest.fake_input(d, X.ButtonRelease, btn); d.sync(); time.sleep(0.12)
def key(keysym_name, mods=()):
    from Xlib import XK
    codes = [d.keysym_to_keycode(XK.string_to_keysym(m)) for m in mods]
    kc = d.keysym_to_keycode(XK.string_to_keysym(keysym_name))
    for c in codes: xtest.fake_input(d, X.KeyPress, c)
    xtest.fake_input(d, X.KeyPress, kc); d.sync(); time.sleep(0.05)
    xtest.fake_input(d, X.KeyRelease, kc)
    for c in reversed(codes): xtest.fake_input(d, X.KeyRelease, c)
    d.sync(); time.sleep(0.08)
def type_text(s):
    for ch in s:
        name = {'/': 'slash', '.': 'period', '-': 'minus', '_': 'underscore', ' ': 'space', ':': 'colon'}.get(ch, ch)
        mods = ('Shift_L',) if ch.isupper() or ch in ':_' else ()
        key(name, mods)
def drag(x1, y1, x2, y2):
    move(x1, y1); time.sleep(0.2)
    xtest.fake_input(d, X.ButtonPress, 1); d.sync(); time.sleep(0.3)
    steps = 25
    for i in range(1, steps + 1):
        move(int(x1 + (x2 - x1) * i / steps), int(y1 + (y2 - y1) * i / steps)); time.sleep(0.03)
    time.sleep(0.3)
    xtest.fake_input(d, X.ButtonRelease, 1); d.sync(); time.sleep(0.3)
args = sys.argv[1:]
i = 0
while i < len(args):
    a = args[i]
    if a == 'click': click(int(args[i+1]), int(args[i+2])); i += 3
    elif a == 'drag': drag(*map(int, args[i+1:i+5])); i += 5
    elif a == 'move': move(int(args[i+1]), int(args[i+2])); i += 3
    elif a == 'key': key(args[i+1]); i += 2
    elif a == 'ctrl': key(args[i+1], ('Control_L',)); i += 2
    elif a == 'type': type_text(args[i+1]); i += 2
    elif a == 'sleep': time.sleep(float(args[i+1])); i += 2
    else: raise SystemExit('bad arg ' + a)
