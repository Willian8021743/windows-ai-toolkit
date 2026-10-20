#Requires -Version 5.1
<#
.SYNOPSIS
    安装 Windows AI Toolkit 的 Skills 与 MCP 配置。

.DESCRIPTION
    默认只复制技能到 %USERPROFILE%\.agents\skills，不碰任何配置。
    MCP 采用增量合并：只追加缺失条目，改动前生成 .bak-时间戳 备份。

.PARAMETER SkillsTarget
    技能安装目标，可多选：agents / goose / claude / codex / cursor / all / none

.PARAMETER McpTarget
    MCP 配置写入目标：none / goose / claude / cursor / codex / all

.PARAMETER Force
    覆盖已存在的同名技能

.PARAMETER DryRun
    只打印计划，不写入

.EXAMPLE
    .\install.ps1 -SkillsTarget all -McpTarget all -DryRun

.EXAMPLE
    .\install.ps1 -SkillsTarget agents -McpTarget goose
#>
[CmdletBinding()]
param(
    [ValidateSet('agents','goose','claude','codex','cursor','all','none')]
    [string[]]$SkillsTarget = @('agents'),

    [ValidateSet('none','goose','claude','cursor','codex','all')]
    [string]$McpTarget = 'none',

    [string]$Source,

    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$script:Installed = 0
$script:Skipped = 0

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  [ok]   $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "  [skip] $msg" -ForegroundColor DarkGray }
function Write-Warn2($msg){ Write-Host "  [warn] $msg" -ForegroundColor Yellow }
function Write-Plan($msg) { Write-Host "  [plan] $msg" -ForegroundColor Magenta }

if (-not $Source) { $Source = Split-Path -Parent $PSScriptRoot }
$skillsRoot = Join-Path $Source 'skills'
if (-not (Test-Path $skillsRoot)) { throw "找不到 skills 目录: $skillsRoot" }

if ($SkillsTarget -contains 'all')  { $SkillsTarget = @('agents','claude','codex','cursor') }
if ($SkillsTarget -contains 'none') { $SkillsTarget = @() }

$targets = [ordered]@{}
foreach ($t in $SkillsTarget) {
    switch ($t) {
        'agents' { $targets['agents'] = Join-Path $env:USERPROFILE '.agents\skills' }
        'goose'  { $targets['goose']  = Join-Path $env:USERPROFILE '.agents\skills' }
        'claude' { $targets['claude'] = Join-Path $env:USERPROFILE '.claude\skills' }
        'codex'  { $targets['codex']  = Join-Path $env:USERPROFILE '.codex\skills' }
        'cursor' { $targets['cursor'] = Join-Path $env:USERPROFILE '.cursor\skills-cursor' }
    }
}

$skillDirs = Get-ChildItem -Path $skillsRoot -Directory | Sort-Object Name

# ---------------------------------------------------------------- skills
if ($targets.Count -gt 0) {
    Write-Step ("安装技能 {0} 个 -> {1} 个目标" -f $skillDirs.Count, $targets.Count)
    foreach ($name in $targets.Keys) {
        $dest = $targets[$name]
        Write-Host "  target [$name]: $dest" -ForegroundColor White
        if ($DryRun) { Write-Plan "would copy $($skillDirs.Count) skills to $dest"; continue }
        if (-not (Test-Path $dest)) { New-Item -ItemType Directory -Path $dest -Force | Out-Null }

        foreach ($s in $skillDirs) {
            $dst = Join-Path $dest $s.Name
            if ((Test-Path $dst) -and -not $Force) { $script:Skipped++; continue }
            Copy-Item -Path $s.FullName -Destination $dst -Recurse -Force
            $script:Installed++
        }
        Write-Ok "copied to $dest"
    }
}

# ---------------------------------------------------------------- helpers
function Backup-File($path) {
    if (Test-Path $path) {
        $bak = "$path.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $path $bak -Force
        Write-Ok "backup -> $(Split-Path -Leaf $bak)"
    }
}

