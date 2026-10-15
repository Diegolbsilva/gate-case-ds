"""Anexos do e-SIC (criterio 15.4): segue "Ver mais detalhes", baixa os PDFs e extrai o texto.

Por que existe: em alguns portais o texto que o 15.4 avalia (prazos, autoridade, recurso) nao esta na
pagina, e sim num PDF anexo dentro de uma janela de detalhe. Caso real: Itaborai, "Prazos de respostas do
SIC" > "Ver mais detalhes" > ANEXO 1 (PDF com texto selecionavel). Sem isso, o LLM do 15.4 nao teria o que ler.

Como funciona (decidido em 13/10/2026), sem abrir navegador:
1. Pega as paginas do e-SIC ja salvas nesta execucao: as do cadastro ligadas ao 15.4 e as da descoberta (alvo esic).
2. Procura nelas paginas de DETALHE: endereco dentro de onclick="popup('...')" ou link com o texto
   "ver mais detalhes" / "mais detalhes" / "saiba mais". Baixa cada uma (1 nivel so, sem seguir adiante).
3. Em todas essas paginas, procura links para PDF: <a href> ou endereco dentro de onclick (window.open,
   location.href) com .pdf no endereco; ou <a href> com texto "anexo", "download", "baixar" ou "arquivo".
   Depois de baixar, so aceita se o arquivo for mesmo um PDF (comeca com %PDF); senao, descarta.
4. Baixa cada PDF e extrai o texto (pypdf). Salva o PDF e o texto (.txt), com hash, ligados ao 15.4.
   PDF sem texto (digitalizado) fica registrado como ocorrencia: precisaria de OCR, que nao e feito aqui.

Limites, para nao sair baixando o portal inteiro:
- so paginas do e-SIC (15.4); PDFs de RGF e outros nao sao baixados (o 12.1 so precisa saber se o link existe);
- ate 5 PDFs por entidade e ate 15 MB por PDF;
- so do mesmo endereco da pagina ou dos dominios_permitidos da entidade (quando o cadastro tiver a lista).

Uso, na raiz do projeto, com o ambiente ativo:
    python -m coletor.anexos --execucao N      (normalmente chamado pelo coletor.executar)
"""
import argparse
import hashlib
import io
import re
import subprocess
from pathlib import Path, PureWindowsPath
from urllib.parse import urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from pypdf import PdfReader

from coletor import banco
from coletor.descoberta import normalizar

RAIZ = Path(__file__).resolve().parent.parent
MAX_PDFS_POR_ENTIDADE = 5
MAX_BYTES_PDF = 15 * 1024 * 1024
TEXTO_DETALHE = re.compile(r"ver mais detalhes|mais detalhes|saiba mais")
POPUP = re.compile(r"""popup\(\s*['"]([^'"]+)['"]""")
# endereco escrito dentro de um comando JavaScript no onclick: window.open('...'), location.href = '...'.
# Itaborai: o ANEXO 1 e um <div onclick="window.open('.../Prazos_Procedimentos....pdf','_blank')">, sem <a>.
URL_NO_ONCLICK = re.compile(r"""(?:window\.open\(|location(?:\.href)?\s*=)\s*['"]([^'"]+)['"]""")
TEXTO_ANEXO = re.compile(r"\banexo\b|download|baixar|arquivo")

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
criterio_15_4 = con.execute("SELECT id FROM criterios WHERE codigo = '15.4'").fetchone()
criterio_15_4 = criterio_15_4[0] if criterio_15_4 else None
if args.execucao:
    execucao_id = args.execucao
else:
    try:
        versao_codigo = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                                       cwd=RAIZ).stdout.strip() or None
    except FileNotFoundError:
        versao_codigo = None
    execucao_id = banco.iniciar_execucao(con, origem="manual", versao_checklist="v1-2026-10",
                                         versao_codigo=versao_codigo, observacao="Anexos do e-SIC")
print(f"Usando a execucao {execucao_id}" if args.execucao else f"Execucao {execucao_id} iniciada")

sessao = requests.Session()
sessao.headers["User-Agent"] = coleta["user_agent"]


