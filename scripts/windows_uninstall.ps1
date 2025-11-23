<#
Windows uninstaller for MegaSmart AI (complements windows_install.ps1)

What it does:
- Removes installation folder and shortcuts created by the installer

Usage:
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\scripts\windows_uninstall.ps1
#>

Param()

$installPath = Read-Host "Enter install folder to uninstall (default: $env:LOCALAPPDATA\\MegaSmartAI)"
if ([string]::IsNullOrWhiteSpace($installPath)) { $installPath = Join-Path $env:LOCALAPPDATA 'MegaSmartAI' }

if (-not (Test-Path $installPath)) { Write-Host "Install folder not found: $installPath"; exit 0 }

Write-Host "This will remove: $installPath and associated shortcuts. Continue?"
$yn = Read-Host "Confirm [y/N]"
if ($yn.Trim().ToLower() -ne 'y') { Write-Host "Aborted."; exit 0 }

try {
    Remove-Item -Path $installPath -Recurse -Force -ErrorAction Stop
    Write-Host "Removed: $installPath"
} catch {
    Write-Warning "Failed to remove install folder: $_"
}

# Remove shortcuts
$desktopPath = [Environment]::GetFolderPath('Desktop')
$lnkDesktop = Join-Path $desktopPath 'MegaSmart AI.lnk'
if (Test-Path $lnkDesktop) { Remove-Item $lnkDesktop -Force }

$startMenuFolder = Join-Path ([Environment]::GetFolderPath('StartMenu')) 'Programs\MegaSmart AI'
if (Test-Path $startMenuFolder) {
    Remove-Item -Path $startMenuFolder -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Uninstall complete."
