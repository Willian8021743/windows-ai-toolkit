#!/usr/bin/env python3
"""Example: two buildings, fiber between switches, copper to end devices.
Run:  ./venv/bin/python example_tebstarts.py out.pkt
"""
import sys
from ptlib import Network, router_config

NET, GW = '192.168.10.', '192.168.10.1'
net = Network()

# Hauptgebäude KG: Router + Core
net.add('router', 'Router-HG-KG', 600, 40,
        config=router_config('Router-HG-KG', {'GigabitEthernet0/0': (GW, '255.255.255.0')}))
net.set_ip('Router-HG-KG', 'GigabitEthernet0/0', GW + '/24')
net.add('switch', 'Core-HG-KG', 600, 190)
# Etagen-Switches
for name, x, y in [('SW-HG-EG', 250, 350), ('SW-HG-1OG', 500, 350), ('SW-HG-2OG', 720, 350),
                   ('SW-NG-KG', 1050, 350), ('SW-NG-EG', 950, 510), ('SW-NG-1OG', 1200, 510)]:
    net.add('switch', name, x, y)
# Endgeräte
hosts = [('PC1-EG', 'pc', 11), ('PC2-EG', 'pc', 12), ('PC3-EG', 'pc', 13), ('PC4-EG', 'pc', 14),
         ('PC5-EG', 'pc', 15), ('PC6-EG', 'pc', 16), ('PC7-EG', 'pc', 17), ('PC8-EG', 'pc', 18),
         ('Printer1-EG', 'printer', 21), ('Printer2-EG', 'printer', 22), ('Server-EG', 'server', 10)]
for i, (name, kind, host) in enumerate(hosts):
    net.add(kind, name, 40 + (i % 6) * 115, 540 + (i // 6) * 150, ip=NET + str(host) + '/24', gw=GW)
    net.link(name, 'FastEthernet0', 'SW-HG-EG', 'GigabitEthernet1/0/%d' % (i + 1))
net.add('pc', 'PC1-NG-EG', 880, 680, ip=NET + '31/24', gw=GW)
net.add('printer', 'Printer1-NG-EG', 1020, 680, ip=NET + '32/24', gw=GW)
net.link('PC1-NG-EG', 'FastEthernet0', 'SW-NG-EG', 'GigabitEthernet1/0/1')
net.link('Printer1-NG-EG', 'FastEthernet0', 'SW-NG-EG', 'GigabitEthernet1/0/2')

# Backbone
net.link('Router-HG-KG', 'GigabitEthernet0/0', 'Core-HG-KG', 'GigabitEthernet1/0/1')
net.fiber('Core-HG-KG', 'GigabitEthernet1/1/1', 'SW-HG-EG', 'GigabitEthernet1/1/1')
net.fiber('Core-HG-KG', 'GigabitEthernet1/1/2', 'SW-HG-1OG', 'GigabitEthernet1/1/1')
net.fiber('Core-HG-KG', 'GigabitEthernet1/1/3', 'SW-HG-2OG', 'GigabitEthernet1/1/1')
net.fiber('Core-HG-KG', 'GigabitEthernet1/1/4', 'SW-NG-KG', 'GigabitEthernet1/1/1')
net.fiber('SW-NG-KG', 'GigabitEthernet1/1/2', 'SW-NG-EG', 'GigabitEthernet1/1/1')
net.fiber('SW-NG-KG', 'GigabitEthernet1/1/3', 'SW-NG-1OG', 'GigabitEthernet1/1/1')

net.note(40, 10, 'TEBstarts - Neubau Unternehmungsgebaeude\nNetz 192.168.10.0/24, Gateway 192.168.10.1')
net.note(660, 60, 'Hauptgebaeude KG - Technik:\nRouter + Core-Switch')
for text, x, y in [('HG EG - Technik', 120, 300), ('HG 1.OG - Technik', 420, 300), ('HG 2.OG - Technik', 650, 300),
                   ('Nebengebaeude KG - Technik', 1000, 300), ('NG EG - Technik', 870, 460),
                   ('NG 1.OG - Technik', 1130, 460), ('NG EG - Empfang', 860, 640)]:
    net.note(x, y, text)

net.save(sys.argv[1] if len(sys.argv) > 1 else 'tebstarts.pkt')