function Resolve-WindowsMcp {
    $exe = Join-Path $env:USERPROFILE '.local\bin\windows-mcp.exe'
    if (Test-Path $exe) { return $exe }
    $cmd = Get-Command windows-mcp -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Ensure-WindowsMcp {
    $exe = Resolve-WindowsMcp
    if ($exe) { return $exe }
    Write-Warn2 'windows-mcp 未安装，尝试 uv tool install windows-mcp'
    if (-not $DryRun) {
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            Write-Warn2 '未找到 uv，请先 winget install astral-sh.uv，或手动安装 windows-mcp'
            return $null
        }
        & uv tool install windows-mcp
        $exe = Resolve-WindowsMcp
        if ($exe) { Write-Ok "installed windows-mcp -> $exe" }
    }
    return $exe
}

function Merge-JsonServers($path, $servers) {
    $exists = Test-Path $path
    if ($DryRun) { Write-Plan "would merge MCP servers into $path"; return }
    if ($exists) { Backup-File $path }

    if (-not $exists) {
        $dir = Split-Path -Parent $path
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        $json = [pscustomobject]@{}
    } else {
        $raw = Get-Content $path -Raw -Encoding UTF8
        $json = if ([string]::IsNullOrWhiteSpace($raw)) { [pscustomobject]@{} } else { $raw | ConvertFrom-Json }
    }

    if (-not ($json.PSObject.Properties.Name -contains 'mcpServers')) {
        $json | Add-Member -NotePropertyName 'mcpServers' -NotePropertyValue ([pscustomobject]@{}) -Force
    }
    $added = 0
    foreach ($p in $servers.PSObject.Properties) {
        if ($json.mcpServers.PSObject.Properties.Name -contains $p.Name) {
            Write-Skip "$($p.Name) already configured"
        } else {
            $json.mcpServers | Add-Member -NotePropertyName $p.Name -NotePropertyValue $p.Value -Force
            $added++
        }
    }
    $json | ConvertTo-Json -Depth 20 | Set-Content -Path $path -Encoding UTF8
    Write-Ok "merged $added server(s) -> $path"
}

function Insert-GooseExtensions($path, $blocks) {
    $dir = Split-Path -Parent $path
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if (-not (Test-Path $path)) {
        if ($DryRun) { Write-Plan "would create $path with extensions"; return }
        Set-Content -Path $path -Value @('extensions:') -Encoding UTF8
    }

    $lines = Get-Content -Path $path -Encoding UTF8
    $toAdd = @()
    foreach ($b in $blocks) {
        $present = $lines | Where-Object { $_ -match ('^\s{2}' + [regex]::Escape($b.Name) + ':\s*$') }
        if ($present) { Write-Skip "$($b.Name) already in goose config" }
        else { $toAdd += $b }
    }
    if ($toAdd.Count -eq 0) { return }

    if ($DryRun) { Write-Plan "would insert $($toAdd.Count) extension block(s) into $path"; return }
    Backup-File $path

    $idx = -1
    for ($i = 0; $i -lt $lines.Count; $i++) { if ($lines[$i] -match '^extensions:\s*$') { $idx = $i; break } }

    $newBlock = @()
    foreach ($b in $toAdd) { $newBlock += $b.Lines }

    if ($idx -ge 0) {
        $out = @()
        $out += $lines[0..$idx]
        $out += $newBlock
        if ($idx + 1 -le $lines.Count - 1) { $out += $lines[($idx + 1)..($lines.Count - 1)] }
    } else {
        $out = @('extensions:') + $newBlock + $lines
    }
    Set-Content -Path $path -Value $out -Encoding UTF8
    Write-Ok "goose extensions updated -> $path"
}

