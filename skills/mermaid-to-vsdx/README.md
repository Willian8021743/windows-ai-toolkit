# Mermaid → Visio VSDX Skill

Convert Mermaid flowchart diagrams into real Microsoft Visio `.vsdx` files.  
Pure Python, no Visio required to generate.

## Quick Start

```bash
git clone https://github.com/simoneven/mermaid-to-vsdx-skill.git
cd mermaid-to-vsdx-skill
python scripts/gen_vsdx.py 'graph TD; A[Start] --> B[Process]; B --> C{Decision}; C -->|Yes| D[End]' output.vsdx
```

## For Hermes Users

```bash
cp -r mermaid-to-vsdx-skill ~/.hermes/skills/productivity/
```

## Author
Simon Chen — [szhzz.com](https://szhzz.com)
