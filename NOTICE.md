# NOTICE / 第三方声明

本仓库是一个**打包与分发容器**：其中的安装脚本、文档、清单（MIT）与
skills/ 目录下的内容是**分别授权**的。

## 许可分层

| 范围 | 许可 |
| --- | --- |
| 根目录脚本（scripts/）、文档（README、docs/）、manifest.json | MIT（见 LICENSE） |
| skills/<name>/ 下的每个技能 | 以该技能自带的 LICENSE 为准；没有 LICENSE 的，权利归原作者，仅作个人学习与配置备份用途 |
| MCP 服务器（windows-mcp、Playwright MCP 等） | 不随本仓库分发，由安装脚本从上游获取，遵循各自上游许可 |

## 已知第三方组件

| 组件 | 来源 | 许可 |
| --- | --- | --- |
| network-engineering | Juan David (Juanfrxz) | MIT |
| pkt | packet-tracer-skill contributors | MIT |
| mermaid-to-vsdx | Simonchen | MIT |
| excel-hygiene | 上游 skill 作者 | Apache-2.0 |
| frontend-design / webapp-testing / web-artifacts-builder | Anthropic | Apache-2.0 |
| answer-me-with-html 字体 | Bangers (Google Fonts) | SIL OFL 1.1 |
| @playwright/mcp | Microsoft | Apache-2.0 |
| windows-mcp | CursorTouch | MIT |

## 未收录的技能

以下四个技能带有 Anthropic 专有许可，明确禁止再分发，因此**不在本仓库中**：

- docx
- pptx
- xlsx
- pdf

请从 Anthropic 官方仓库获取并遵守其条款：<https://github.com/anthropics/skills>

## 商标

文中出现的产品名称与商标归各自所有者所有。本仓库与 Anthropic、Microsoft、
Cursor、Block 等公司无隶属或背书关系。
