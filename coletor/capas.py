"""Coleta as capas (site oficial e portal) de todas as entidades do cadastro.

Uso, na raiz do projeto, com o ambiente ativo:
    python -m coletor.capas

Saida:
    dados/gate.db                                  banco com execucao, artefatos e ocorrencias
    dados/execucoes/<id>/<entidade>/capa_*.html    HTML renderizado
    dados/execucoes/<id>/<entidade>/capa_*.png     print da pagina inteira
"""
import argparse
import subprocess
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

from coletor import banco
from coletor.navegador import abrir_pagina, salvar_pagina

RAIZ = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=RAIZ / "config" / "entidades.yaml")
parser.add_argument("--dados", default=RAIZ / "dados")
args = parser.parse_args()

cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
coleta = cfg["coleta"]
pasta_dados = Path(args.dados)

con = banco.conectar(pasta_dados / "gate.db")
banco.sincronizar_entidades(con, cfg["entidades"])

try:
    versao_codigo = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                   cwd=RAIZ).stdout.strip() or None
except FileNotFoundError:
    versao_codigo = None
execucao_id = banco.iniciar_execucao(con, origem="manual", versao_checklist="v1-2026-10",
                                     versao_codigo=versao_codigo, observacao="Coleta das capas")
print(f"Execucao {execucao_id} iniciada (codigo {versao_codigo})")

with sync_playwright() as p:
    navegador = p.chromium.launch()
    contexto = navegador.new_context(
        viewport={"width": coleta["janela"][0], "height": coleta["janela"][1]},
        user_agent=coleta["user_agent"],
    )
    for entidade in cfg["entidades"]:
        for papel, url in [("capa_site", entidade["site_oficial"]), ("capa_portal", entidade["portal"])]:
            pagina = contexto.new_page()
            resposta, ocorrencias = abrir_pagina(pagina, url, coleta["tentativas"])
            for ocorrencia in ocorrencias:
                banco.registrar_ocorrencia(con, execucao_id, entidade["id"], ocorrencia)
            if resposta is None:
                print(f"  {entidade['id']:22} {papel:12} INDISPONIVEL ({ocorrencias[-1]['tipo']}: {ocorrencias[-1]['mensagem']})")
            else:
                pasta = pasta_dados / "execucoes" / str(execucao_id) / entidade["id"]
                for artefato in salvar_pagina(pagina, resposta, url, pasta, papel, papel):
                    banco.registrar_artefato(con, execucao_id, entidade["id"], artefato)
                aviso = f" ({len(ocorrencias)} falha(s) antes)" if ocorrencias else ""
                print(f"  {entidade['id']:22} {papel:12} ok, HTTP {resposta.status}, final: {pagina.url}{aviso}")
            pagina.close()
    navegador.close()

banco.finalizar_execucao(con, execucao_id)
print(f"Execucao {execucao_id} concluida. Arquivos em {pasta_dados / 'execucoes' / str(execucao_id)}")
con.close()