# ---------------------------------------------------------------- MCP
if ($McpTarget -ne 'none') {
    Write-Step "配置 MCP: $McpTarget"
    $exePath = Ensure-WindowsMcp

    if ($exePath) {
        $winServer = [pscustomobject]@{
            command = $exePath
            args    = @('serve')
            env     = [pscustomobject]@{ UV_DEFAULT_INDEX = 'https://pypi.tuna.tsinghua.edu.cn/simple' }
        }
        $pwServer = [pscustomobject]@{
            command = 'npx'
            args    = @('-y','@playwright/mcp@latest','--browser','chrome')
        }

        if ($McpTarget -in @('claude','all')) {
            $claudePath = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
            Merge-JsonServers $claudePath ([pscustomobject]@{ 'windows-mcp' = $winServer; 'playwright' = $pwServer })
        }
        if ($McpTarget -in @('cursor','all')) {
            $cursorPath = Join-Path $env:USERPROFILE '.cursor\mcp.json'
            Merge-JsonServers $cursorPath ([pscustomobject]@{ 'windows-mcp' = $winServer; 'playwright' = $pwServer })
        }
        if ($McpTarget -in @('goose','all')) {
            $goosePath = Join-Path $env:APPDATA 'Block\goose\config\config.yaml'
            $blocks = @(
                [pscustomobject]@{ Name = 'windows-mcp'; Lines = @(
                    '  windows-mcp:',
                    '    type: stdio',
                    '    name: windows-mcp',
                    '    enabled: true',
                    ("    cmd: '" + $exePath + "'"),
                    '    args:',
                    '    - serve',
                    '    timeout: 300',
                    '    env_keys: []',
                    '    envs:',
                    '      UV_DEFAULT_INDEX: https://pypi.tuna.tsinghua.edu.cn/simple'
                )},
                [pscustomobject]@{ Name = 'playwright'; Lines = @(
                    '  playwright:',
                    '    type: stdio',
                    '    name: playwright',
                    '    display_name: Playwright',
                    '    enabled: true',
                    '    cmd: npx',
                    '    args:',
                    '    - -y',
                    "    - '@playwright/mcp@latest'",
                    '    - --browser',
                    '    - chrome',
                    '    timeout: 300'
                )}
            )
            Insert-GooseExtensions $goosePath $blocks
        }
        if ($McpTarget -in @('codex','all')) {
            $codexPath = Join-Path $env:USERPROFILE '.codex\config.toml'
            $tomlEsc = $exePath -replace '\\','\\'
            $snippet = @(
                '',
                '[mcp_servers.windows-mcp]',
                ('command = "' + $tomlEsc + '"'),
                'args = ["serve"]',
                '',
                '[mcp_servers.playwright]',
                'command = "npx"',
                'args = ["-y", "@playwright/mcp@latest", "--browser", "chrome"]'
            )
            $current = if (Test-Path $codexPath) { Get-Content $codexPath -Raw -Encoding UTF8 } else { '' }
            if ($current -match '\[mcp_servers\.windows-mcp\]') {
                Write-Skip 'windows-mcp already in codex config'
            } elseif ($DryRun) {
                Write-Plan "would append MCP sections to $codexPath"
            } else {
                if (Test-Path $codexPath) { Backup-File $codexPath }
                else { $d = Split-Path -Parent $codexPath; if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null } }
                Add-Content -Path $codexPath -Value $snippet -Encoding UTF8
                Write-Ok "codex config updated -> $codexPath"
            }
        }
    } else {
        Write-Warn2 '跳过 MCP 配置：windows-mcp 不可用'
        Write-Warn2 '请先执行 uv tool install windows-mcp，再重新运行本脚本'
    }
}

# ---------------------------------------------------------------- summary
Write-Host ''
Write-Step '完成'
Write-Host ("  技能复制: {0}   跳过(已存在): {1}" -f $script:Installed, $script:Skipped)
if ($DryRun) { Write-Host '  (DryRun: 未写入任何文件)' -ForegroundColor Magenta }
Write-Host ''
Write-Host '  下一步: 重启客户端，或运行 .\scripts\verify.ps1 自检' -ForegroundColor Yellow
