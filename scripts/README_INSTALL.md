# Windows Installer / Shortcuts

Files added:

- `scripts/windows_install.ps1` — installer that copies `dist\run_update_and_serve.exe`, `main.py`, `coletor_megasena.py` and DB (if present) to an install folder and creates Desktop + Start Menu shortcuts.
- `scripts/windows_uninstall.ps1` — removes the install folder and shortcuts.

Quick install (PowerShell):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_install.ps1
```

Quick uninstall:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_uninstall.ps1
```

Default installation path: `%LOCALAPPDATA%\MegaSmartAI` (doesn't require admin privileges).

If you prefer installing to `Program Files`, run PowerShell as Administrator and specify the path when prompted.

## Notes

- The installer copies `run_update_and_serve.exe` from the `dist` folder; make sure the exe is present.
- The launcher expects `main.py` and `coletor_megasena.py` to be available next to the exe; the installer copies them so the exe can execute them.
- If you want a truly standalone exe (no external Python required), we should refactor the launcher to run collector/main logic inside the same process and rebuild the exe. I can do that if you want.
