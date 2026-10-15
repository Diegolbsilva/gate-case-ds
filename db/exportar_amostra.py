"""Exporta uma amostra publica do banco (amostra/gate.db) para quem clona o repositorio ver os resultados sem coletar.

O banco completo (dados/gate.db) e os arquivos brutos ficam fora do Git: paginas de despesa trazem nome e CPF de
credores. A amostra leva so as execucoes oficiais avaliadas, com:
- avaliacoes, evidencias (trechos), scores, descobertas, ocorrencias, metadados dos artefatos e respostas do LLM;
- CPF mascarado de novo em todo texto (defesa em profundidade: os trechos ja sao gravados mascarados);
- caminhos de arquivo relativos (execucoes/N/entidade/arquivo), sem a pasta do computador de quem coletou;
- nenhum arquivo bruto (HTML, print, PDF).
Depois de gravar, varre todas as colunas de texto. Se ainda houver algo com formato de CPF, apaga a amostra e para.

Uso, na raiz do projeto:  python db/exportar_amostra.py
A API e o dashboard usam a amostra quando dados/gate.db nao existe. As regras tambem leem a amostra
(ex.: python -m regras.validar --dados amostra), mas nao a reavaliam: os arquivos brutos nao vao junto.
"""
import re
import sqlite3
import sys
from pathlib import Path, PureWindowsPath

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from coletor import banco  # noqa: E402

ORIGEM = Path(sys.argv[1]) if len(sys.argv) > 1 else RAIZ / "dados" / "gate.db"      # para teste: outro banco
DESTINO = Path(sys.argv[2]) if len(sys.argv) > 2 else RAIZ / "amostra" / "gate.db"
CPF = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
COLUNAS_CAMINHO = {"caminho", "caminho_arquivo"}
# tabelas na ordem das chaves estrangeiras, com o filtro de cada uma (so as execucoes oficiais)
TABELAS = [
    ("entidades", "1"), ("entidade_urls", "1"), ("criterios", "1"), ("criterio_aplicabilidade", "1"),
    ("execucoes", "id IN oficiais"), ("artefatos", "execucao_id IN oficiais"),
    ("descobertas", "execucao_id IN oficiais"), ("ocorrencias", "execucao_id IN oficiais"),
    ("avaliacoes", "execucao_id IN oficiais"),
    ("evidencias", "avaliacao_id IN (SELECT id FROM o.avaliacoes WHERE execucao_id IN oficiais)"),
    ("scores", "execucao_id IN oficiais"), ("respostas_llm", "execucao_id IN oficiais"),
]


def mascarar(texto):
    return CPF.sub("***.***.***-**", texto) if isinstance(texto, str) else texto


def relativo(caminho):
    """C:\\Users\\...\\dados\\execucoes\\16\\japeri\\x.html -> execucoes/16/japeri/x.html"""
    if not isinstance(caminho, str) or "execucoes" not in caminho:
        return caminho
    partes = (PureWindowsPath(caminho) if "\\" in caminho else Path(caminho)).parts
    return "/".join(partes[partes.index("execucoes"):])


if not ORIGEM.exists():
    raise SystemExit(f"Banco nao encontrado: {ORIGEM}")
DESTINO.parent.mkdir(exist_ok=True)
if DESTINO.exists():
    DESTINO.unlink()
con = banco.conectar(DESTINO)  # cria as tabelas pelo db/schema.sql
con.create_function("mascarar", 1, mascarar)
con.create_function("relativo", 1, relativo)
# caminho simples (sem "file:...?mode=ro": no Windows o SQLite so aceita URI se a conexao foi aberta com uri=True).
# O banco de origem so e lido: nenhum comando abaixo escreve em "o".
con.execute("ATTACH DATABASE ? AS o", (str(ORIGEM),))
oficiais = ("(SELECT e.id FROM o.execucoes e WHERE e.status = 'concluida' AND e.observacao LIKE 'Execucao completa%' "
            "AND e.observacao NOT LIKE '%(so %' AND EXISTS (SELECT 1 FROM o.avaliacoes a WHERE a.execucao_id = e.id))")

for tabela, filtro in TABELAS:
    colunas = [(c[1], (c[2] or "").upper()) for c in con.execute(f"PRAGMA o.table_info({tabela})")]
    if not colunas:
        continue  # tabela que nao existe no banco de origem
    seletor = ", ".join(f"relativo({n})" if n in COLUNAS_CAMINHO else (f"mascarar({n})" if "TEXT" in t else n)
                        for n, t in colunas)
    nomes = ", ".join(n for n, _ in colunas)
    n = con.execute(f"INSERT INTO {tabela} ({nomes}) SELECT {seletor} FROM o.{tabela} "
                    f"WHERE {filtro.replace('oficiais', oficiais)}").rowcount
    print(f"  {tabela:24} {n} linha(s)")
con.commit()
con.execute("DETACH DATABASE o")

# varredura final: nenhum texto com formato de CPF
achados = []
for (tabela,) in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall():
    for coluna, tipo in [(c[1], (c[2] or "").upper()) for c in con.execute(f"PRAGMA table_info({tabela})")]:
        if "TEXT" in tipo:
            for (valor,) in con.execute(f"SELECT {coluna} FROM {tabela} WHERE {coluna} IS NOT NULL"):
                if CPF.search(valor):
                    achados.append(f"{tabela}.{coluna}")
con.execute("VACUUM")
con.close()
if achados:
    DESTINO.unlink()
    raise SystemExit(f"Amostra NAO gravada: texto com formato de CPF em {sorted(set(achados))}")
print(f"\nAmostra gravada em {DESTINO} ({DESTINO.stat().st_size // 1024} KB); varredura de CPF: nada encontrado")
