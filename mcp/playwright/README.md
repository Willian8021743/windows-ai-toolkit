# playwright MCP

浏览器自动化的官方 MCP 服务器（Microsoft）。

- 上游：<https://github.com/microsoft/playwright-mcp>
- 许可：Apache-2.0
- 传输：stdio

## 运行

~~~~powershell
npx -y @playwright/mcp@latest --browser chrome
~~~~

## 最小配置

~~~~json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest", "--browser", "chrome"]
    }
  }
}
~~~~

国内网络建议先设置镜像，见 [../docs/MCP.md](../docs/MCP.md)。
