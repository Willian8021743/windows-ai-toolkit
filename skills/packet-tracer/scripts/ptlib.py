#!/usr/bin/env python3
"""Build Cisco Packet Tracer .pkt files from Python (tested with PT 8.2.2 on Linux).

    from ptlib import Network
    net = Network()
    net.add('router', 'R1', 400, 40, config=router_config('R1', {'GigabitEthernet0/0': ('10.0.0.1', '255.255.255.0')}))
    net.add('switch', 'SW1', 400, 200)                       # 3650-24PS (has 4 SFP slots -> fiber)
    net.add('pc', 'PC1', 300, 360, ip='10.0.0.10/24', gw='10.0.0.1')
    net.link('R1', 'GigabitEthernet0/0', 'SW1', 'GigabitEthernet1/0/1')   # copper, straight/cross chosen automatically
    net.link('PC1', 'FastEthernet0', 'SW1', 'GigabitEthernet1/0/2')
    net.fiber('SW1', 'GigabitEthernet1/1/1', 'SW2', 'GigabitEthernet1/1/1')  # inserts GLC-LH-SMD SFPs
    net.note(20, 20, 'Label text')
    net.save('out.pkt')                                       # also writes out.pkt.xml for inspection

Device kinds (templates/*.xml):
  router  -> 1941      (GigabitEthernet0/0, 0/1)
  switch  -> 3650-24PS (GigabitEthernet1/0/1-24 copper, 1/1/1-4 SFP)  [use for anything needing fiber]
  switch2960 -> 2960-24TT (FastEthernet0/1-24, GigabitEthernet0/1-2, copper only)
  switch3560 -> 3560-24PS (FastEthernet0/1-24, GigabitEthernet0/1-2, copper only, L3)
  pc / server / printer -> PC-PT / Server-PT / Printer-PT (port FastEthernet0)
"""
import copy, os, random, re, sys, uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ptcrypto import encrypt_pkt

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.join(HERE, '..', 'templates')
KINDS = {
    'router': ('router-1941.xml', 'rack'),
    'switch': ('switch-3650-24PS.xml', 'rack'),
    'switch2960': ('switch-2960-24TT.xml', 'rack'),
    'switch3560': ('switch-3560-24PS.xml', 'rack'),
    'pc': ('pc-PT.xml', 'office'),
    'server': ('server-PT.xml', 'rack'),
    'printer': ('pc-PT.xml', 'office'),      # derived from the PC template, see _to_printer
}
SWITCH_KINDS = {'switch', 'switch2960', 'switch3560'}


def _set(el, path, text):
    e = el.find(path)
    if e is not None:
        e.text = text
    return e


def _eui64(mac):
    b = bytes.fromhex(mac.replace('.', ''))
    b = bytes([b[0] ^ 2]) + b[1:3] + b'\xff\xfe' + b[3:]
    return 'FE80::' + ':'.join('%X' % int.from_bytes(b[i:i+2], 'big') for i in range(0, 8, 2))


def router_config(hostname, interfaces=None, extra=()):
    """Minimal IOS 15 running-config for the 1941. interfaces = {'GigabitEthernet0/0': (ip, mask)}."""
    lines = ['!', 'version 15.1', 'no service timestamps log datetime msec',
             'no service timestamps debug datetime msec', 'no service password-encryption', '!',
             'hostname ' + hostname, '!', 'ip cef', 'no ipv6 cef', '!']
    for name in ('GigabitEthernet0/0', 'GigabitEthernet0/1'):
        lines.append('interface ' + name)
        if interfaces and name in interfaces:
            ip, mask = interfaces[name]
            lines += [' ip address %s %s' % (ip, mask), ' duplex auto', ' speed auto']
        else:
            lines += [' no ip address', ' duplex auto', ' speed auto', ' shutdown']
        lines.append('!')
    lines += ['interface Vlan1', ' no ip address', ' shutdown', '!', 'ip classless', '!',
              'ip flow-export version 9', '!', *extra,
              'line con 0', '!', 'line aux 0', '!', 'line vty 0 4', ' login', '!', 'end']
    return lines


