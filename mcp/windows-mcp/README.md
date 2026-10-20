# windows-mcp

Windows 桌面控制的 MCP 服务器（截屏、点击、输入、窗口、剪贴板、通知）。

- 上游：<https://github.com/CursorTouch/Windows-MCP>
- 许可：MIT
- 传输：stdio

## 安装

~~~~powershell
uv tool install windows-mcp
~~~~

可执行文件：<code>%USERPROFILE%\.local\bin\windows-mcp.exe</code>

## 最小配置（Claude Desktop / Cursor）

~~~~json
{
  "mcpServers": {
    "windows-mcp": {
      "command": "C:\\Users\\<you>\\.local\\bin\\windows-mcp.exe",
      "args": ["serve"]
    }
  }
}
~~~~

完整工具列表与安全建议见 [../docs/MCP.md](../docs/MCP.md)。
