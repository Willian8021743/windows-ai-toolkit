#!/usr/bin/env python3
"""
Mermaid → VSDX 转换器 v2
基于用户手工参考文件"示例1111.vsdx"设计
核心思路：利用 Visio 原生粘附机制，不写死 Geometry 路径
"""

import re
import sys
import zipfile
import os

MASTER_PROCESS = 5
MASTER_DECISION = 4
MASTER_STARTEND = 2
MASTER_CONNECTOR = 6

SHAPE_W = 1.0
SHAPE_H = 0.6
LAYER_GAP = 1.0
LEFT_COL_X = 1.6
RIGHT_COL_X = 5.0
START_TOP_Y = 6.7
# 参考文件路径 — 相对于脚本位置的 templates/ 目录
import pathlib, os
_SCRIPT_DIR = pathlib.Path(os.path.realpath(__file__) if '__file__' in dir() else os.path.abspath(sys.argv[0])).resolve().parent.parent
REFERENCE_VSDX = str(_SCRIPT_DIR / 'templates' / 'reference.vsdx')


def parse_mermaid(text):
    """Parse Mermaid flowchart text. Returns (nodes_dict, edges_list)."""
    nodes = {}
    edges = []
    nid_map = {}
    next_id = 1

    # Expand semicolons into separate lines
    raw_lines = text.strip().split('\n')
    lines = []
    for line in raw_lines:
        for part in line.split(';'):
            stripped = part.strip()
            if stripped:
                lines.append(stripped)

    # Pass 1: extract all node declarations from ANY line pattern
    # Patterns: A[text], A{text}, A([text]) — anywhere in the line
    node_decls = {}  # key -> (label, type)
    for line in lines:
        line = line.strip()
        if line.startswith('%%') or line.startswith('graph ') or line.startswith('flowchart '):
            continue
        # Find ALL node declarations in this line
        # Pattern: word followed by [text] or {text} or ([text])
        for m in re.finditer(r'(\w+)\s*\(\[([^\]]+)\]\)', line):
            node_decls[m.group(1)] = (m.group(2), 'startend')
        for m in re.finditer(r'(\w+)\s*\[([^\]]+)\]', line):
            if m.group(1) not in node_decls:
                node_decls[m.group(1)] = (m.group(2), 'process')
        for m in re.finditer(r'(\w+)\s*\{([^}]+)\}', line):
            if m.group(1) not in node_decls:
                node_decls[m.group(1)] = (m.group(2), 'decision')

    # Also detect bare node references used as arrow targets
    for line in lines:
        line = line.strip()
        if line.startswith('%%') or line.startswith('graph ') or line.startswith('flowchart '):
            continue
        for m in re.finditer(r'--+>?\s*(?:\|([^|]*)\|)?\s*--*>?\s*(\w+)', line):
            tk = m.group(2)
            if tk not in node_decls:
                node_decls[tk] = (tk, 'process')
        for m in re.finditer(r'--+>?\s*(\w+)', line):
            tk = m.group(1)
            if tk not in node_decls:
                node_decls[tk] = (tk, 'process')

    # Assign IDs
    for key, (label, ntype) in node_decls.items():
        nodes[next_id] = {'id': next_id, 'key': key, 'label': label, 'type': ntype}
        nid_map[key] = next_id
        next_id += 1

    # Pass 2: parse edges
    for line in lines:
        line = line.strip()
        if line.startswith('%%') or line.startswith('graph ') or line.startswith('flowchart '):
            continue
        # Try to extract source node key
        src_m = re.match(r'(\w+)', line)
        if not src_m:
            continue
        sk = src_m.group(1)
        if sk not in nid_map:
            continue
        src_key = sk
        # Find arrow patterns — both labeled and unlabeled
        # Strategy: find all occurrences of --> or -> then parse what follows
        pos = 0
        while pos < len(line):
            # Search for arrow in the remaining substring
            remainder = line[pos:]
            arrow_m = re.search(r'-{2,}>?\s*', remainder)
            if not arrow_m:
                break
            arrow_end = arrow_m.end()  # relative to remainder
            after_arrow = remainder[arrow_end:]
            # Check for label: |label|
            label = ''
            label_m = re.match(r'\s*\|\s*([^|]*?)\s*\|\s*', after_arrow)
            tk_pos = 0
            if label_m:
                label = label_m.group(1)
                tk_pos = label_m.end()
            else:
                tk_pos = 0  # No label, start looking for target right after arrow
            # Find target word (skip optional second arrow)
            after_label = after_arrow[tk_pos:]
            # Skip optional second arrow
            second_arrow = re.match(r'-{2,}>?\s*', after_label)
            if second_arrow:
                after_label = after_label[second_arrow.end():]
            target_m = re.match(r'\s*(\w+)', after_label)
            if target_m:
                tk = target_m.group(1)
                if tk in nid_map:
                    # Check not duplicate
                    if not any(e['src'] == nid_map[src_key] and e['tgt'] == nid_map[tk] for e in edges):
                        edges.append({'src': nid_map[src_key], 'tgt': nid_map[tk], 'label': label})
            pos += arrow_m.start() + 1  # Advance past arrow start

    return nodes, edges


