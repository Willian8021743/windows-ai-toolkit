# MCP 服务器配置 / MCP Servers

本仓库收录 5 个 MCP 服务器：2 个本地 stdio（Windows 原生能力 + 浏览器自动化），
3 个远程 HTTP（Figma / Notion / Linear）。

| 名称 | 传输 | 入口 | 适用客户端 |
| --- | --- | --- | --- |
| windows-mcp | stdio | <code>%USERPROFILE%\.local\bin\windows-mcp.exe serve</code> | 全部 |
| playwright | stdio | <code>npx -y @playwright/mcp@latest --browser chrome</code> | 全部 |
| figma | HTTP | <code>https://mcp.figma.com/mcp</code> | 支持远程 MCP 的客户端 |
| notion | HTTP | <code>https://mcp.notion.com/mcp</code> | 支持远程 MCP 的客户端 |
| linear | HTTP | <code>https://mcp.linear.app/mcp</code> | 支持远程 MCP 的客户端 |

现成配置样例在 [configs/](configs)：

- [configs/goose.extensions.yaml](configs/goose.extensions.yaml)
- [configs/claude_desktop_config.json](configs/claude_desktop_config.json)
- [configs/cursor.mcp.json](configs/cursor.mcp.json)
- [configs/codex.config.toml](configs/codex.config.toml)

---

## 1. windows-mcp —— 桌面控制

上游：<https://github.com/CursorTouch/Windows-MCP>（MIT）

### 安装

~~~~powershell
winget install astral-sh.uv      # 若还没装 uv
uv tool install windows-mcp
windows-mcp --help               # 验证，可执行文件位于 %USERPROFILE%\.local\bin\
~~~~

### 提供的能力

| 工具 | 作用 |
| --- | --- |
| <code>Snapshot</code> / <code>Screenshot</code> | 截屏 + 可交互元素树（含坐标） |
| <code>Click</code> / <code>Type</code> / <code>Scroll</code> / <code>Move</code> | 鼠标键盘操作 |
| <code>Shortcut</code> | 组合键，如 <code>ctrl+c</code>、<code>win+r</code> |
| <code>App</code> | 启动应用、切窗口、调整窗口大小 |
| <code>WaitFor</code> / <code>Wait</code> | 等待元素/窗口/时长 |
| <code>Scrape</code> | 抓取网页正文（可用 DOM 模式） |
| <code>Clipboard</code> / <code>Notification</code> | 剪贴板读写、系统通知 |
| <code>DisplayInventory</code> | 多显示器与 DPI 信息 |

### 安全提示

这个 MCP 等价于把键鼠交给模型。建议：

- 只在需要时启用（goose 里可用 <code>extensionmanager</code> 临时开关）
- 不要在挂着网银/工作 IM 的会话里放任其自由操作
- 敏感操作前让它先 <code>Snapshot</code>，确认焦点窗口

---

## 2. Playwright MCP —— 浏览器自动化

上游：<https://github.com/microsoft/playwright-mcp>（Apache-2.0）

~~~~powershell
node --version        # 需要 20+
npx -y @playwright/mcp@latest --help
~~~~

首次运行会下载 Playwright 运行时；国内网络可设置镜像：

~~~~powershell
$env:npm_config_registry = 'https://registry.npmmirror.com'
$env:PLAYWRIGHT_DOWNLOAD_HOST = 'https://npmmirror.com/mirrors/playwright'
~~~~

提供导航、点击、表单填写、a11y 快照、网络请求查看、多标签、截图等工具。

---

## 3. 远程 MCP（Figma / Notion / Linear）

这三家是托管服务，只需在客户端里登记 URL，首次连接走 OAuth：

~~~~json
{
  "mcpServers": {
    "figma":  { "url": "https://mcp.figma.com/mcp" },
    "notion": { "url": "https://mcp.notion.com/mcp" },
    "linear": { "url": "https://mcp.linear.app/mcp" }
  }
}
~~~~

Codex 用 TOML：

~~~~toml
[mcp_servers.figma]
url = "https://mcp.figma.com/mcp"
~~~~

---

## 各客户端配置位置

| 客户端 | 文件 | 顶层键 |
| --- | --- | --- |
| goose | <code>%APPDATA%\Block\goose\config\config.yaml</code> | <code>extensions:</code> |
| Claude Desktop | <code>%APPDATA%\Claude\claude_desktop_config.json</code> | <code>mcpServers</code> |
| Claude Code | <code>~/.claude.json</code> 或 <code>claude mcp add</code> | <code>mcpServers</code> |
| Cursor | <code>%USERPROFILE%\.cursor\mcp.json</code> | <code>mcpServers</code> |
| Codex CLI | <code>%USERPROFILE%\.codex\config.toml</code> | <code>[mcp_servers.*]</code> |

一条命令写入（推荐）：

~~~~powershell
.\scripts\install.ps1 -SkillsTarget none -McpTarget all
~~~~

---

## 排错

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| goose 启动报 extension 超时 | windows-mcp 启动慢/路径错误 | 手动执行 <code>windows-mcp serve</code> 看报错；确认 <code>cmd</code> 指向真实 exe |
| Playwright 报 browser not found | 未装 Chrome | <code>npx playwright install chrome</code> |
| npx 每次都很慢 | 未缓存 | <code>npm i -g @playwright/mcp</code> 后改用 <code>playwright-mcp</code> |
| 远程 MCP 401 | OAuth 未完成 | 在客户端里触发一次登录，或换用 API key 版本 |
