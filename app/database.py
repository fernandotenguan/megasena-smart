import sqlite3
import os

# Caminho do banco, que está na pasta raiz do projeto
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'megasena_db.sqlite3')
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'megasena_db.sqlite3')

def conectar():
    return sqlite3.connect(DB_PATH)

def listar_sorteios(limit=20):
    with conectar() as conn:
        cursor = conn.execute('SELECT Concurso, Data, Bola1, Bola2, Bola3, Bola4, Bola5, Bola6 FROM resultados_megasena ORDER BY Concurso DESC LIMIT ?', (limit,))
        return cursor.fetchall()

def buscar_sorteio(concurso_num):
    with conectar() as conn:
        cursor = conn.execute('SELECT Concurso, Data, Bola1, Bola2, Bola3, Bola4, Bola5, Bola6 FROM resultados_megasena WHERE Concurso=?', (concurso_num,))
        return cursor.fetchone()
