# Windows AI Toolkit

> **61 个 Skills + 5 个 MCP 服务器，一条 PowerShell 命令接入 goose / Claude / Cursor / Codex。**

把散落在各处的 AI 技能与 MCP 配置收拢成一个可版本化、可审查、可一键安装的 Windows 项目。

![platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4)
![skills](https://img.shields.io/badge/skills-61-brightgreen)
![mcp](https://img.shields.io/badge/MCP-5-blue)
![license](https://img.shields.io/badge/license-MIT%20%2B%20third--party-lightgrey)

---

## 快速开始

~~~~powershell
git clone https://github.com/Willian8021743/windows-ai-toolkit.git
cd windows-ai-toolkit

# 预览将要执行的操作（不写任何文件）
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkillsTarget all -McpTarget all -DryRun

# 正式安装：技能复制到各客户端，MCP 写入各客户端配置
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkillsTarget all -McpTarget all
~~~~

只给 goose 装：

~~~~powershell
.\scripts\install.ps1 -SkillsTarget agents -McpTarget goose
~~~~

装完自检：

~~~~powershell
.\scripts\verify.ps1
~~~~

---

## 包含什么

### Skills（61 个，9 大类）

| 类别 | 数量 | 代表技能 |
| --- | ---: | --- |
| 办公与文档 | 15 | brand-docx / brand-pptx / brand-xlsx、deck-refresh、excel-hygiene、pivot-table-builder、scenario-manager、pdf-converter、mermaid-to-vsdx |
| 金融与投研 | 3 | reverse-dcf（反推市场隐含增长）、ib-check-deck（投行级 deck 质检）、evidence-chain-builder |
| 网络与实验 | 3 | network-engineering、packet-tracer（真实 PT 8.2.2 校验）、pkt（生成/编辑 .pkt） |
| 浏览器与自动化 | 2 | browser-use（CDP 控制）、webapp-testing（Playwright 测试本机 Web 应用） |
| 社交与媒体 | 15 | bilibili / weibo / xiaohongshu / xianyu / twitter-x / tg / spotify / ytmusic / bilibili 下载等 |
| 搜索与研究 | 5 | exa-search、tavily-search、web-content-extractor、openstreetmap-marker |
| 创作与设计 | 10 | answer-me-with-html（一页纸可视化解释）、hyperframes（HTML 视频）、nano-banana / codex-image（生图）、免费 TTS |
| 开发与运维 | 7 | github-sync-helper、clash-controller、cloudflare-dns、notion-hub、memos-api |
| 示例 | 1 | hello-demo |

完整清单与说明见 [docs/SKILLS.md](docs/SKILLS.md)。

### MCP 服务器（5 个）

| 名称 | 类型 | 能力 | Windows 依赖 |
| --- | --- | --- | --- |
| **windows-mcp** | stdio | 截屏、点击、输入、快捷键、窗口控制、剪贴板、通知——让模型真正操作 Windows 桌面 | <code>uv tool install windows-mcp</code> |
| **playwright** | stdio | 浏览器自动化：导航、点击、a11y 快照、网络请求、多标签 | Node 20+、Chrome |
| **figma** | HTTP | 读取设计稿（远程服务） | 无 |
| **notion** | HTTP | 读写 Notion 工作区（远程服务） | 无 |
| **linear** | HTTP | 读取 Linear 议题（远程服务） | 无 |

配置样例见 [mcp/configs](mcp/configs)，接入说明见 [docs/MCP.md](docs/MCP.md)。

---

## 安装到哪里

| 目标 | Skills 目录 | MCP 配置文件 |
| --- | --- | --- |
| goose / 通用 agents | <code>%USERPROFILE%\.agents\skills</code> | <code>%APPDATA%\Block\goose\config\config.yaml</code> |
| Claude Code | <code>%USERPROFILE%\.claude\skills</code> | — |
| Codex CLI | <code>%USERPROFILE%\.codex\skills</code> | <code>%USERPROFILE%\.codex\config.toml</code> |
| Cursor | <code>%USERPROFILE%\.cursor\skills-cursor</code> | <code>%USERPROFILE%\.cursor\mcp.json</code> |
| Claude Desktop | — | <code>%APPDATA%\Claude\claude_desktop_config.json</code> |

安装脚本**只做增量合并**：已存在的同名技能默认跳过（加 <code>-Force</code> 覆盖），
配置文件改动前会生成带时间戳的 <code>.bak-*</code> 备份，已有的 MCP 条目不会被覆盖。

---

## 目录结构

~~~~
windows-ai-toolkit/
├── skills/                  # 61 个技能，每个含 SKILL.md
│   ├── answer-me-with-html/
│   ├── network-engineering/
│   └── ...
├── mcp/
│   ├── windows-mcp/README.md
│   ├── playwright/README.md
│   └── configs/             # goose / claude / cursor / codex 配置样例
├── scripts/
│   ├── install.ps1          # 一键安装（支持 -DryRun）
│   ├── verify.ps1           # 安装自检
│   └── validate.mjs         # 仓库结构校验（CI 使用）
├── docs/
│   ├── SKILLS.md            # 自动生成的技能清单
│   ├── MCP.md               # MCP 详解与各客户端配置
│   └── INSTALL.md           # 手动安装 / 环境变量 / 卸载
├── manifest.json            # 机器可读清单
├── NOTICE.md                # 第三方许可分层
└── LICENSE
~~~~

---

## 前置依赖

| 依赖 | 用途 | 安装 |
| --- | --- | --- |
| PowerShell 5.1+ | 安装脚本 | Windows 自带 |
| Git | 克隆与更新 | <code>winget install Git.Git</code> |
| Python 3.11+ + uv | 大多数技能是 Python 脚本 | <code>winget install astral-sh.uv</code> |
| Node.js 20+ | Playwright MCP、部分技能 | <code>winget install OpenJS.NodeJS.LTS</code> |
| Chrome | Playwright MCP | <https://www.google.com/chrome/> |

技能大多通过 <code>uv run</code> 声明依赖，首次执行时自动拉取，无需预装一堆包。

---

## 安全须知

- **技能是可执行内容**：SKILL.md 会指示模型运行脚本、访问网络。安装前请先读一遍，尤其是带 <code>scripts/</code> 的技能。
- **windows-mcp 能接管键鼠**：相当于把桌面控制权交给模型，建议在受控环境使用。
- **凭据不入库**：本仓库不含任何 token、cookie 或账号文件；社交类技能通过浏览器会话现场取 cookie。
- **密钥请放环境变量**：见 [docs/INSTALL.md](docs/INSTALL.md#环境变量)。
- 安装脚本对已存在的配置只追加、不删除，且保留备份。

---

## 许可

- 仓库脚本与文档：MIT（[LICENSE](LICENSE)）
- 各技能：遵循其自带许可，详见 [NOTICE.md](NOTICE.md)
- **未收录** docx / pptx / xlsx / pdf 四个 Anthropic 专有许可技能（禁止再分发），
  请从 <https://github.com/anthropics/skills> 获取。

---

## English

A curated, Windows-ready bundle of 61 AI agent skills and 5 MCP servers, with a
one-command PowerShell installer that wires them into goose, Claude Code/Desktop,
Cursor and Codex.

~~~~powershell
git clone https://github.com/Willian8021743/windows-ai-toolkit.git
cd windows-ai-toolkit
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkillsTarget all -McpTarget all
~~~~

Skills are plain <code>SKILL.md</code> folders and work with any agent that reads
that convention. The installer is additive: existing skills and MCP entries are
never overwritten, and every config change is backed up first.

See [docs/SKILLS.md](docs/SKILLS.md) for the full index and
[docs/MCP.md](docs/MCP.md) for client configuration snippets.
