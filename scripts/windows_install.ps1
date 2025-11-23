<#
Windows installer script for MegaSmart AI

What it does:
- Copies the built executable `dist\run_update_and_serve.exe` and required files into an install folder
- Creates shortcuts on the user's Desktop and in the Start Menu

Usage (PowerShell):
  Open PowerShell and run:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
    .\scripts\windows_install.ps1

Notes:
- This installer defaults to installing under `$env:LOCALAPPDATA\MegaSmartAI` (no admin required).
- The script assumes `dist\run_update_and_serve.exe` exists in the repository root.
#>

Param()

function Prompt-YesNo($msg, $default=$true) {
    $yn = Read-Host "$msg [Y/n]"
    if ([string]::IsNullOrWhiteSpace($yn)) { return $default }
    return $yn.Trim().ToLower().StartsWith('y')
}

$RepoRoot = Split-Path -Parent -Path $PSScriptRoot
$DefaultInstall = Join-Path $env:LOCALAPPDATA 'MegaSmartAI'

Write-Host "MegaSmart AI - Installer"
Write-Host "Repository root: $RepoRoot"

$installPath = Read-Host "Enter install folder (`$Default: $DefaultInstall` )"
if ([string]::IsNullOrWhiteSpace($installPath)) { $installPath = $DefaultInstall }

if (-not (Test-Path $installPath)) { New-Item -ItemType Directory -Path $installPath | Out-Null }

$distExe = Join-Path $RepoRoot 'dist\run_update_and_serve.exe'
if (-not (Test-Path $distExe)) {
    Write-Error "Executable not found: $distExe`nPlease build the exe first (see scripts/README_RUNNER.md)."
    exit 1
}

Write-Host "Copying files to $installPath..."
Copy-Item -Path $distExe -Destination $installPath -Force

# Copy main.py and coletor so the launcher can find them (launcher expects these alongside the exe)
foreach ($f in @('main.py','coletor_megasena.py')) {
    $src = Join-Path $RepoRoot $f
    if (Test-Path $src) { Copy-Item -Path $src -Destination $installPath -Force }
}

# Copy database file if present
$db = Join-Path $RepoRoot 'megasena_db.sqlite3'
if (Test-Path $db) { Copy-Item -Path $db -Destination $installPath -Force }

Write-Host "Creating Start Menu and Desktop shortcuts..."
$WshShell = New-Object -ComObject WScript.Shell

$desktopPath = [Environment]::GetFolderPath('Desktop')
$startMenuFolder = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\MegaSmart AI'
if (-not (Test-Path $startMenuFolder)) { New-Item -ItemType Directory -Path $startMenuFolder | Out-Null }

$exePath = Join-Path $installPath 'run_update_and_serve.exe'

# Desktop shortcut
$lnkDesktop = Join-Path $desktopPath 'MegaSmart AI.lnk'
$s = $WshShell.CreateShortcut($lnkDesktop)
$s.TargetPath = $exePath
$s.WorkingDirectory = $installPath
$s.IconLocation = "$exePath,0"
$s.Save()

# Start Menu shortcut
$lnkStart = Join-Path $startMenuFolder 'MegaSmart AI.lnk'
$s2 = $WshShell.CreateShortcut($lnkStart)
$s2.TargetPath = $exePath
$s2.WorkingDirectory = $installPath
$s2.IconLocation = "$exePath,0"
$s2.Save()

Write-Host "Installation complete. Shortcuts created on Desktop and Start Menu."
Write-Host "Install path: $installPath"
Write-Host "To uninstall, run scripts\windows_uninstall.ps1"
