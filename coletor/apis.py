"""Detecta o fornecedor de cada portal e, quando ha adaptador, coleta pela API do fornecedor.

Portal de cada entidade: o descoberto na ultima execucao de descoberta (tabela descobertas);
se nao houver, o do cadastro. HTML da capa do portal: baixado na hora.
Tudo o que vem da API e salvo como JSON e registrado na tabela artefatos.

Uso, na raiz do projeto, com o ambiente ativo:
    python -m coletor.apis
"""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import requests
import yaml

from coletor import banco
from coletor.fornecedores import ADAPTADORES, COM_ADAPTADOR, detectar

RAIZ = Path(__file__).resolve().parent.parent

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=RAIZ / "config" / "entidades.yaml")
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--entidade", help="rodar so para uma entidade (id do cadastro)")
parser.add_argument("--execucao", type=int,
                    help="usar uma execucao ja aberta (coletor.executar); sem isso, abre e fecha a propria")
args = parser.parse_args()

cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
coleta = cfg["coleta"]
entidades = [e for e in cfg["entidades"] if not args.entidade or e["id"] == args.entidade]
pasta_dados = Path(args.dados)

con = banco.conectar(pasta_dados / "gate.db")
banco.sincronizar_entidades(con, cfg["entidades"])
try:
    versao_codigo = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                   cwd=RAIZ).stdout.strip() or None
except FileNotFoundError:
    versao_codigo = None
if args.execucao:
    execucao_id = args.execucao
else:
    execucao_id = banco.iniciar_execucao(con, origem="manual", versao_checklist="v1-2026-10",
                                         versao_codigo=versao_codigo, observacao="Deteccao de fornecedor e APIs")
print(f"Usando a execucao {execucao_id}" if args.execucao else f"Execucao {execucao_id} iniciada (codigo {versao_codigo})")

sessao = requests.Session()
sessao.headers["User-Agent"] = coleta["user_agent"]


def salvar_json(entidade_id, nome, conteudo, url, papel):
    pasta = pasta_dados / "execucoes" / str(execucao_id) / entidade_id
    pasta.mkdir(parents=True, exist_ok=True)
    bruto = json.dumps(conteudo, ensure_ascii=False, indent=1).encode("utf-8")
    caminho = pasta / f"{nome}.json"
    caminho.write_bytes(bruto)
    return banco.registrar_artefato(con, execucao_id, entidade_id, {
        "papel": papel, "url": url, "url_final": url, "tipo": "json", "caminho": str(caminho),
        "hash_sha256": hashlib.sha256(bruto).hexdigest(), "tamanho_bytes": len(bruto),
        "status_http": None, "coletado_em": banco.agora()})


for entidade in entidades:
    eid = entidade["id"]
    linha = con.execute(
        "SELECT url_destino FROM descobertas WHERE entidade_id = ? AND alvo = 'portal' AND sucesso = 1 "
        "ORDER BY id DESC LIMIT 1", (eid,)).fetchone()
    url_portal, origem = (linha[0], "descoberta") if linha else (entidade.get("portal"), "cadastro")
    if not url_portal:
        print(f"\n{eid}: sem portal (nao achado pela descoberta e nao anotado no cadastro): pulado")
        continue
    try:
        resposta = sessao.get(url_portal, timeout=60)
        html = resposta.text
    except requests.RequestException as erro:
        html = ""
        banco.registrar_ocorrencia(con, execucao_id, eid, {"url": url_portal, "tipo": "erro_http", "tentativa": 1,
                                                          "mensagem": str(erro)[:300], "ocorrido_em": banco.agora()})
    fornecedores = detectar(url_portal, html)
    salvar_json(eid, "deteccao_fornecedor", {"url_portal": url_portal, "origem_url_portal": origem,
                                             "fornecedores": [{"nome": n, "evidencia": e} for n, e in fornecedores]},
                url_portal, "deteccao_fornecedor")
    nomes = [n for n, _ in fornecedores]
    print(f"\n{eid}: portal ({origem}) {url_portal}")
    print(f"  fornecedor(es): {', '.join(f'{n} [{e}]' for n, e in fornecedores) or 'nenhum conhecido'}")

    com_adaptador = [n for n in nomes if n in COM_ADAPTADOR]
    if not com_adaptador:
        print("  sem adaptador: segue pela descoberta generica")
        continue
    for nome in com_adaptador:
        arquivos, ocorrencias, resumo = ADAPTADORES[nome](sessao, url_portal, coleta["tentativas"])
        for o in ocorrencias:
            banco.registrar_ocorrencia(con, execucao_id, eid, o)
        for arquivo, conteudo, url in arquivos:
            salvar_json(eid, arquivo, conteudo, url, f"api_{nome}")
        salvar_json(eid, f"resumo_{nome}", resumo, url_portal, f"resumo_{nome}")
        print(f"  adaptador {nome}: {json.dumps(resumo, ensure_ascii=False)}")

if not args.execucao:
    banco.finalizar_execucao(con, execucao_id)
print(f"\n{'Etapa terminada' if args.execucao else f'Execucao {execucao_id} concluida'}. "
      f"Arquivos em {pasta_dados / 'execucoes' / str(execucao_id)}")
con.close()
