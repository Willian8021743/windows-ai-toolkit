# 贡献指南

## 新增一个技能

1. 在 <code>skills/</code> 下新建目录，目录名用 kebab-case（与 frontmatter 的 <code>name</code> 一致）。
2. 目录内必须有 <code>SKILL.md</code>，开头是 YAML frontmatter：

~~~~markdown
---
name: my-skill
description: 一句话说明它做什么，以及什么时候该触发（这是模型判断是否使用的唯一依据）。
---

# My Skill

具体步骤……
~~~~

3. 脚本一律放在技能目录内的 <code>scripts/</code>，用 <code>uv run</code> 声明依赖，不要假设全局安装。
4. 不要提交密钥、cookie、个人路径（<code>C:\Users\你的名字</code>）。
5. 更新 <code>manifest.json</code> 与 <code>docs/SKILLS.md</code>：运行 <code>node scripts/gen-index.mjs</code>（或手动按同样格式补）。
6. 本地跑一遍：

~~~~powershell
node scripts/validate.mjs
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 -SkillsTarget agents -DryRun
~~~~

## Windows 兼容性要求

- 路径拼接不要硬编码 <code>/</code> 或 <code>~</code>，用 <code>pathlib</code> 或环境变量。
- 调外部程序时使用 <code>shutil.which</code>，并给出 Windows 下的安装提示。
- 控制台输出统一 UTF-8；不要在代码里 <code>print</code> emoji 依赖字体。

## 提交信息

<code>feat(skill): add xxx</code> / <code>fix(mcp): correct windows-mcp path</code> / <code>docs: ...</code>
