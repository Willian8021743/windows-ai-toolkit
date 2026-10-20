#!/usr/bin/env node
/**
 * 重新生成 docs/SKILLS.md 与 manifest.json
 *   node scripts/gen-index.mjs
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SKILLS = path.join(ROOT, 'skills');
const BT = String.fromCharCode(96);

const EXCLUDED = {
  docx: 'Anthropic proprietary license — redistribution prohibited',
  pptx: 'Anthropic proprietary license — redistribution prohibited',
  xlsx: 'Anthropic proprietary license — redistribution prohibited',
  pdf:  'Anthropic proprietary license — redistribution prohibited',
};

const CATEGORIES = {
  '办公与文档': ['brand-docx','brand-pptx','brand-xlsx','.brand-docs','document-polisher','deck-refresh','excel-hygiene','formula-audit-checker','data-cleaning-for-excel','pivot-table-builder','inputs-calcs-outputs-design','model-architecture-template','scenario-manager','pdf-converter','mermaid-to-vsdx'],
  '金融与投研': ['reverse-dcf','ib-check-deck','evidence-chain-builder'],
  '网络与实验': ['network-engineering','packet-tracer','pkt'],
  '浏览器与自动化': ['browser-use','webapp-testing'],
  '社交与媒体': ['bilibili-hub','douyin-downloader','youtube-downloader','twitter-downloader','twitter-x-hub','weibo-hub','xiaohongshu-hub','xianyu-hub','maimai-hub','tg-hub','spotify-hub','ytmusic-hub','quark-hub','qbt-hub','fucai3d-latest'],
  '搜索与研究': ['exa-search','tavily-search','web-content-extractor','whenpeak','openstreetmap-marker'],
  '创作与设计': ['answer-me-with-html','hyperframes','frontend-design','web-artifacts-builder','generative-ui-minis','nano-banana','codex-image','free-tts','doubao-tts','contact-vcard-extractor'],
  '开发与运维': ['github-sync-helper','production-agent-public','self-improving-agent','clash-controller','cloudflare-dns','memos-api','notion-hub'],
  '示例': ['hello-demo'],
};

const catOf = new Map();
for (const [cat, list] of Object.entries(CATEGORIES)) for (const d of list) catOf.set(d, cat);

function parseFrontmatter(raw) {
  if (!raw.startsWith('---')) return {};
  const end = raw.indexOf('\n---', 3);
  if (end === -1) return {};
  const out = {};
  let key = null, buf = [];
  const flush = () => { if (key) { out[key] = buf.join(' ').trim(); key = null; buf = []; } };
  for (const line of raw.slice(3, end).replace(/\r/g, '').split('\n')) {
    const m = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
    if (m) { flush(); key = m[1]; buf = [m[2]]; }
    else if (key) buf.push(line);
  }
  flush();
  for (const k of Object.keys(out)) {
    out[k] = out[k].replace(/^[>|][+-]?\s*/, '').replace(/^-\s+/, '').replace(/\s+/g, ' ').trim();
  }
  return out;
}

function stats(dir) {
  let files = 0, bytes = 0;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) { const s = stats(p); files += s.files; bytes += s.bytes; }
    else if (e.isFile()) { files++; bytes += fs.statSync(p).size; }
  }
  return { files, bytes };
}

const included = [];
const excluded = [];
for (const name of fs.readdirSync(SKILLS).sort()) {
  const dir = path.join(SKILLS, name);
  if (!fs.statSync(dir).isDirectory()) continue;
  const file = path.join(dir, 'SKILL.md');
  const fm = fs.existsSync(file) ? parseFrontmatter(fs.readFileSync(file, 'utf8')) : {};
  const st = stats(dir);
  const item = {
    dir: name,
    name: fm.name || name,
    description: fm.description || '',
    license: fm.license || '',
    files: st.files,
    sizeKB: Math.round(st.bytes / 1024),
  };
  if (EXCLUDED[name]) excluded.push({ ...item, reason: EXCLUDED[name] });
  else included.push({ ...item, category: catOf.get(name) || '其他' });
}
for (const name of Object.keys(EXCLUDED)) {
  if (!excluded.some(e => e.dir === name)) {
    excluded.push({ dir: name, name, description: '', license: 'Proprietary (Anthropic)', files: 0, sizeKB: 0, reason: EXCLUDED[name] });
  }
}

included.sort((a, b) => a.category.localeCompare(b.category, 'zh') || a.dir.localeCompare(b.dir));

const clean = (s) => s.replace(/^[-–—>\s]+/, '').replace(/\s+/g, ' ').trim();
const trunc = (s, n) => s.length <= n ? s : s.slice(0, n - 1).trimEnd() + '…';
const esc = (s) => s.replace(/\|/g, String.fromCharCode(92) + '|');

let md = '# 技能清单 / Skills Index\n\n';
md += '> 自动生成（node scripts/gen-index.mjs），请勿手动编辑。共 **' + included.length + '** 个技能。\n\n';
md += '| 类别 | 技能数 |\n| --- | ---: |\n';
for (const cat of Object.keys(CATEGORIES)) {
  const n = included.filter(s => s.category === cat).length;
  if (n) md += '| ' + cat + ' | ' + n + ' |\n';
}
md += '\n---\n';

for (const cat of Object.keys(CATEGORIES)) {
  const items = included.filter(s => s.category === cat);
  if (!items.length) continue;
  md += '\n## ' + cat + '（' + items.length + '）\n\n';
  md += '| 技能 | 说明 | 文件 | 大小 |\n| --- | --- | ---: | ---: |\n';
  for (const s of items) {
    const desc = s.description ? trunc(clean(s.description), 190) : '_（品牌技能的支撑资源，无独立 SKILL.md）_';
    const size = s.sizeKB >= 1024 ? (s.sizeKB / 1024).toFixed(1) + ' MB' : s.sizeKB + ' KB';
    md += '| [' + BT + s.dir + BT + '](../skills/' + s.dir + '/) | ' + esc(desc) + ' | ' + s.files + ' | ' + size + ' |\n';
  }
}

if (excluded.length) {
  md += '\n## 未包含（许可限制）\n\n| 技能 | 原因 | 替代方案 |\n| --- | --- | --- |\n';
  for (const s of excluded) {
    md += '| ' + BT + s.dir + BT + ' | ' + s.reason + ' | 从 [anthropics/skills](https://github.com/anthropics/skills) 获取 |\n';
  }
}
fs.writeFileSync(path.join(ROOT, 'docs', 'SKILLS.md'), md, 'utf8');

const manifest = {
  name: 'windows-ai-toolkit',
  version: '1.0.0',
  generatedAt: new Date().toISOString(),
  platform: 'windows',
  stats: {
    skills: included.length,
    files: included.reduce((a, s) => a + s.files, 0),
    sizeKB: included.reduce((a, s) => a + s.sizeKB, 0),
  },
  skills: included.map(s => ({ dir: s.dir, name: s.name, category: s.category, license: s.license || null, files: s.files, sizeKB: s.sizeKB })),
  excluded: excluded.map(s => ({ dir: s.dir, reason: s.reason })),
  mcpServers: ['windows-mcp', 'playwright', 'figma', 'notion', 'linear'],
};
fs.writeFileSync(path.join(ROOT, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n', 'utf8');

console.log('生成完成: ' + included.length + ' 个技能, ' + excluded.length + ' 个排除');
