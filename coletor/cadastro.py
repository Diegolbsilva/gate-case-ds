"""Coleta as paginas anotadas por criterio no cadastro (config/entidades.yaml), para cada entidade.

Por que existe: e o passo de reserva da avaliacao em cascata (decidido em 12/10/2026). Para cada criterio,
a avaliacao procura a evidencia nas paginas da descoberta e, se nao achar, nestas paginas do cadastro.
Tambem cobre o que a descoberta nao procura (16.2, paginas extras do 15.4) e serve de gabarito para medir
a descoberta (pagina achada sozinha x pagina anotada a mao).

O que coleta:
- metodo 'pagina' ou 'navegador' com URL: abre a URL e salva HTML + print, ligados ao criterio.
- metodo 'api': nao coleta aqui (coletor/apis.py faz isso).
- caminho descrito em texto (ex.: "Portal > Pedido de Informacao > ..."), sem URL: nao coleta e avisa.
  Nesses casos a evidencia vem das paginas da descoberta.
A mesma URL usada por mais de um criterio e aberta uma vez so; o arquivo e ligado a cada criterio.
{ano} na URL vira o ano corrente (exercicio avaliado).

Pesquisa (decidido em 12/10/2026, depois da execucao 8): em paginas de consulta de dados (criterios 4.1, 4.6 e
12.1), se houver um botao visivel "Pesquisar", "Consultar" ou "Buscar", o coletor clica uma vez e salva tambem o
resultado. Antes, se houver um seletor de mes vazio, escolhe o mes corrente. Nunca clica se a pagina tiver
reCAPTCHA e nunca em paginas do e-SIC (15.4), para nao enviar formulario. Nao faz download.
Motivo: em Japeri (RGF, GeoSiap) e Itaboraí (despesas, Supernova) a tabela so aparece depois do Pesquisar.

Uso, na raiz do projeto, com o ambiente ativo:
    python -m coletor.cadastro [--entidade id]
"""
import argparse
import re
import subprocess
from datetime import date
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright

from coletor import banco
from coletor.navegador import abrir_pagina, esperar_estabilizar, fechar_popups, salvar_pagina, texto_da_pagina

RAIZ = Path(__file__).resolve().parent.parent
ESPERA_JS_MS = 6000  # sistemas inteiros em JavaScript (Contas Rio, Betha) demoram mais que uma pagina comum
CRITERIOS_COM_PESQUISA = ("4.1", "4.6", "12.1")   # consultas de dados; nunca 15.4 (formulario do e-SIC)
# \W* nas pontas: o nome do botao pode trazer o caractere do icone (ex.: Itaboraí, icone de lupa "fa-search"
# desenhado por CSS entra no nome acessivel do botao, e "^pesquisar$" nao achava o botao na execucao 11)
BOTAO_PESQUISA = re.compile(r"^\W*(pesquisar|consultar|buscar)\W*$", re.I)
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro",
         "Novembro", "Dezembro"]

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=RAIZ / "config" / "entidades.yaml")
parser.add_argument("--criterios", default=RAIZ / "config" / "criterios.yaml")
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--entidade", help="rodar so para uma entidade (id do cadastro)")
args = parser.parse_args()

cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
cfg_criterios = yaml.safe_load(Path(args.criterios).read_text(encoding="utf-8"))
coleta = cfg["coleta"]
entidades = [e for e in cfg["entidades"] if not args.entidade or e["id"] == args.entidade]
pasta_dados = Path(args.dados)
ano = date.today().year

con = banco.conectar(pasta_dados / "gate.db")
banco.sincronizar_entidades(con, cfg["entidades"])
ids_criterios = banco.sincronizar_criterios(con, cfg_criterios)
try:
    versao_codigo = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                   cwd=RAIZ).stdout.strip() or None
except FileNotFoundError:
    versao_codigo = None
execucao_id = banco.iniciar_execucao(con, origem="manual", versao_checklist=cfg_criterios["versao_checklist"],
                                     versao_codigo=versao_codigo, observacao="Coleta das paginas do cadastro por criterio")
print(f"Execucao {execucao_id} iniciada (codigo {versao_codigo})")

