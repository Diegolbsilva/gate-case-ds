"""Descoberta automatica, partindo SO do site oficial de cada entidade.

Passo 1: na capa do site, acha o link do portal da transparencia (e mede se esta visivel e se precisa rolar: 1.2).
Passo 2: na capa do portal, para cada alvo (despesa, rgf, esic), clica no melhor texto. Segundo clique
(no maximo 2) so em texto que o primeiro clique REVELOU: o que ja estava visivel antes e irmao no menu,
nao um passo mais fundo (erro visto em Cachoeiras: foi de "Execucao Detalhada de Despesas" para
"... - Educacao"). Texto ja clicado tambem nunca e clicado de novo.
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
from coletor.descoberta import SELETOR_CLICAVEL, extrair_candidatos, generico, melhores
from coletor.navegador import abrir_pagina, examinar_elemento, fechar_popups, html_dos_frames, salvar_pagina, seguir, textos_visiveis

RAIZ = Path(__file__).resolve().parent.parent
ALVOS = ["despesa", "rgf", "esic"]
NOTA_MINIMA_SEGUNDO_CLIQUE = 6

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
                                         versao_codigo=versao_codigo, observacao="Descoberta automatica")
print(f"Usando a execucao {execucao_id}" if args.execucao else f"Execucao {execucao_id} iniciada (codigo {versao_codigo})")


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
        portal_url, origem_inicio = entidade.get("portal"), "cadastro"  # portal no cadastro e opcional
        capa = contexto.new_page()
        resposta, ocorrencias = abrir_pagina(capa, entidade["site_oficial"], coleta["tentativas"])
        for o in ocorrencias:
            banco.registrar_ocorrencia(con, execucao_id, eid, o)
        escolhido = None
        if resposta is not None:
            fechar_popups(capa)
            escolhidos = melhores(candidatos_da_pagina(capa), "portal", quantos=1,
                                  visiveis=textos_visiveis(capa, SELETOR_CLICAVEL))
            escolhido = escolhidos[0] if escolhidos else None
        if escolhido is None:
            banco.registrar_descoberta(con, execucao_id, eid, {
                "alvo": "portal", "passo": 1, "url_origem": entidade["site_oficial"], "origem_inicio": "cadastro",
                "sucesso": 0, "observacao": "Link do portal nao encontrado na capa do site; usado o cadastro"
                                            if portal_url else "Link do portal nao encontrado e sem portal no cadastro"})
            print(f"  portal   NAO ACHADO" + (f", usando cadastro: {portal_url}" if portal_url else ""))
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

        if not portal_url:
            print("  sem portal (nao achado no site e nao anotado no cadastro): despesa, rgf e esic ficam sem pagina")
            continue

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
            ignorar = []  # passo 2: textos ja clicados + textos visiveis antes do primeiro clique
            for passo in (1, 2):
                visiveis = textos_visiveis(atual, SELETOR_CLICAVEL)
                escolhidos = melhores(candidatos_da_pagina(atual), alvo, quantos=1, ignorar=ignorar, visiveis=visiveis)
                if not escolhidos or (passo == 2 and escolhidos[0]["nota"] < NOTA_MINIMA_SEGUNDO_CLIQUE):
                    if passo == 2:
                        print(f"  {alvo:8} 2. nenhum texto novo revelado pelo 1o clique: fica no 1o")
                    if passo == 1:
                        banco.registrar_descoberta(con, execucao_id, eid, {
                            "alvo": alvo, "passo": 1, "url_origem": atual.url, "origem_inicio": origem_inicio,
                            "sucesso": 0, "observacao": "Nenhum texto do dicionario encontrado"})
                        print(f"  {alvo:8} NAO ACHADO no portal")
                    break
                escolhido = escolhidos[0]
                exame = examinar_elemento(atual, escolhido)
                url_origem = atual.url
                if passo == 1:
                    ignorar += visiveis
                destino, modo, ocorrencias = seguir(contexto, atual, escolhido, coleta["tentativas"])
                for o in ocorrencias:
                    banco.registrar_ocorrencia(con, execucao_id, eid, o)
                artefato_id = registrar_pagina(destino, f"descoberta_{alvo}_{passo}", eid) if destino else None
                banco.registrar_descoberta(con, execucao_id, eid, {
                    "alvo": alvo, "passo": passo, "texto_clicado": escolhido["rotulo"] if generico(escolhido) else escolhido["texto"], "nota": escolhido["nota"],
                    "url_origem": url_origem, "url_destino": destino.url if destino else None, "modo": modo,
                    "visivel_sem_interacao": exame["visivel"], "precisou_rolar": exame["precisa_rolar"],
                    "origem_inicio": origem_inicio, "sucesso": int(destino is not None), "artefato_id": artefato_id})
                print(f"  {alvo:8} {passo}. '{(escolhido['rotulo'] if generico(escolhido) else escolhido['texto'])[:45]}' (nota {escolhido['nota']}, {modo}) -> "
                      f"{destino.url if destino else 'FALHOU (' + str(modo) + ')'}")
                if destino is None:
                    break
                ignorar += [escolhido["rotulo"]] if generico(escolhido) else [escolhido["texto"], escolhido["rotulo"]]
                atual = destino
            for aberta in list(contexto.pages):
                aberta.close()
    navegador.close()

if not args.execucao:
    banco.finalizar_execucao(con, execucao_id)
print(f"\n{'Etapa terminada' if args.execucao else f'Execucao {execucao_id} concluida'}. "
      f"Arquivos em {pasta_dados / 'execucoes' / str(execucao_id)}")
con.close()
