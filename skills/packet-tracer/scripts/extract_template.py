#!/usr/bin/env python3
"""Pull a <DEVICE> block out of any .pkt/.pka to use as a new template.
usage: extract_template.py file.pkt MODEL [out.xml]      e.g. MODEL = 2911, IE-2000, Laptop-PT
       extract_template.py file.pkt --list
"""
import os, re, sys
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ptcrypto import decrypt_pkt

f, want = sys.argv[1], sys.argv[2]
x = decrypt_pkt(open(f, 'rb').read()).decode('utf-8', 'replace')
x = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', x)          # old files may contain control chars
r = ET.fromstring(x)
print('file version', r.find('VERSION').text)
for d in r.find('NETWORK/DEVICES'):
    t = d.find('ENGINE/TYPE')
    if want == '--list':
        print(t.get('model'), t.text, d.find('ENGINE/NAME').text)
    elif t.get('model') == want:
        out = sys.argv[3] if len(sys.argv) > 3 else want + '.xml'
        open(out, 'w').write(ET.tostring(d, encoding='unicode'))
        print('saved', out); break
