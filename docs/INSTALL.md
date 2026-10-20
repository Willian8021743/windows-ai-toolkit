# 安装与卸载 / Install Guide

## 1. 前置检查

~~~~powershell
$PSVersionTable.PSVersion      # 5.1 或 7+
git --version
uv --version                   # 没有就: winget install astral-sh.uv
node --version                 # 20+
~~~~

## 2. 一键安装

~~~~powershell
git clone https://github.com/Willian8021743/windows-ai-toolkit.git
cd windows-ai-toolkit

# 先预览
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkillsTarget all -McpTarget all -DryRun

# 再执行
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkillsTarget all -McpTarget all
~~~~

### 参数

| 参数 | 取值 | 说明 |
| --- | --- | --- |
| <code>-SkillsTarget</code> | <code>agents</code> / <code>goose</code> / <code>claude</code> / <code>codex</code> / <code>cursor</code> / <code>all</code> / <code>none</code> | 可多选，默认 <code>agents</code> |
| <code>-McpTarget</code> | <code>none</code> / <code>goose</code> / <code>claude</code> / <code>cursor</code> / <code>codex</code> / <code>all</code> | 默认 <code>none</code> |
| <code>-Force</code> | 开关 | 覆盖已存在的同名技能 |
| <code>-DryRun</code> | 开关 | 只打印计划，不落盘 |

## 3. 只装单个技能

技能就是文件夹，复制即可：

~~~~powershell
Copy-Item .\skills\network-engineering "$env:USERPROFILE\.agents\skills\" -Recurse -Force
~~~~

## 4. 环境变量

大部分技能无需密钥。需要外部服务的，按需设置（用户级，永久）：

~~~~powershell
[Environment]::SetEnvironmentVariable('TAVILY_API_KEY','tvly-xxx','User')
[Environment]::SetEnvironmentVariable('EXA_API_KEY','xxx','User')
[Environment]::SetEnvironmentVariable('NOTION_API_KEY','ntn_xxx','User')
[Environment]::SetEnvironmentVariable('GITHUB_TOKEN','ghp_xxx','User')
~~~~

| 变量 | 用于 | 备注 |
| --- | --- | --- |
| <code>TAVILY_API_KEY</code> | tavily-search | <https://tavily.com> |
| <code>EXA_API_KEY</code> | exa-search | <https://exa.ai> |
| <code>NOTION_API_KEY</code> | notion-hub | Notion integration token |
| <code>GITHUB_TOKEN</code> | github-sync-helper | 建议 fine-grained PAT |
| <code>DOUBAO_TTS_APPID</code> / <code>DOUBAO_TTS_TOKEN</code> | doubao-tts | 火山引擎控制台 |
| <code>VOLC_ACCESS_KEY</code> / <code>VOLC_APP_KEY</code> | douyin-downloader 转写 | 火山引擎 ASR |
| <code>SPOTIPY_CLIENT_ID</code> / <code>SPOTIPY_CLIENT_SECRET</code> | spotify-hub | Spotify Developer |
| <code>TG_API_ID</code> / <code>TG_API_HASH</code> | tg-hub | <https://my.telegram.org> |
| <code>QBT_USER</code> / <code>QBT_PASS</code> / <code>QBT_HOST</code> | qbt-hub | qBittorrent WebUI |
| <code>CODEX_IMAGE_TOKEN</code> | codex-image | 可选，默认自动从浏览器会话读取 |
| <code>GEMINI_API_KEY</code> | nano-banana | Google AI Studio |
| <code>XHS_WEB_SESSION</code> / <code>XHS_A1</code> / <code>XHS_WEBID</code> | xiaohongshu-hub | 可选，默认自动取 cookie |

**不要把密钥写进仓库里的任何文件。** 本仓库的 <code>.gitignore</code> 已屏蔽 <code>.env*</code>。

## 5. 手动配置 MCP

见 [MCP.md](MCP.md)，或直接复制 [../mcp/configs](../mcp/configs) 里对应客户端的样例。

## 6. 验证

~~~~powershell
.\scripts\verify.ps1
~~~~

会检查：技能数量、各目标目录、windows-mcp 可执行文件、goose 配置中是否已有 windows-mcp 条目、
以及 uv / node / git 版本。

## 7. 更新

~~~~powershell
cd windows-ai-toolkit
git pull
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkillsTarget all -Force
~~~~

<code>-Force</code> 会覆盖同名技能；你自己改过的技能请先备份。

## 8. 卸载

~~~~powershell
# 技能
Get-ChildItem .\skills -Directory | ForEach-Object {
  Remove-Item "$env:USERPROFILE\.agents\skills\$($_.Name)" -Recurse -Force -ErrorAction SilentlyContinue
}

# MCP（删掉配置里的 windows-mcp / playwright 段落，并保留 .bak 备份）
~~~~

## 9. 常见问题

**Q：装完 goose 里看不到技能？**
A：goose 读取 <code>%USERPROFILE%\.agents\skills</code>，确认目录存在且每个技能里都有 <code>SKILL.md</code>；重启 goose。

**Q：Python 技能第一次跑很慢？**
A：<code>uv</code> 在解析并下载依赖。可设置国内索引：
<code>setx UV_DEFAULT_INDEX https://pypi.tuna.tsinghua.edu.cn/simple</code>

**Q：中文字符乱码？**
A：所有脚本文本按 UTF-8 保存；Windows 控制台请执行 <code>chcp 65001</code>。

**Q：公司电脑禁止脚本执行？**
A：用 <code>powershell -ExecutionPolicy Bypass -File ...</code> 单次绕过，或让 IT 签名。