def build_flow_levels(nodes, edges):
    from collections import deque

    in_deg = {nid: 0 for nid in nodes}
    adj = {nid: [] for nid in nodes}
    for e in edges:
        s, t = e['src'], e['tgt']
        if t in in_deg:
            in_deg[t] += 1
        if s in adj:
            adj[s].append(t)

    # Kahn's algorithm — respects DAG, handles cycles gracefully
    level = {}
    q = deque()
    for nid, d in in_deg.items():
        if d == 0:
            level[nid] = 0
            q.append(nid)

    processed = 0
    while q:
        cur = q.popleft()
        processed += 1
        for nxt in adj[cur]:
            in_deg[nxt] -= 1
            nl = level[cur] + 1
            if nxt not in level or nl > level[nxt]:
                level[nxt] = nl
            if in_deg[nxt] == 0:
                q.append(nxt)

    # Handle cycle nodes (never got in_deg==0)
    max_lv = max(level.values()) if level else 0
    for nid in nodes:
        if nid not in level:
            max_lv += 1
            level[nid] = max_lv

    return level


def assign_columns(nodes, edges, level):
    col = {nid: 'L' for nid in nodes}

    # First pass: decision branches
    for e in edges:
        src = e['src']
        if nodes[src]['type'] != 'decision':
            continue
        label = e.get('label', '')
        positive = any(k in label for k in ['充足', '匹配', '通过', '同意', '是', '一致', '常规', '正常', '成功'])
        col[e['tgt']] = 'R' if positive else 'L'

    # Second pass: propagate columns through non-decision chains
    changed = True
    while changed:
        changed = False
        for e in edges:
            src, tgt = e['src'], e['tgt']
            if nodes[src]['type'] in ('process', 'startend') and col[src] != col[tgt]:
                col[tgt] = col[src]
                changed = True

    return col


def make_shape_xml(nid, node, px, py):
    nt = node['type']
    label = node['label']

    if nt == 'process':
        master = MASTER_PROCESS
        lw, lc, fc = '0.003472222222222222', '#c8c8c8', '#4d4d4d'
    elif nt == 'decision':
        master = MASTER_DECISION
        lw, lc, fc = '0.01041666666666667', '#31528f', '#4d4d4d'
    else:
        master = MASTER_STARTEND
        lw, lc, fc = '0.01041666666666667', '#31528f', '#4d4d4d'

    return f'''<Shape ID="{nid}" NameU="{nt.title()}" Name="{label}" Type="Shape" Master="{master}">
        <Cell N="PinX" V="{px:.6f}"/>
        <Cell N="PinY" V="{py:.6f}"/>
        <Cell N="LayerMember" V="0"/>
        <Cell N="LineWeight" V="{lw}" U="PT" F="Inh"/>
        <Cell N="LineColor" V="{lc}" F="Inh"/>
        <Cell N="FillBkgnd" V="{fc}" F="Inh"/>
        <Section N="Character">
          <Row IX="0">
            <Cell N="Color" V="#feffff" F="Inh"/>
          </Row>
        </Section>
        <Text>{label}</Text>
      </Shape>'''


