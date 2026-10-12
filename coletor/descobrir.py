"""Descoberta automatica, partindo SO do site oficial de cada entidade.

Passo 1: na capa do site, acha o link do portal da transparencia (e mede se esta visivel e se precisa rolar: 1.2).
Passo 2: na capa do portal, para cada alvo (despesa, rgf, esic), clica no melhor texto e, se a pagina
seguinte tiver um texto ainda melhor, clica de novo (ate 2 cliques).
Cada pagina alcancada e salva (HTML + print) e o caminho fica na tabela 'descobertas'.
Se a descoberta do portal falhar, usa o portal do cadastro e registra origem 'cadastro'.

Uso, na raiz do projeto, com o ambiente ativo:
    python -m coletor.descobrir
"""
import argparse
import subprocess
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

from coletor import banco
from coletor.descoberta import extrair_candidatos, melhores
from coletor.navegador import abrir_pagina, examinar_elemento, fechar_popups, html_dos_frames, salvar_pagina, seguir

RAIZ = Path(__file__).resolve().parent.parent
ALVOS = ["despesa", "rgf", "esic"]
NOTA_MINIMA_SEGUNDO_CLIQUE = 6

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=RAIZ / "config" / "entidades.yaml")
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--entidade", help="rodar so para uma entidade (id do cadastro)")
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
execucao_id = banco.iniciar_execucao(con, origem="manual", versao_checklist="v1-2026-10",
                                     versao_codigo=versao_codigo, observacao="Descoberta automatica")
print(f"Execucao {execucao_id} iniciada (codigo {versao_codigo})")


def registrar_pagina(pagina, papel, entidade_id):
    """Salva a pagina alcancada e devolve o id do artefato HTML principal."""
    pasta = pasta_dados / "execucoes" / str(execucao_id) / entidade_id
    ids = [banco.registrar_artefato(con, execucao_id, entidade_id, a)
           for a in salvar_pagina(pagina, None, pagina.url, pasta, papel, papel)]
    return ids[0]


def candidatos_da_pagina(pagina):
    return [c for i, html, url in html_dos_frames(pagina) for c in extrair_candidatos(html, url, frame=i)]


with sync_playwright() as p:
    navegador = p.chromium.launch()
    contexto = navegador.new_context(viewport={"width": coleta["janela"][0], "height": coleta["janela"][1]},
                                     user_agent=coleta["user_agent"])
    for entidade in entidades:
        eid = entidade["id"]
        print(f"\n{eid}")

        # Passo 1: site oficial -> portal
        portal_url, origem_inicio = entidade["portal"], "cadastro"
        capa = contexto.new_page()
        resposta, ocorrencias = abrir_pagina(capa, entidade["site_oficial"], coleta["tentativas"])
        for o in ocorrencias:
            banco.registrar_ocorrencia(con, execucao_id, eid, o)
        escolhido = None
        if resposta is not None:
            fechar_popups(capa)
            escolhidos = melhores(candidatos_da_pagina(capa), "portal", quantos=1)
            escolhido = escolhidos[0] if escolhidos else None
        if escolhido is None:
            banco.registrar_descoberta(con, execucao_id, eid, {
                "alvo": "portal", "passo": 1, "url_origem": entidade["site_oficial"], "origem_inicio": "cadastro",
                "sucesso": 0, "observacao": "Link do portal nao encontrado na capa do site; usado o cadastro"})
            print(f"  portal   NAO ACHADO, usando cadastro: {portal_url}")
        else:
            exame = examinar_elemento(capa, escolhido)
            destino, modo, ocorrencias = seguir(contexto, capa, escolhido, coleta["tentativas"])
            for o in ocorrencias:
                banco.registrar_ocorrencia(con, execucao_id, eid, o)
            artefato_id = registrar_pagina(destino, "descoberta_portal", eid) if destino else None
            if destino:
                portal_url, origem_inicio = destino.url, "descoberta"
            banco.registrar_descoberta(con, execucao_id, eid, {
                "alvo": "portal", "passo": 1, "texto_clicado": escolhido["texto"], "nota": escolhido["nota"],
                "url_origem": capa.url, "url_destino": destino.url if destino else None, "modo": modo,
                "visivel_sem_interacao": exame["visivel"], "precisou_rolar": exame["precisa_rolar"],
                "origem_inicio": "descoberta", "sucesso": int(destino is not None), "artefato_id": artefato_id})
            print(f"  portal   '{escolhido['texto'][:45]}' (nota {escolhido['nota']}, visivel={exame['visivel']}, "
                  f"rolar={exame['precisa_rolar']}) -> {destino.url if destino else 'FALHOU'}")
        for aberta in list(contexto.pages):
            aberta.close()

        # Passo 2: portal -> cada alvo, ate 2 cliques
        for alvo in ALVOS:
            atual = contexto.new_page()
            resposta, ocorrencias = abrir_pagina(atual, portal_url, coleta["tentativas"])
            for o in ocorrencias:
                banco.registrar_ocorrencia(con, execucao_id, eid, o)
            if resposta is None:
                print(f"  {alvo:8} portal indisponivel")
                for aberta in list(contexto.pages):
                    aberta.close()
                continue
            fechar_popups(atual)
            clicados = []
            for passo in (1, 2):
                escolhidos = melhores(candidatos_da_pagina(atual), alvo, quantos=1, ignorar=clicados)
                if not escolhidos or (passo == 2 and escolhidos[0]["nota"] < NOTA_MINIMA_SEGUNDO_CLIQUE):
                    if passo == 1:
                        banco.registrar_descoberta(con, execucao_id, eid, {
                            "alvo": alvo, "passo": 1, "url_origem": atual.url, "origem_inicio": origem_inicio,
                            "sucesso": 0, "observacao": "Nenhum texto do dicionario encontrado"})
                        print(f"  {alvo:8} NAO ACHADO no portal")
                    break
                escolhido = escolhidos[0]
                exame = examinar_elemento(atual, escolhido)
                url_origem = atual.url
                destino, modo, ocorrencias = seguir(contexto, atual, escolhido, coleta["tentativas"])
                for o in ocorrencias:
                    banco.registrar_ocorrencia(con, execucao_id, eid, o)
                artefato_id = registrar_pagina(destino, f"descoberta_{alvo}_{passo}", eid) if destino else None
                banco.registrar_descoberta(con, execucao_id, eid, {
                    "alvo": alvo, "passo": passo, "texto_clicado": escolhido["texto"], "nota": escolhido["nota"],
                    "url_origem": url_origem, "url_destino": destino.url if destino else None, "modo": modo,
                    "visivel_sem_interacao": exame["visivel"], "precisou_rolar": exame["precisa_rolar"],
                    "origem_inicio": origem_inicio, "sucesso": int(destino is not None), "artefato_id": artefato_id})
                print(f"  {alvo:8} {passo}. '{escolhido['texto'][:45]}' (nota {escolhido['nota']}, {modo}) -> "
                      f"{destino.url if destino else 'FALHOU'}")
                if destino is None:
                    break
                clicados.append(escolhido["texto"])
                atual = destino
            for aberta in list(contexto.pages):
                aberta.close()
    navegador.close()

banco.finalizar_execucao(con, execucao_id)
print(f"\nExecucao {execucao_id} concluida. Arquivos em {pasta_dados / 'execucoes' / str(execucao_id)}")
con.close()