def baixar(url, eid):
    """GET com novas tentativas. Devolve a resposta ou None (e registra a ocorrencia)."""
    for n in range(1, coleta["tentativas"] + 1):
        try:
            resposta = sessao.get(url, timeout=60, stream=True)
            if resposta.status_code < 400:
                return resposta
            mensagem, tipo = f"HTTP {resposta.status_code}", "erro_servidor" if resposta.status_code >= 500 else "erro_http"
        except requests.RequestException as erro:
            mensagem, tipo = str(erro)[:300], "timeout" if isinstance(erro, requests.Timeout) else "erro_http"
        banco.registrar_ocorrencia(con, execucao_id, eid, {"url": url, "tipo": tipo, "mensagem": mensagem, "tentativa": n,
                                                          "ocorrido_em": banco.agora()}, criterio_15_4)
    return None


def salvar(eid, nome, conteudo, url, tipo, papel):
    pasta = pasta_dados / "execucoes" / str(execucao_id) / eid
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / nome
    caminho.write_bytes(conteudo)
    banco.registrar_artefato(con, execucao_id, eid, {
        "papel": papel, "url": url, "url_final": url, "tipo": tipo, "caminho": str(caminho),
        "hash_sha256": hashlib.sha256(conteudo).hexdigest(), "tamanho_bytes": len(conteudo), "status_http": 200,
        "coletado_em": banco.agora()}, criterio_15_4)


def permitido(url, origem, permitidos):
    """PDF ou detalhe so do mesmo endereco da pagina de origem ou dos dominios_permitidos da entidade."""
    host = urlparse(url).hostname or ""
    return host == urlparse(origem).hostname or any(host == d or host.endswith("." + d) for d in permitidos)


def caminho_local(caminho):
    partes = (PureWindowsPath(caminho) if "\\" in caminho else Path(caminho)).parts
    return pasta_dados.joinpath(*partes[partes.index("execucoes"):])