def make_connector_xml(e, src_pos, tgt_pos, src_col, tgt_col, my_id):
    spx, spy = src_pos
    tpx, tpy = tgt_pos
    label = e.get('label', '')
    dx = tpx - spx
    dy = tpy - spy
    has_label = bool(label)
    src = e['src']
    tgt = e['tgt']

    cells = []
    cells.append(f'<Cell N="BegTrigger" V="2" F="_XFTRIGGER(Sheet.{src}!EventXFMod)"/>')
    cells.append(f'<Cell N="EndTrigger" V="2" F="_XFTRIGGER(Sheet.{tgt}!EventXFMod)"/>')
    cells.append('<Cell N="LayerMember" V="1"/>')
    cells.append('<Cell N="LineWeight" V="0.01388888888888889" U="PT" F="Inh"/>')
    cells.append('<Cell N="LineColor" V="#4672c4" F="Inh"/>')
    cells.append('<Cell N="EndArrow" V="4" F="Inh"/>')

    is_vertical = abs(dx) < 0.5
    is_horizontal = abs(dy) < 0.5
    control = ''

    connects = []

    if is_vertical:
        # Pure vertical (same column, different row)
        bx, by = spx, spy - SHAPE_H/2
        ex, ey = tpx, tpy + SHAPE_H/2
        w = 0.1968503937007874
        h = ey - by  # preserve sign (negative = downward in Visio)
        if abs(h) < 0.01:
            h = -0.1 if ey < by else 0.1

        cells.append(f'<Cell N="BeginX" V="{bx:.6f}" F="PAR(PNT(Sheet.{src}!Connections.X3,Sheet.{src}!Connections.Y3))"/>')
        cells.append(f'<Cell N="BeginY" V="{by:.6f}" F="PAR(PNT(Sheet.{src}!Connections.X3,Sheet.{src}!Connections.Y3))"/>')
        cells.append(f'<Cell N="EndX" V="{ex:.6f}" F="_WALKGLUE(EndTrigger,BegTrigger,WalkPreference)"/>')
        cells.append(f'<Cell N="EndY" V="{ey:.6f}" F="_WALKGLUE(EndTrigger,BegTrigger,WalkPreference)"/>')
        cells.append(f'<Cell N="Width" V="{w:.6f}" F="GUARD(0.19685039370079DL)"/>')
        cells.append(f'<Cell N="Height" V="{h:.6f}" F="GUARD(EndY-BeginY)"/>')
        cells.append(f'<Cell N="LocPinX" V="{w/2:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="LocPinY" V="{h/2:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="PinX" V="{bx:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="PinY" V="{by + h/2:.6f}" F="Inh"/>')
        cells.append('<Cell N="ConFixedCode" V="5"/>')

        geom = f'''<Section N="Geometry" IX="0">
        <Row T="MoveTo" IX="1"><Cell N="X" V="0.09842519685039353"/></Row>
        <Row T="LineTo" IX="2"><Cell N="X" V="0.09842519685039353"/><Cell N="Y" V="{h:.6f}"/></Row>
        <Row T="LineTo" IX="3" Del="1"/>
      </Section>'''

        connects.append(f'<Connect FromSheet="{my_id}" FromCell="BeginX" FromPart="9" ToSheet="{src}" ToCell="PinX" ToPart="3"/>')
        connects.append(f'<Connect FromSheet="{my_id}" FromCell="EndX" FromPart="12" ToSheet="{tgt}" ToCell="PinX" ToPart="3"/>')

    elif is_horizontal:
        # Pure horizontal (same row, different column)
        bx, by = spx + SHAPE_W/2, spy
        ex, ey = tpx - SHAPE_W/2, tpy
        w = ex - bx if ex > bx else 0.1

        cells.append(f'<Cell N="BeginX" V="{bx:.6f}" F="PAR(PNT(Sheet.{src}!Connections.X2,Sheet.{src}!Connections.Y2))"/>')
        cells.append(f'<Cell N="BeginY" V="{by:.6f}" F="PAR(PNT(Sheet.{src}!Connections.X2,Sheet.{src}!Connections.Y2))"/>')
        cells.append(f'<Cell N="EndX" V="{ex:.6f}" F="PAR(PNT(Sheet.{tgt}!Connections.X1,Sheet.{tgt}!Connections.Y1))"/>')
        cells.append(f'<Cell N="EndY" V="{ey:.6f}" F="PAR(PNT(Sheet.{tgt}!Connections.X1,Sheet.{tgt}!Connections.Y1))"/>')
        cells.append(f'<Cell N="Width" V="{w:.6f}" F="GUARD(EndX-BeginX)"/>')
        cells.append(f'<Cell N="Height" V="0.1968503937007874" F="GUARD(0.19685039370079DL)"/>')
        cells.append(f'<Cell N="LocPinX" V="{w/2:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="LocPinY" V="0.09842519685039369" F="Inh"/>')
        cells.append(f'<Cell N="PinX" V="{bx + w/2:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="PinY" V="{by:.6f}" F="Inh"/>')

        mid_y = 0.09842519685039353
        geom = f'''<Section N="Geometry" IX="0">
        <Row T="MoveTo" IX="1"><Cell N="Y" V="{mid_y}"/></Row>
        <Row T="LineTo" IX="2"><Cell N="X" V="{w:.6f}"/><Cell N="Y" V="{mid_y}"/></Row>
        <Row T="LineTo" IX="3" Del="1"/>
      </Section>'''

        connects.append(f'<Connect FromSheet="{my_id}" FromCell="BeginX" FromPart="9" ToSheet="{src}" ToCell="PinX" ToPart="3"/>')
        connects.append(f'<Connect FromSheet="{my_id}" FromCell="EndX" FromPart="12" ToSheet="{tgt}" ToCell="PinX" ToPart="3"/>')

    else:
        # L-shape (branch from decision to far side)
        cells.append(f'<Cell N="BeginX" V="{spx:.6f}" F="_WALKGLUE(BegTrigger,EndTrigger,WalkPreference)"/>')
        cells.append(f'<Cell N="BeginY" V="{spy:.6f}" F="_WALKGLUE(BegTrigger,EndTrigger,WalkPreference)"/>')

        if tgt_col == 'R':
            cells.append(f'<Cell N="EndX" V="{tpx - SHAPE_W/2:.6f}" F="PAR(PNT(Sheet.{tgt}!Connections.X1,Sheet.{tgt}!Connections.Y1))"/>')
            cells.append(f'<Cell N="EndY" V="{tpy:.6f}" F="PAR(PNT(Sheet.{tgt}!Connections.X1,Sheet.{tgt}!Connections.Y1))"/>')
            w = tpx - SHAPE_W/2 - spx
            h = tpy - spy
        else:
            cells.append(f'<Cell N="EndX" V="{tpx + SHAPE_W/2:.6f}" F="PAR(PNT(Sheet.{tgt}!Connections.X2,Sheet.{tgt}!Connections.Y2))"/>')
            cells.append(f'<Cell N="EndY" V="{tpy:.6f}" F="PAR(PNT(Sheet.{tgt}!Connections.X2,Sheet.{tgt}!Connections.Y2))"/>')
            w = tpx + SHAPE_W/2 - spx
            h = tpy - spy

        if abs(w) < 0.01:
            w = 0.5 if dx >= 0 else -0.5
        if abs(h) < 0.01:
            h = -0.5 if dy < 0 else 0.5

        cells.append(f'<Cell N="Width" V="{w:.6f}" F="GUARD(EndX-BeginX)"/>')
        cells.append(f'<Cell N="Height" V="{h:.6f}" F="GUARD(EndY-BeginY)"/>')
        cells.append(f'<Cell N="LocPinX" V="{w/2:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="LocPinY" V="{h/2:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="PinX" V="{spx + w/2:.6f}" F="Inh"/>')
        cells.append(f'<Cell N="PinY" V="{spy + h/2:.6f}" F="Inh"/>')

        geom = f'''<Section N="Geometry" IX="0">
        <Row T="LineTo" IX="2"><Cell N="X" V="{w:.6f}"/><Cell N="Y" V="0"/></Row>
        <Row T="LineTo" IX="3"><Cell N="X" V="{w:.6f}"/><Cell N="Y" V="{h:.6f}"/></Row>
      </Section>'''

        control = ''
        if has_label:
            txt_pin_x = w * 0.85 if w > 0 else w * 0.85
            txt_pin_y = 0.0
            txt_w = min(abs(w) * 0.7, 1.2)
            txt_h = 0.2590782864040798

            cells.append(f'<Cell N="TxtPinX" V="{txt_pin_x:.6f}" F="Inh"/>')
            cells.append(f'<Cell N="TxtPinY" V="{txt_pin_y:.6f}" F="Inh"/>')
            cells.append(f'<Cell N="TxtWidth" V="{txt_w:.6f}" F="Inh"/>')
            cells.append(f'<Cell N="TxtHeight" V="{txt_h:.6f}" F="Inh"/>')
            cells.append(f'<Cell N="TxtLocPinX" V="{txt_w/2:.6f}" F="Inh"/>')
            cells.append(f'<Cell N="TxtLocPinY" V="{txt_h/2:.6f}" F="Inh"/>')

            control = f'''<Section N="Control">
        <Row N="TextPosition">
          <Cell N="X" V="{txt_pin_x:.6f}"/>
          <Cell N="Y" V="{txt_pin_y:.6f}"/>
          <Cell N="XDyn" V="{txt_pin_x:.6f}" F="Inh"/>
          <Cell N="YDyn" V="{txt_pin_y:.6f}" F="Inh"/>
          <Cell N="XCon" V="0" F="Inh"/>
        </Row>
      </Section>'''

        if tgt_col == 'R':
            connects.append(f'<Connect FromSheet="{my_id}" FromCell="BeginX" FromPart="9" ToSheet="{src}" ToCell="PinX" ToPart="3"/>')
            connects.append(f'<Connect FromSheet="{my_id}" FromCell="EndX" FromPart="12" ToSheet="{tgt}" ToCell="PinX" ToPart="3"/>')
        else:
            connects.append(f'<Connect FromSheet="{my_id}" FromCell="BeginX" FromPart="9" ToSheet="{src}" ToCell="PinX" ToPart="3"/>')
            connects.append(f'<Connect FromSheet="{my_id}" FromCell="EndX" FromPart="12" ToSheet="{tgt}" ToCell="PinX" ToPart="3"/>')

    cells_str = '\n        '.join(cells)
    return f'''<Shape ID="{my_id}" Type="Shape" Master="{MASTER_CONNECTOR}">
        {cells_str}
        {geom}
        {control if has_label else ''}
        {f'<Text>{label}</Text>' if has_label else ''}
      </Shape>''', connects