with sync_playwright() as p:
    navegador = p.chromium.launch()
    contexto = navegador.new_context(viewport={"width": coleta["janela"][0], "height": coleta["janela"][1]},
                                     user_agent=coleta["user_agent"])
    for entidade in entidades:
        eid = entidade["id"]
        pasta = pasta_dados / "execucoes" / str(execucao_id) / eid
        ja_salvas = {}  # url -> artefatos ja salvos nesta entidade (mesma URL em varios criterios)
        print(f"\n{eid}")
        for codigo, regra in entidade.get("criterios", {}).items():
            criterio_id = ids_criterios.get(codigo)
            if regra["metodo"] == "api":
                print(f"  {codigo:5} api: coletado por coletor.apis")
                continue
            urls = regra["url"] if isinstance(regra["url"], list) else [regra["url"]]
            for n, url in enumerate(urls, start=1):
                if not url.startswith("http"):
                    print(f"  {codigo:5} {n}. sem URL (caminho descrito: '{url[:60]}'): evidencia vem da descoberta")
                    continue
                url = url.replace("{ano}", str(ano))
                papel = f"cadastro_{codigo}_{n}"
                if url in ja_salvas:
                    for artefato in ja_salvas[url]:
                        banco.registrar_artefato(con, execucao_id, eid, dict(artefato, papel=papel), criterio_id)
                    print(f"  {codigo:5} {n}. mesma pagina ja salva, ligada tambem a este criterio: {url}")
                    continue
                pagina = contexto.new_page()
                resposta, ocorrencias = abrir_pagina(pagina, url, coleta["tentativas"], espera_js_ms=ESPERA_JS_MS)
                for o in ocorrencias:
                    banco.registrar_ocorrencia(con, execucao_id, eid, o, criterio_id)
                if resposta is None:
                    print(f"  {codigo:5} {n}. INDISPONIVEL ({ocorrencias[-1]['tipo']}: {ocorrencias[-1]['mensagem']})")
                else:
                    fechar_popups(pagina)
                    artefatos = salvar_pagina(pagina, resposta, url, pasta, papel.replace(".", "_"), papel)
                    aviso = f" ({len(ocorrencias)} falha(s) antes)" if ocorrencias else ""
                    print(f"  {codigo:5} {n}. ok, HTTP {resposta.status} -> {pagina.url}{aviso}")

                    # Pesquisa: so em consulta de dados, com botao visivel e sem captcha
                    botao = pagina.get_by_role("button", name=BOTAO_PESQUISA)
                    tem_botao = codigo in CRITERIOS_COM_PESQUISA and botao.count() > 0 and botao.first.is_visible()
                    if codigo in CRITERIOS_COM_PESQUISA and not tem_botao:
                        nomes = [t.strip()[:20] for t in pagina.get_by_role("button").all_inner_texts() if t.strip()][:8]
                        print(f"  {codigo:5} {n}. sem botao de pesquisa visivel (botoes na pagina: {nomes})")
                    if tem_botao and "recaptcha" in pagina.content().lower():
                        print(f"  {codigo:5} {n}. tem botao de pesquisa, mas a pagina tem reCAPTCHA: nao clica")
                    elif tem_botao:
                        mes = pagina.evaluate("""() => {
                            const s = [...document.querySelectorAll('select')].find(s =>
                                [...s.options].some(o => /janeiro/i.test(o.text)) &&
                                [...s.options].some(o => /dezembro/i.test(o.text)));
                            if (!s || /janeiro|fevereiro|mar|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro/i
                                .test(s.options[s.selectedIndex]?.text || '')) return null;
                            return s.id || s.name || null; }""")
                        if mes:
                            pagina.locator(f"select#{mes}, select[name='{mes}']").first.select_option(
                                label=MESES[date.today().month - 1], force=True)
                            pagina.wait_for_timeout(2000)
                        antes = texto_da_pagina(pagina)
                        botao.first.click(timeout=10000)
                        pagina.wait_for_timeout(3000)
                        esperar_estabilizar(pagina)
                        if texto_da_pagina(pagina) == antes:
                            banco.registrar_ocorrencia(con, execucao_id, eid, {
                                "url": pagina.url, "tipo": "layout_inesperado", "tentativa": 1, "ocorrido_em": banco.agora(),
                                "mensagem": "Pesquisar sem efeito: a pagina nao mudou"}, criterio_id)
                            print(f"  {codigo:5} {n}. pesquisar: SEM EFEITO")
                        else:
                            artefatos += salvar_pagina(pagina, None, url, pasta, papel.replace(".", "_") + "_pesquisa",
                                                       papel + "_pesquisa")
                            extra = f", mes {MESES[date.today().month - 1]}" if mes else ""
                            print(f"  {codigo:5} {n}. pesquisar: ok{extra}")
                    for artefato in artefatos:
                        banco.registrar_artefato(con, execucao_id, eid, artefato, criterio_id)
                    ja_salvas[url] = artefatos
                for aberta in list(contexto.pages):
                    aberta.close()
    navegador.close()

banco.finalizar_execucao(con, execucao_id)
print(f"\nExecucao {execucao_id} concluida. Arquivos em {pasta_dados / 'execucoes' / str(execucao_id)}")
con.close()