for entidade in entidades:
    eid = entidade["id"]
    permitidos = set(entidade.get("dominios_permitidos") or [])
    paginas = con.execute(
        "SELECT url_final, url, caminho FROM artefatos WHERE execucao_id = ? AND entidade_id = ? AND tipo = 'html' "
        "AND (criterio_id = ? OR papel LIKE 'descoberta_esic%')", (execucao_id, eid, criterio_15_4)).fetchall()
    print(f"\n{eid}: {len(paginas)} pagina(s) do e-SIC salvas")

    # 2. paginas de detalhe (1 nivel) e 3. links para PDF
    htmls = []  # (url da pagina, html)
    for url_final, url, caminho in paginas:
        arquivo = caminho_local(caminho)
        if arquivo.exists():
            htmls.append((url_final or url, arquivo.read_text(encoding="utf-8")))
    detalhes = []
    for base, html in htmls:
        sopa = BeautifulSoup(html, "html.parser")
        candidatos = [urljoin(base, m) for m in POPUP.findall(html)]
        candidatos += [urljoin(base, a["href"]) for a in sopa.find_all("a", href=True)
                       if TEXTO_DETALHE.search(normalizar(a.get_text(" "))) and not a["href"].startswith(("#", "javascript"))]
        detalhes += [d for d in candidatos if permitido(d, base, permitidos)]
    detalhes = list(dict.fromkeys(detalhes))
    for n, url in enumerate(detalhes, start=1):
        resposta = baixar(url, eid)
        if resposta is None:
            print(f"  detalhe {url}: FALHOU")
            continue
        html = resposta.text
        salvar(eid, f"anexo_detalhe_{n}.html", html.encode("utf-8"), url, "html", "anexo_detalhe")
        htmls.append((url, html))
        print(f"  detalhe {n}: {url}")

    pdfs = []
    for base, html in htmls:
        sopa = BeautifulSoup(html, "html.parser")
        for a in sopa.find_all("a", href=True):
            alvo, rotulo = urljoin(base, a["href"]), re.sub(r"\s+", " ", a.get_text(" ", strip=True))[:80]
            if (".pdf" in urlparse(alvo).path.lower() or TEXTO_ANEXO.search(normalizar(rotulo))) \
                    and not a["href"].startswith(("#", "javascript", "mailto:")) and permitido(alvo, base, permitidos):
                pdfs.append((alvo, rotulo))
        for el in sopa.find_all(onclick=True):
            for achado in URL_NO_ONCLICK.findall(el["onclick"]):
                alvo, rotulo = urljoin(base, achado), re.sub(r"\s+", " ", el.get_text(" ", strip=True))[:80]
                if ".pdf" in urlparse(alvo).path.lower() and permitido(alvo, base, permitidos):
                    pdfs.append((alvo, rotulo))
    pdfs = list(dict.fromkeys(pdfs))
    if not pdfs:
        print("  nenhum PDF nas paginas do e-SIC")
    if len(pdfs) > MAX_PDFS_POR_ENTIDADE:
        print(f"  {len(pdfs)} PDFs encontrados; baixando so os {MAX_PDFS_POR_ENTIDADE} primeiros")

    # 4. baixa e extrai o texto (numeracao anexo_1, anexo_2... so dos que sao PDF de verdade)
    salvos, hashes_salvos = 0, set()
    for n, (url, rotulo) in enumerate(pdfs[:MAX_PDFS_POR_ENTIDADE], start=1):
        resposta = baixar(url, eid)
        if resposta is None:
            print(f"  pdf {n} '{rotulo}': FALHOU")
            continue
        conteudo = resposta.raw.read(MAX_BYTES_PDF + 1, decode_content=True)
        if len(conteudo) > MAX_BYTES_PDF:
            banco.registrar_ocorrencia(con, execucao_id, eid, {"url": url, "tipo": "outro", "tentativa": 1,
                                                              "mensagem": "PDF acima de 15 MB: nao baixado",
                                                              "ocorrido_em": banco.agora()}, criterio_15_4)
            print(f"  pdf {n} '{rotulo}': acima de 15 MB, ignorado")
            continue
        if not conteudo.startswith(b"%PDF"):
            print(f"  link {n} '{rotulo}': nao e PDF, descartado")
            continue  # link com texto "anexo"/"baixar" que leva a uma pagina comum
        hash_pdf = hashlib.sha256(conteudo).hexdigest()
        if hash_pdf in hashes_salvos:
            print(f"  pdf {n} '{rotulo}': mesmo arquivo de um PDF ja salvo, ignorado")
            continue  # Caxias: "Visualizar PDF" e "Baixar PDF" apontam para o mesmo documento
        hashes_salvos.add(hash_pdf)
        salvos += 1
        salvar(eid, f"anexo_{salvos}.pdf", conteudo, url, "pdf", "anexo_pdf")
        try:
            leitor = PdfReader(io.BytesIO(conteudo))
            paginas_texto = [p.extract_text() or "" for p in leitor.pages]
        except Exception as erro:  # PDF corrompido ou protegido: registra e segue
            paginas_texto = []
            banco.registrar_ocorrencia(con, execucao_id, eid, {"url": url, "tipo": "layout_inesperado", "tentativa": 1,
                                                              "mensagem": f"PDF ilegivel: {str(erro)[:200]}",
                                                              "ocorrido_em": banco.agora()}, criterio_15_4)
        texto = "\n\n".join(f"--- pagina {i} ---\n{t}" for i, t in enumerate(paginas_texto, start=1))
        if len(re.sub(r"\s|-+ pagina \d+ -+", "", texto)) < 50:
            banco.registrar_ocorrencia(con, execucao_id, eid, {"url": url, "tipo": "layout_inesperado", "tentativa": 1,
                                                              "mensagem": "PDF sem texto (digitalizado?): precisaria de OCR",
                                                              "ocorrido_em": banco.agora()}, criterio_15_4)
            print(f"  pdf {n} '{rotulo}': {len(paginas_texto)} pagina(s), SEM TEXTO (precisaria de OCR)")
            continue
        salvar(eid, f"anexo_{salvos}.txt", texto.encode("utf-8"), url, "outro", "anexo_texto")
        print(f"  pdf {n} '{rotulo}': {len(paginas_texto)} pagina(s), {len(texto)} caracteres de texto")

if not args.execucao:
    banco.finalizar_execucao(con, execucao_id)
print(f"\n{'Etapa terminada' if args.execucao else 'Execucao concluida'}. Arquivos em "
      f"{pasta_dados / 'execucoes' / str(execucao_id)}")
con.close()