def build_vsdx(nodes, edges, level, column, output_path):
    with zipfile.ZipFile(REFERENCE_VSDX, 'r') as z:
        ref = {n: z.read(n) for n in z.namelist()}

    out = {}
    for name, data in ref.items():
        if 'pages/page1.xml' in name:
            continue
        out[name] = data

    positions = {}
    for nid, node in nodes.items():
        col = column.get(nid, 'L')
        lv = level.get(nid, 0)
        if node['type'] == 'decision':
            # Decision nodes centered between columns
            px = (LEFT_COL_X + RIGHT_COL_X) / 2
        else:
            px = RIGHT_COL_X if col == 'R' else LEFT_COL_X
        py = START_TOP_Y - lv * LAYER_GAP
        positions[nid] = (px, py)

    # page1.xml.rels — ensure page references master files
    # (reference file already has correct rels, but we need page1.xml.rels)
    if 'visio/pages/_rels/page1.xml.rels' not in out:
        out['visio/pages/_rels/page1.xml.rels'] = ('''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/master" Target="../masters/master2.xml"/>
  <Relationship Id="rId2" Type="http://schemas.microsoft.com/visio/2010/relationships/master" Target="../masters/master1.xml"/>
  <Relationship Id="rId3" Type="http://schemas.microsoft.com/visio/2010/relationships/master" Target="../masters/master4.xml"/>
  <Relationship Id="rId4" Type="http://schemas.microsoft.com/visio/2010/relationships/master" Target="../masters/master3.xml"/>
</Relationships>''').encode()

    # Add RecalcDocument to docProps/custom.xml — required for programmatically generated VSDX
    # so Visio recalculates connector routing on open
    custom_xml = out.get('docProps/custom.xml', b'')
    if b'RecalcDocument' not in custom_xml:
        # Parse and inject
        import xml.etree.ElementTree as ET
        try:
            cust_root = ET.fromstring(custom_xml)
            ns = {'cp': 'http://schemas.openxmlformats.org/officeDocument/2006/custom-properties',
                  'vt': 'http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes'}
            # Find max pid
            props = cust_root.findall('cp:property', ns)
            max_pid = max(int(p.get('pid', 0)) for p in props) if props else 0
            
            import uuid
            recalc = ET.SubElement(cust_root, '{http://schemas.openxmlformats.org/officeDocument/2006/custom-properties}property')
            recalc.set('fmtid', '{D5CDD505-2E9C-101B-9397-08002B2CF9AE}')
            recalc.set('pid', str(max_pid + 1))
            recalc.set('name', 'RecalcDocument')
            val = ET.SubElement(recalc, '{http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes}bool')
            val.text = 'true'
            
            out['docProps/custom.xml'] = ET.tostring(cust_root, encoding='unicode').encode('utf-8')
        except Exception as e:
            print(f"Warning: Could not add RecalcDocument: {e}")

    shape_xmls = []
    all_connects = []

    for nid in sorted(nodes):
        shape_xmls.append(make_shape_xml(nid, nodes[nid], *positions[nid]))

    cid = 2000
    for e in edges:
        src_col = column.get(e['src'], 'L')
        tgt_col = column.get(e['tgt'], 'L')
        conn_xml, conns = make_connector_xml(e, positions[e['src']], positions[e['tgt']],
                                              src_col, tgt_col, cid)
        shape_xmls.append(conn_xml)
        all_connects.extend(conns)
        cid += 1

    shapes_block = '\n      '.join(shape_xmls)
    connects_block = '\n      '.join(all_connects)

    page1 = f'''<?xml version='1.0' encoding='utf-8' ?>
<PageContents xmlns='http://schemas.microsoft.com/office/visio/2012/main' xmlns:r='http://schemas.openxmlformats.org/officeDocument/2006/relationships' xml:space='preserve'>
  <Shapes>
      {shapes_block}
  </Shapes>
  <Connects>
      {connects_block}
  </Connects>
</PageContents>'''
    out['visio/pages/page1.xml'] = page1.encode()

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in out.items():
            z.writestr(name, data)

    return output_path


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 mermaid_to_vsdx.py 'mermaid_text' output.vsdx")
        sys.exit(1)

    mermaid_text = sys.argv[1]
    output_path = sys.argv[2]

    nodes, edges = parse_mermaid(mermaid_text)
    if not nodes:
        print("Error: could not parse Mermaid text")
        sys.exit(1)

    level = build_flow_levels(nodes, edges)
    column = assign_columns(nodes, edges, level)

    print(f"Parsed {len(nodes)} nodes, {len(edges)} edges")
    for nid in sorted(nodes):
        n = nodes[nid]
        print(f"  ID={nid}: {n['label']} [{n['type']}] L={level[nid]} C={column[nid]}")

    build_vsdx(nodes, edges, level, column, output_path)
    print(f"Output: {output_path}")


if __name__ == '__main__':
    main()
