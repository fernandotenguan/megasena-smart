# Run Update & Serve

## Purpose

Small launcher that:

- Runs the collector (`coletor_megasena.py`) to update the SQLite DB
- Starts the Flask app (`main.py`)
- Waits until the server is available and opens the default browser

## Usage (development)

Activate your project venv and run the launcher with the same interpreter:

PowerShell (Windows):

```powershell
venv\Scripts\Activate.ps1
python scripts\run_update_and_serve.py
```

This uses `sys.executable` so it will use the activated environment's Python.

## Create a single-file executable (optional)

If you want a single `.exe` to distribute, you can use PyInstaller.
Install PyInstaller in your venv:

```powershell
venv\Scripts\Activate.ps1
pip install pyinstaller
```

Then build:

```powershell
pyinstaller --onefile --noconsole --add-data "app;app" --add-data "templates;templates" scripts\run_update_and_serve.py
```

Notes:

- `--noconsole` hides the console window; remove it while debugging so you can see logs.
- Use `--add-data` to include folders used by your app; PyInstaller syntax for --add-data on Windows is `SRC;DEST`.
- After building you'll find the `.exe` in `dist\run_update_and_serve.exe`.

## Caveats

- The exe will embed the launcher only; if your collector/main import dynamic modules or files, you must ensure those files are included by PyInstaller (use `--add-data` and/or `--hidden-import`).
- Test thoroughly after packaging.

If you want, I can:

- Create a PowerShell wrapper with nicer prompts and logging
- Produce a ready PyInstaller command tuned for this repo (I can inspect imports and add `--add-data` entries)
- Build the `.exe` here if you allow installing PyInstaller into the venv (I will only modify files and show the commands).