class Network:
    def __init__(self, base=os.path.join(TEMPLATES, 'base.xml'), seed=42):
        random.seed(seed)
        self.root = ET.parse(base).getroot()
        self.tpl = {}
        self.devices, self.links, self.ref, self.dev, self.kind = [], [], {}, {}, {}
        self._mac = 0x100
        phys = self.root.find('PHYSICALWORKSPACE/NODE')
        self.rack, self.rack_path = self._find_node(phys, 'Rack')
        self.office, self.office_path = self._find_node(phys, 'Corporate Office')
        self.node_tpl = self._node_template()
        self.phys_x = {'rack': 0, 'office': 0}
        self.notes = self.root.find('PHYSICALWORKSPACE/NOTES')

    # ------------------------------------------------------------ internals
    def _find_node(self, node, name, path=()):
        path = path + (node.find('UUID_STR').text,)
        if node.find('NAME').text == name:
            return node, path
        for c in node.find('CHILDREN'):
            r = self._find_node(c, name, path)
            if r:
                return r
        return None

    def _node_template(self):
        n = ET.Element('NODE')
        for tag, val in [('X', '0'), ('Y', '0'), ('TYPE', '6'), ('NAME', 'dev'), ('SX', '0.2'), ('SY', '0.2'),
                         ('W', '20'), ('H', '20'), ('D', '0')]:
            ET.SubElement(n, tag).text = val
        p = ET.SubElement(n, 'PATH', isanim='false'); p.text = '../art/Background/grid_100x100.png'
        ET.SubElement(n, 'CHILDREN')
        for tag, val in [('MANUAL_SCALING', 'false'), ('SCALED_PIXMAP_WIDTH', '0'), ('SCALED_PIXMAP_HEIGHT', '0'),
                         ('INIT_WIDTH', '20'), ('INIT_HEIGHT', '20'), ('INIT_DEPTH', '0'), ('INIT_SX', '0.2'),
                         ('INIT_SY', '0.2'), ('INIT_SZ', '0.2'), ('BG_TILED', 'false'), ('CUSTOM_IMAGE_WIDTH', '-1'),
                         ('CUSTOM_IMAGE_HEIGHT', '-1'), ('SCALE_FACTOR', '1'), ('UUID_STR', ''), ('SLOT', '0'),
                         ('SUB_SLOT', '0')]:
            ET.SubElement(n, tag).text = val
        n.find('NAME').set('translate', 'true')
        return n

    def _template(self, kind):
        if kind not in self.tpl:
            self.tpl[kind] = ET.parse(os.path.join(TEMPLATES, KINDS[kind][0])).getroot()
        return copy.deepcopy(self.tpl[kind])

    def _new_mac(self, oui):
        self._mac += 1
        return '%02X%02X.%02X%02X.%02X%02X' % tuple(oui + self._mac.to_bytes(3, 'big'))

    def _ports(self, dev):
        return [p for p in dev.find('ENGINE').iter('PORT') if p.find('MACADDRESS') is not None]

    def port(self, name, portname):
        """Find the PORT element of device `name` by IOS interface name (or 'FastEthernet0' on end devices)."""
        dev = self.dev[name]
        ports = self._ports(dev)
        rc = dev.find('ENGINE/RUNNINGCONFIG')
        if rc is None:
            return ports[0]
        names = [l.text.split()[1] for l in rc.findall('LINE')
                 if l.text and l.text.startswith('interface ') and not l.text.startswith('interface Vlan')]
        assert len(names) == len(ports), 'port/interface count mismatch on %s' % name
        return ports[names.index(portname)]

    def _to_printer(self, d):
        eng = d.find('ENGINE')
        t = eng.find('TYPE'); t.text = 'Printer'; t.set('model', 'Printer-PT')
        mod = eng.find('MODULE')
        for slot in mod.findall('SLOT'):          # drop the audio-jack slot
            if slot.find('TYPE').text != 'ePtHostModule':
                mod.remove(slot)
        for tag in ('BLUETOOTH_PORT', 'BLUETOOTH_MANAGER'):
            e = eng.find(tag)
            if e is not None:
                eng.remove(e)
        _set(eng, 'USB_PORT_COUNT', '0')
        _set(eng, 'EXT_ATTRIBUTES', 'MTBF:17520;cost:1500;power source:0;rack units:3;wattage:30;')

    # ------------------------------------------------------------ public API
    def add(self, kind, name, x, y, ip=None, gw=None, config=None, place=None):
        """Add a device. ip='a.b.c.d/24' (end devices), config=list of IOS lines (replaces running-config)."""
        d = self._template(kind)
        eng = d.find('ENGINE')
        _set(eng, 'NAME', name)
        _set(eng, 'SYS_NAME', name)
        _set(eng, 'POWER', 'true')
        _set(eng, 'SERIALNUMBER', 'PTX%08X' % random.getrandbits(32))
        ref = 'save-ref-id:%d' % random.getrandbits(62)
        if eng.find('SAVE_REF_ID') is None:
            ET.SubElement(eng, 'SAVE_REF_ID')
        _set(eng, 'SAVE_REF_ID', ref)

        for p in self._ports(d):
            m = p.find('MACADDRESS')
            mac = self._new_mac(bytes.fromhex(m.text.replace('.', ''))[:3])
            m.text = mac
            _set(p, 'BIA', mac)
            for tag in ('IPV6_LINK_LOCAL', 'IPV6_DEFAULT_LINK_LOCAL'):
                e = p.find(tag)
                if e is not None and e.text:
                    e.text = _eui64(mac)
            if p.find('UP_METHOD') is None:
                ET.SubElement(p, 'UP_METHOD').text = '5'
        bia = eng.find('BUILD_IN_ADDR')
        if bia is not None and bia.text:
            bia.text = self._new_mac(bytes.fromhex(bia.text.replace('.', ''))[:3])

        rc = eng.find('RUNNINGCONFIG')
        if rc is not None:
            if config is not None:
                for l in list(rc):
                    rc.remove(l)
                for line in config:
                    ET.SubElement(rc, 'LINE').text = line
            else:
                for l in rc.findall('LINE'):
                    if l.text and l.text.startswith('hostname '):
                        l.text = 'hostname ' + name

        if kind == 'printer':
            self._to_printer(d)

        # workspace + physical placement (always the 8.2-style WORKSPACE block of the PC template)
        d.remove(d.find('WORKSPACE'))
        ws = copy.deepcopy(self._template('pc').find('WORKSPACE')); d.append(ws)
        _set(ws, 'LOGICAL/X', str(x)); _set(ws, 'LOGICAL/Y', str(y))
        _set(ws, 'LOGICAL/MEM_ADDR', '0'); _set(ws, 'LOGICAL/DEV_ADDR', '0')
        place = place or KINDS[kind][1]
        cont, path = (self.rack, self.rack_path) if place == 'rack' else (self.office, self.office_path)
        dev_uuid = '{%s}' % uuid.uuid4()
        _set(ws, 'PHYSICAL', ','.join(path + (dev_uuid,)))
        cp = ws.find('PHYSICAL_CPUR')
        px = self.phys_x[place]; self.phys_x[place] += 30 if place == 'rack' else 60
        _set(cp, 'X', str(px)); _set(cp, 'Y', '0')
        _set(cp, 'PARENT_PATH', ','.join(path[:-1])); _set(cp, 'CONTAINER_ID', path[-1])
        n = copy.deepcopy(self.node_tpl)
        _set(n, 'NAME', name); _set(n, 'UUID_STR', dev_uuid); _set(n, 'X', str(px))
        cont.find('CHILDREN').append(n)

        self.devices.append(d); self.ref[name] = ref; self.dev[name] = d; self.kind[name] = kind
        if ip:
            self.set_ip(name, None, ip, gw)
        return d

    def set_ip(self, name, portname, ip, gw=None):
        """Static IPv4 on a port. ip='a.b.c.d/nn' or 'a.b.c.d' (then mask 255.255.255.0)."""
        addr, _, bits = ip.partition('/')
        mask = '.'.join(str((0xffffffff << (32 - int(bits or 24)) >> i) & 0xff) for i in (24, 16, 8, 0))
        p = self.port(name, portname) if portname else self._ports(self.dev[name])[0]
        _set(p, 'IP', addr); _set(p, 'SUBNET', mask); _set(p, 'POWER', 'true')
        _set(p, 'PORT_DHCP_ENABLE', 'false')
        if gw:
            _set(p, 'PORT_GATEWAY', gw)
            _set(self.dev[name].find('ENGINE'), 'GATEWAY', gw)

    def _make_fiber_port(self, name, portname):
        """3650 only: SFP slot N behind GigabitEthernet1/1/N gets a GLC-LH-SMD, port becomes fiber."""
        p = self.port(name, portname)
        p.find('TYPE').text = 'eFiberGigabitEthernet'
        n = int(portname.rsplit('/', 1)[1])
        slots = [s for s in self.dev[name].find('ENGINE').iter('SLOT') if s.find('TYPE').text == 'eSfpModule']
        if not slots:
            raise ValueError('%s has no SFP slots - only the 3650-24PS ("switch") can take fiber' % name)
        slot = slots[n - 1]
        if slot.find('MODULE') is None:
            m = ET.SubElement(slot, 'MODULE')
            ET.SubElement(m, 'TYPE').text = 'eSfpModule'
            ET.SubElement(m, 'MODEL').text = 'GLC-LH-SMD'

    def link(self, a, pa, b, pb, media='eCopper', cable=None):
        """Cable between two ports. media: eCopper | eFiber | eSerial. Copper sub-type auto: same class -> crossover."""
        if media == 'eFiber':
            self._make_fiber_port(a, pa); self._make_fiber_port(b, pb)
        if cable is None:
            same = (self.kind[a] in SWITCH_KINDS) == (self.kind[b] in SWITCH_KINDS)
            cable = 'eCrossOver' if same else 'eStraightThrough'
        l = ET.Element('LINK')
        ET.SubElement(l, 'TYPE').text = media
        c = ET.SubElement(l, 'CABLE')
        for tag, val in [('LENGTH', '1'), ('FUNCTIONAL', 'true'), ('FROM', self.ref[a]), ('PORT', pa),
                         ('TO', self.ref[b]), ('PORT', pb), ('FROM_DEVICE_MEM_ADDR', '0'),
                         ('TO_DEVICE_MEM_ADDR', '0'), ('FROM_PORT_MEM_ADDR', '0'), ('TO_PORT_MEM_ADDR', '0'),
                         ('GEO_VIEW_COLOR', '#000000'), ('IS_MANAGED_IN_RACK_VIEW', 'false')]:
            ET.SubElement(c, tag).text = val
        if media == 'eCopper':
            ET.SubElement(c, 'TYPE').text = cable     # only copper has a sub-type; fiber/serial: none
        self.links.append(l)

    def fiber(self, a, pa, b, pb):
        self.link(a, pa, b, pb, media='eFiber')

    def note(self, x, y, text):
        n = ET.SubElement(self.notes, 'NOTE', uuid='{%s}' % uuid.uuid4())
        ET.SubElement(n, 'X').text = str(x); ET.SubElement(n, 'Y').text = str(y)
        ET.SubElement(n, 'Z').text = '40000'
        ET.SubElement(n, 'TEXT', translate='true').text = text
        ET.SubElement(n, 'NOTECLUSTERID').text = '1-1'
        ET.SubElement(n, 'MEM_ADDR').text = '0'

    def to_xml(self):
        devs = self.root.find('NETWORK/DEVICES'); devs.clear()
        for d in self.devices:
            devs.append(d)
        lk = self.root.find('NETWORK/LINKS'); lk.clear()
        for l in self.links:
            lk.append(l)
        return ET.tostring(self.root, encoding='unicode')

    def save(self, path, keep_xml=True):
        xml = self.to_xml()
        if keep_xml:
            open(path + '.xml', 'w').write(xml)
        open(path, 'wb').write(encrypt_pkt(xml.encode('utf-8')))
        print('wrote %s (%d devices, %d links)' % (path, len(self.devices), len(self.links)))
        return path
