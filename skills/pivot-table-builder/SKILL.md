---
name: pivot-table-builder
description: Specifies and builds a pivot table from a flat data range, choosing rows, columns, values, and filters. Use it when you have raw tabular data and need a summary view without building it cell by cell.
---


> **Windows 环境**：技能目录为 C:\Users\Willian\.agents\skills\pivot-table-builder，脚本请用绝对路径或先 cd 进技能目录；产物写到当前工作目录。本机没有 LibreOffice（soffice），依赖它做渲染、缩略图、接受修订、公式重算的步骤会失败，其余 Python 操作正常。
# Pivot Table Builder

## When to use
Use this when you have a flat data range, one row per record, and need a summarized view by
category, time period, or segment, and would rather describe the summary you want than
build the pivot table manually.

## Instructions
1. Confirm the data range is genuinely flat: one header row, no merged cells, no subtotal rows mixed into the data.
2. Ask what question the summary needs to answer if it is not stated, since that decides which fields go where.
3. Propose the pivot table layout: which field goes to Rows, which to Columns, which to Values (and the aggregation, sum, count, or average), and any Filters.
4. Build the pivot table with that layout.
5. Flag any field that will not aggregate cleanly, for example a text column dropped into Values by mistake.

## Example prompts
- "Use the pivot-table-builder skill to summarize this sales data by region and month."
- "Build a pivot showing headcount by department and level from this raw HR export."

## Output
A pivot table specification (rows, columns, values, filters) and the built pivot table on the worksheet, with a one-line note on what it answers.
