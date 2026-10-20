#Requires -Version 5.1
<#
.SYNOPSIS
    安装后的自检脚本。
.EXAMPLE
    .\verify.ps1
#>
[CmdletBinding()]
param([string]$Source)

$ErrorActionPreference = 'Continue'
if (-not $Source) { $Source = Split-Path -Parent $PSScriptRoot }

function Line($label, $value, $ok) {
    $mark = if ($null -eq $ok) { '  ' } elseif ($ok) { 'OK' } else { '!!' }
    Write-Host ("[{0}] {1,-34} {2}" -f $mark, $label, $value)
}

Write-Host ''
Write-Host 'Windows AI Toolkit - 自检' -ForegroundColor Cyan
Write-Host ('-' * 60)

# 仓库自身
$manifestPath = Join-Path $Source 'manifest.json'
if (Test-Path $manifestPath) {
    $m = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $repoSkills = @(Get-ChildItem (Join-Path $Source 'skills') -Directory).Count
    Line '仓库技能数 (manifest)' $m.stats.skills ($m.stats.skills -eq $repoSkills)
    Line '仓库技能数 (磁盘)' $repoSkills $true
} else {
    Line 'manifest.json' '缺失' $false
}

# 依赖
foreach ($tool in @('git','uv','node','npx')) {
    $c = Get-Command $tool -ErrorAction SilentlyContinue
    Line "$tool" $(if ($c) { $c.Source } else { '未安装' }) ([bool]$c)
}

# windows-mcp
$exe = Join-Path $env:USERPROFILE '.local\bin\windows-mcp.exe'
Line 'windows-mcp.exe' $(if (Test-Path $exe) { $exe } else { '未安装 (uv tool install windows-mcp)' }) (Test-Path $exe)

# 各客户端技能目录
$dirs = [ordered]@{
    'agents' = Join-Path $env:USERPROFILE '.agents\skills'
    'claude' = Join-Path $env:USERPROFILE '.claude\skills'
    'codex'  = Join-Path $env:USERPROFILE '.codex\skills'
    'cursor' = Join-Path $env:USERPROFILE '.cursor\skills-cursor'
}
foreach ($k in $dirs.Keys) {
    $p = $dirs[$k]
    $n = if (Test-Path $p) { @(Get-ChildItem $p -Directory).Count } else { 0 }
    Line "skills[$k]" $(if (Test-Path $p) { "$n 个 -> $p" } else { '未安装' }) ($n -gt 0)
}

# goose 配置
$goose = Join-Path $env:APPDATA 'Block\goose\config\config.yaml'
if (Test-Path $goose) {
    $txt = Get-Content $goose -Raw -Encoding UTF8
    Line 'goose: windows-mcp' $(if ($txt -match 'windows-mcp:') { '已配置' } else { '未配置' }) ($txt -match 'windows-mcp:')
    Line 'goose: playwright' $(if ($txt -match '(?m)^\s{2}playwright:') { '已配置' } else { '未配置' }) ($txt -match '(?m)^\s{2}playwright:')
} else {
    Line 'goose config.yaml' '未找到' $null
}

# 其他 MCP 配置
$cursorMcp = Join-Path $env:USERPROFILE '.cursor\mcp.json'
if (Test-Path $cursorMcp) {
    $cj = Get-Content $cursorMcp -Raw -Encoding UTF8 | ConvertFrom-Json
    $names = @($cj.mcpServers.PSObject.Properties.Name)
    Line 'cursor mcp.json' ($names -join ', ') ($names.Count -gt 0)
}
$codexToml = Join-Path $env:USERPROFILE '.codex\config.toml'
if (Test-Path $codexToml) {
    $t = Get-Content $codexToml -Raw -Encoding UTF8
    Line 'codex config.toml' $(if ($t -match 'mcp_servers\.') { '含 mcp_servers' } else { '无 mcp_servers' }) ($t -match 'mcp_servers\.')
}

Write-Host ('-' * 60)
Write-Host '完成。标 !! 的项需要处理。' -ForegroundColor Yellow
