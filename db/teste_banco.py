"""Cria um banco de teste, carrega os dados reais do gabarito e responde as perguntas da secao 7.

Uso: python teste_banco.py   (na mesma pasta de schema.sql, exemplo_dados.sql e consultas_exemplo.sql)
Nao precisa instalar nada: o sqlite3 vem com o Python.
"""
import sqlite3
from pathlib import Path

pasta = Path(__file__).parent
banco = pasta / "teste.db"
banco.unlink(missing_ok=True)

con = sqlite3.connect(banco)
con.execute("PRAGMA foreign_keys = ON")
con.executescript((pasta / "schema.sql").read_text(encoding="utf-8"))
con.executescript((pasta / "exemplo_dados.sql").read_text(encoding="utf-8"))

for bloco in (pasta / "consultas_exemplo.sql").read_text(encoding="utf-8").split("-- == ")[1:]:
    titulo, sql = bloco.split("\n", 1)
    cur = con.execute(sql)
    colunas = [d[0] for d in cur.description]
    linhas = cur.fetchall()
    larguras = [max(len(str(x)) for x in [col] + [l[i] for l in linhas]) for i, col in enumerate(colunas)]
    print(f"\n== {titulo}")
    print("  ".join(col.ljust(w) for col, w in zip(colunas, larguras)))
    for l in linhas:
        print("  ".join(str(x).ljust(w) for x, w in zip(l, larguras)))

con.close()
