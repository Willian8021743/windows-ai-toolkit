#!/usr/bin/env node
/**
 * 仓库结构校验（CI 与本地通用）
 *   node scripts/validate.mjs
 * 检查：目录结构、SKILL.md frontmatter、manifest 一致性、疑似密钥、文件体积。
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const NL = String.fromCharCode(10);
const errors = [];
const warnings = [];

function readJson(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
}

function parseFrontmatter(raw) {
  if (!raw.startsWith('---')) return null;
  const end = raw.indexOf(NL + '---', 3);
  if (end === -1) return null;
  const body = raw.slice(3, end).replace(/\r/g, '');
  const out = {};
  let key = null;
  let buf = [];
  const flush = () => {
    if (key) { out[key] = buf.join(' ').trim(); key = null; buf = []; }
  };
  for (const line of body.split(NL)) {
    const m = /^([A-Za-z0-9_-]+):\s*(.*)$/.exec(line);
    if (m) { flush(); key = m[1]; buf = [m[2]]; }
    else if (key) buf.push(line);
  }
  flush();
  for (const k of Object.keys(out)) {
    out[k] = out[k]
      .replace(/^[>|][+-]?\s*/, '')
      .replace(/^-\s+/, '')
      .replace(/\s+/g, ' ')
      .trim();
  }
  return out;
}

function walkSize(dir) {
  let total = 0;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) total += walkSize(p);
    else if (e.isFile()) total += fs.statSync(p).size;
  }
  return total;
}

// 1. manifest
const manifestPath = path.join(ROOT, 'manifest.json');
if (!fs.existsSync(manifestPath)) errors.push('manifest.json 缺失');
const manifest = fs.existsSync(manifestPath) ? readJson(manifestPath) : null;

// 2. skills
const skillsDir = path.join(ROOT, 'skills');
if (!fs.existsSync(skillsDir)) errors.push('skills/ 缺失');
const dirs = fs.existsSync(skillsDir)
  ? fs.readdirSync(skillsDir, { withFileTypes: true }).filter(d => d.isDirectory()).map(d => d.name).sort()
  : [];

const SECRET = /(sk-[A-Za-z0-9]{24,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|xox[baprs]-[A-Za-z0-9-]{10,}|AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----)/;

const allFiles = [];
function walk(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (['__pycache__', 'node_modules', '.git', '.venv'].includes(e.name)) {
        warnings.push('应忽略的目录: ' + path.relative(ROOT, p));
        continue;
      }
      walk(p);
    } else if (e.isFile()) allFiles.push(p);
  }
}
if (fs.existsSync(skillsDir)) walk(skillsDir);

for (const name of dirs) {
  const skillDir = path.join(skillsDir, name);
  const skillFile = path.join(skillDir, 'SKILL.md');
  if (!fs.existsSync(skillFile)) {
    if (!name.startsWith('.')) warnings.push('缺少 SKILL.md: ' + name);
    continue;
  }
  const fm = parseFrontmatter(fs.readFileSync(skillFile, 'utf8'));
  if (!fm) { errors.push('frontmatter 无效: ' + name); continue; }
  if (!fm.name) warnings.push('frontmatter 缺 name: ' + name);
  if (!fm.description || fm.description.trim().length < 10) warnings.push('frontmatter 缺 description: ' + name);
  const size = walkSize(skillDir);
  if (size > 25 * 1024 * 1024) warnings.push('技能超过 25MB: ' + name);
}

// 3. manifest 与磁盘一致
if (manifest) {
  const listed = manifest.skills.map(s => s.dir).sort();
  const missing = listed.filter(d => !dirs.includes(d));
  const extra = dirs.filter(d => !listed.includes(d) && !d.startsWith('.'));
  if (missing.length) errors.push('manifest 列出但磁盘不存在: ' + missing.join(', '));
  if (extra.length) errors.push('磁盘存在但 manifest 未列出（请运行 node scripts/gen-index.mjs）: ' + extra.join(', '));
}

// 4. 密钥扫描
for (const f of allFiles) {
  if (!/\.(md|txt|json|ya?ml|js|mjs|ts|py|ps1|sh|toml)$/i.test(f)) continue;
  if (fs.statSync(f).size > 2 * 1024 * 1024) continue;
  const text = fs.readFileSync(f, 'utf8');
  if (SECRET.test(text)) errors.push('疑似密钥: ' + path.relative(ROOT, f));
}

// 5. 必需文件
for (const f of ['README.md', 'LICENSE', 'NOTICE.md', 'docs/SKILLS.md', 'docs/MCP.md', 'scripts/install.ps1']) {
  if (!fs.existsSync(path.join(ROOT, f))) errors.push('缺少文件: ' + f);
}

// 报告
console.log('skills: ' + dirs.length + '  files: ' + allFiles.length);
for (const w of warnings) console.log('WARN  ' + w);
for (const e of errors) console.log('ERROR ' + e);
if (errors.length) {
  console.log(NL + '校验失败: ' + errors.length + ' 个错误');
  process.exit(1);
}
console.log(NL + '校验通过 (' + warnings.length + ' 个警告)');
