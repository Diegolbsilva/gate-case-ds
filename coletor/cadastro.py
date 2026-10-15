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
- "cliques" (13/10/2026): lista de textos para clicar a partir da capa do portal, em ordem. Para portais
  que nao mudam o endereco ao navegar (Webrun de Caxias): a pagina do recurso so existe depois de 3 cliques.
  Clica no elemento VISIVEL com exatamente aquele texto, espera a tela estabilizar e confere se mudou;
  se um clique falhar ou nao mudar nada, para e registra. No fim, salva HTML e print da tela (o print
  guarda tambem infograficos em imagem, que o LLM pode ler).
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
import hashlib
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
def clicar_texto(pagina, texto):
    """Clica no primeiro elemento visivel com exatamente este texto (em qualquer moldura).
    Devolve None se deu certo, ou o motivo da falha."""
    for frame in pagina.frames:
        alvos = frame.get_by_text(texto, exact=True)
        for i in range(min(alvos.count(), 10)):
            if alvos.nth(i).is_visible():
                antes = texto_da_pagina(pagina)
                alvos.nth(i).click(timeout=10000)
                pagina.wait_for_timeout(3000)
                esperar_estabilizar(pagina)
                return None if texto_da_pagina(pagina) != antes else "clique sem efeito"
    return "texto nao encontrado visivel na tela"


# Imagens de conteudo (infografico): minimo de 600 px de largura e 400 de altura no tamanho original.
# Icones e logos ficam de fora. Motivo: em Caxias o recurso e um infografico dentro de uma caixa com rolagem
# propria; o print da pagina inteira corta a imagem no meio. Baixando o arquivo, o LLM le a imagem inteira.
# So conta imagem que NAO estava na tela antes dos cliques: a que ja estava e do layout do portal (banner,
# logo de menu). Caso real, execucao 20: o icone "Boletim Oficial" e 2 banners vinham nos dois caminhos.
JS_IMAGENS_GRANDES = """() => [...document.images]
    .filter(i => i.naturalWidth >= 600 && i.naturalHeight >= 400)
    .map(i => i.currentSrc || i.src)"""
MAX_IMAGENS = 5


def imagens_grandes(pagina):
    """Enderecos das imagens grandes em todas as molduras da pagina, sem repeticao."""
    srcs = []
    for frame in pagina.frames:
        try:
            srcs += frame.evaluate(JS_IMAGENS_GRANDES)
        except Exception:
            pass
    return list(dict.fromkeys(srcs))


MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro",
         "Novembro", "Dezembro"]

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=RAIZ / "config" / "entidades.yaml")
parser.add_argument("--criterios", default=RAIZ / "config" / "criterios.yaml")
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--entidade", help="rodar so para uma entidade (id do cadastro)")
parser.add_argument("--execucao", type=int,
                    help="usar uma execucao ja aberta (coletor.executar); sem isso, abre e fecha a propria")
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
if args.execucao:
    execucao_id = args.execucao
else:
    execucao_id = banco.iniciar_execucao(con, origem="manual", versao_checklist=cfg_criterios["versao_checklist"],
                                         versao_codigo=versao_codigo, observacao="Coleta das paginas do cadastro por criterio")
print(f"Usando a execucao {execucao_id}" if args.execucao else f"Execucao {execucao_id} iniciada (codigo {versao_codigo})")

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
            for n, cliques in enumerate(regra.get("cliques", []), start=1):
                papel = f"cadastro_{codigo}_cliques{n}"
                pagina = contexto.new_page()
                resposta, ocorrencias = abrir_pagina(pagina, entidade["portal"], coleta["tentativas"], espera_js_ms=ESPERA_JS_MS)
                for o in ocorrencias:
                    banco.registrar_ocorrencia(con, execucao_id, eid, o, criterio_id)
                falha = "portal indisponivel" if resposta is None else None
                if resposta is not None:
                    fechar_popups(pagina)
                imagens_do_layout = set(imagens_grandes(pagina)) if resposta is not None else set()
                for texto in ([] if falha else cliques):
                    falha = clicar_texto(pagina, texto)
                    if falha:
                        falha = f"'{texto}': {falha}"
                        break
                if falha:
                    banco.registrar_ocorrencia(con, execucao_id, eid, {
                        "url": entidade["portal"], "tipo": "layout_inesperado", "tentativa": 1, "ocorrido_em": banco.agora(),
                        "mensagem": f"Caminho de cliques {n} interrompido em {falha}"}, criterio_id)
                    print(f"  {codigo:5} cliques {n}: FALHOU em {falha}")
                else:
                    for artefato in salvar_pagina(pagina, resposta, entidade["portal"], pasta, papel.replace(".", "_"), papel):
                        banco.registrar_artefato(con, execucao_id, eid, artefato, criterio_id)
                    print(f"  {codigo:5} cliques {n}: ok ({' > '.join(cliques)})")
                    # imagens grandes que surgiram com os cliques, baixadas em resolucao original (sessao do navegador)
                    novas = [s for s in imagens_grandes(pagina) if s not in imagens_do_layout]
                    for m, src in enumerate(novas[:MAX_IMAGENS], start=1):
                        try:
                            resp_img = contexto.request.get(src, timeout=60000)
                        except Exception as erro:
                            print(f"  {codigo:5} cliques {n}: imagem {m} FALHOU ({str(erro)[:80]})")
                            continue
                        corpo = resp_img.body() if resp_img.ok else b""
                        extensao = "png" if corpo.startswith(b"\x89PNG") else ("jpg" if corpo.startswith(b"\xff\xd8") else None)
                        if not extensao:
                            continue  # nao e PNG nem JPEG (ou falhou): ignora
                        nome = f"{papel.replace('.', '_')}_imagem{m}.{extensao}"
                        (pasta / nome).write_bytes(corpo)
                        banco.registrar_artefato(con, execucao_id, eid, {
                            "papel": f"{papel}_imagem", "url": src, "url_final": src,
                            "tipo": "png" if extensao == "png" else "outro", "caminho": str(pasta / nome),
                            "hash_sha256": hashlib.sha256(corpo).hexdigest(), "tamanho_bytes": len(corpo),
                            "status_http": resp_img.status, "coletado_em": banco.agora()}, criterio_id)
                        print(f"  {codigo:5} cliques {n}: imagem {m} salva ({len(corpo) // 1024} KB)")
                for aberta in list(contexto.pages):
                    aberta.close()
            urls = regra.get("url") or []
            urls = urls if isinstance(urls, list) else [urls]
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

if not args.execucao:
    banco.finalizar_execucao(con, execucao_id)
print(f"\n{'Etapa terminada' if args.execucao else f'Execucao {execucao_id} concluida'}. "
      f"Arquivos em {pasta_dados / 'execucoes' / str(execucao_id)}")
con.close()
