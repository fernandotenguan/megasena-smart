"""
Launcher: run_update_and_serve.py

- Runs the collector to update the DB (coletor_megasena.py)
- Then starts the Flask app (main.py) in a subprocess
- Waits until the server is reachable and opens the default browser

Designed to be run with the same Python interpreter/venv used by the project:

    venv\Scripts\activate
    python scripts/run_update_and_serve.py

This script is also suitable to be bundled with PyInstaller into a single exe.
"""

import os
import sys
import subprocess
import time
import socket
import webbrowser
import signal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COLETOR = ROOT / 'coletor_megasena.py'
MAIN = ROOT / 'main.py'

HOST = '127.0.0.1'
PORT = 5000
URL = f'http://{HOST}:{PORT}/'

def run_collector(python_exe: str) -> int:
    print('> Executando coletor para atualizar o banco...')
    if not COLETOR.exists():
        print('ERRO: arquivo coletor_megasena.py não encontrado em', COLETOR)
        return 2
    # Run collector and stream output
    proc = subprocess.run([python_exe, str(COLETOR)], cwd=str(ROOT))
    return proc.returncode


def start_main_server(python_exe: str) -> subprocess.Popen:
    if not MAIN.exists():
        raise FileNotFoundError(f'main.py não encontrado em {MAIN}')
    print('> Iniciando servidor Flask (main.py)...')
    # Start main.py as a detached process but keep stdout/stderr visible
    p = subprocess.Popen([python_exe, str(MAIN)], cwd=str(ROOT), stdout=None, stderr=None)
    return p


def wait_for_port(host: str, port: int, timeout: int = 20) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1.0)
            try:
                sock.connect((host, port))
                return True
            except Exception:
                time.sleep(0.5)
    return False


def main():
    python_exe = sys.executable
    print('Usando intérprete:', python_exe)

    code = run_collector(python_exe)
    if code != 0:
        print(f'Coletor terminou com código {code}. Verifique erros e tente novamente.')
        # Decide to continue or not — we will abort to be safe
        sys.exit(code)

    server_proc = start_main_server(python_exe)

    try:
        print(f'Aguardando servidor em {HOST}:{PORT}...')
        ok = wait_for_port(HOST, PORT, timeout=25)
        if not ok:
            print('Servidor não respondeu dentro do timeout. Veja logs do processo.')
            print('PID do servidor:', server_proc.pid)
            sys.exit(3)

        print('Servidor ativo — abrindo navegador...')
        webbrowser.open(URL)

        print('Pressione Ctrl+C para encerrar o servidor.')
        # Wait for server process; forward signals
        while True:
            time.sleep(1)
            if server_proc.poll() is not None:
                print('Servidor finalizou (codigo', server_proc.returncode, ').')
                break

    except KeyboardInterrupt:
        print('\nInterrompido pelo usuário — finalizando servidor...')
    finally:
        try:
            if server_proc.poll() is None:
                print('Terminando processo do servidor (PID', server_proc.pid, ')')
                # On Windows, terminate is sufficient
                server_proc.terminate()
                # wait a bit
                time.sleep(1)
                if server_proc.poll() is None:
                    server_proc.kill()
        except Exception as e:
            print('Erro ao encerrar servidor:', e)

if __name__ == '__main__':
    main()
