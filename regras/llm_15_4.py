"""Criterio 15.4 com LLM: cada subitem com citacao obrigatoria, conferida pelo codigo no texto de origem.

O criterio (texto literal do checklist): "Divulga, na secao relativa ao e-SIC, os prazos de resposta ao
cidadao, incluindo o recursal, e as autoridades competentes para o exame dos pedidos, alem do procedimento
referente a realizacao do pedido e de eventual recurso?"

Por que LLM aqui e regra no resto: o 15.4 e semantico. Cada portal escreve prazos, autoridades e
procedimentos com palavras diferentes ("20 dias, prorrogaveis por mais 10", "o recurso sera submetido a
Comissao..."), em pagina, PDF ou infografico. Uma lista de termos erraria muito; o LLM entende o texto.

Como funciona (decisoes de 15/10/2026, docs/decisoes_regras.md):
1. Fontes: as paginas do e-SIC salvas pela descoberta, pelo cadastro e pela etapa de anexos, o texto dos
   PDFs e as imagens do caminho de cliques. Pagina "nao encontrada" fica de fora.
2. Imagem: uma chamada separada TRANSCREVE o texto da imagem, sem saber do criterio (assim nao tem motivo
   para "achar" prazo ou autoridade). A transcricao vira uma fonte de texto como as outras.
3. Avaliacao: uma chamada com todas as fontes numeradas (F1, F2...) e os 5 subitens, nas palavras do criterio.
   Para cada subitem o modelo responde se a fonte mostra a informacao, de qual fonte e com que trecho literal.
4. Verificacao: o codigo procura o trecho na fonte citada (sem acento, sem diferenca de espaco ou caixa).
   Trecho que nao existe na fonte = subitem nao comprovado, mesmo que o modelo tenha dito que atende.
5. Status: 5 de 5 = Atende; 1 a 4 = Parcial; 0 = Nao atende (so se havia pagina do e-SIC legivel; senao,
   Inconclusivo). Nota gradual = subitens comprovados / 5.

Subitem 3 ("autoridades competentes para o exame dos pedidos"): so a autoridade que examina o PEDIDO.
A que examina apenas o recurso nao basta: o objetivo e o cidadao conhecer o processo inteiro, e o 1o exame
e o passo mais basico (decisao de 15/10/2026; na v1 do prompt a autoridade do recurso tambem contava).

Subitem 2 ("incluindo o recursal"): conta o prazo de resposta ao recurso OU o prazo para entrar com ele
(leitura literal: "prazos de resposta ao cidadao, incluindo o recursal"). O detalhe grava qual foi achado.

Respostas guardadas na tabela respostas_llm: reavaliar a mesma coleta nao chama a API de novo.
Sem chave (ANTHROPIC_API_KEY no ambiente ou no arquivo .env) e sem resposta guardada: Inconclusivo.
"""
import base64
import hashlib
import json
import os
import re
from pathlib import Path

from coletor import banco
from regras import verificacoes as v

RAIZ = Path(__file__).resolve().parent.parent
MODELO = "claude-sonnet-5-5"
ESFORCO = "low"           # decisao de 15/10/2026: tarefa de leitura e extracao, nao de raciocinio longo
VERSAO_PROMPT = "v2-2026-10-15"   # v2: subitem 3 so aceita a autoridade do pedido (decisao de 15/10/2026)
VERSAO_TRANSCRICAO = "v1-2026-10-15"  # versao separada: mudar o prompt da avaliacao nao refaz as transcricoes
MAX_CARACTERES_FONTE = 60000   # PDFs de lei do Rio tem ate ~47 mil; acima disso corta e avisa
MAX_BYTES_IMAGEM = 3_700_000   # a API aceita ate 5 MB em base64 (base64 aumenta ~33%)
PAGINA_NAO_ENCONTRADA = re.compile(r"nao-encontrad|not-found|\b404\b", re.I)

SUBITENS = {
    "prazo_resposta": "os prazos de resposta ao cidadao",
    "prazo_recursal": "incluindo o (prazo) recursal",
    "autoridades": "as autoridades competentes para o exame dos pedidos",
    "procedimento_pedido": "o procedimento referente a realizacao do pedido",
    "procedimento_recurso": "o procedimento referente a eventual recurso",
}

PROMPT_TRANSCRICAO = ("Transcreva literalmente todo o texto visivel nesta imagem, na ordem de leitura, "
                      "mantendo as palavras e os numeros exatamente como aparecem. Nao resuma, nao explique, "
                      "nao corrija. Se nao houver texto, responda apenas: SEM TEXTO.")

PROMPT_AVALIACAO = """Voce avalia um portal da transparencia municipal pelo criterio 15.4 do checklist do Programa Nacional de Transparencia Publica:

"Divulga, na secao relativa ao e-SIC, os prazos de resposta ao cidadao, incluindo o recursal, e as autoridades competentes para o exame dos pedidos, alem do procedimento referente a realizacao do pedido e de eventual recurso?"

O criterio tem 5 subitens:
- prazo_resposta: os prazos de resposta ao cidadao (prazo para o orgao responder o pedido de acesso).
- prazo_recursal: o prazo recursal. Conta o prazo de resposta ao recurso OU o prazo para o cidadao entrar com o recurso. Informe em tipo_prazo_recursal qual foi encontrado.
- autoridades: as autoridades competentes para o exame dos pedidos (quem examina e responde o pedido de acesso). A autoridade que examina somente o recurso NAO basta para este subitem.
- procedimento_pedido: como o cidadao faz o pedido (canal, passos, onde registrar).
- procedimento_recurso: como o cidadao entra com recurso.

Regras:
1. Use SOMENTE as fontes abaixo (F1, F2...). Nao use conhecimento proprio sobre a lei ou sobre o municipio.
2. Para cada subitem com atende = true, copie em "trecho" um pedaco LITERAL e CONTINUO da fonte, de ate 300 caracteres, que mostre a informacao. Copie exatamente como esta, sem reticencias, sem juntar partes distantes. Em "fonte" ponha o identificador (ex.: F3).
3. Se a informacao nao esta nas fontes, atende = false, fonte = "" e trecho = "".
4. Menus, links e titulos soltos (ex.: um link "Recurso" sem explicacao) nao bastam: o texto precisa informar o prazo, a autoridade ou o procedimento.
5. Em "observacao", uma frase curta explicando a decisao do subitem.

FONTES:
"""

ESQUEMA_SUBITEM = {
    "type": "object",
    "properties": {
        "atende": {"type": "boolean"},
        "fonte": {"type": "string"},
        "trecho": {"type": "string"},
        "observacao": {"type": "string"},
    },
    "required": ["atende", "fonte", "trecho", "observacao"],
    "additionalProperties": False,
}
ESQUEMA_RESPOSTA = {
    "type": "object",
    "properties": {
        **{nome: ESQUEMA_SUBITEM for nome in SUBITENS},
        "tipo_prazo_recursal": {"type": "string", "enum": ["resposta_ao_recurso", "entrada_do_recurso", "ambos", "nao_encontrado"]},
    },
    "required": [*SUBITENS, "tipo_prazo_recursal"],
    "additionalProperties": False,
}


def chave_api():
    """ANTHROPIC_API_KEY do ambiente; se nao houver, do arquivo .env na raiz (fora do Git, ver .env.exemplo)."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    arquivo = RAIZ / ".env"
    if arquivo.exists():
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("ANTHROPIC_API_KEY="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def chamar(con, tipo, conteudo, chave_entrada, execucao_id, eid, formato=None, max_tokens=4000):
    """Chama o modelo, ou devolve a resposta ja guardada para a mesma entrada.
    Devolve (texto da resposta, None) ou (None, motivo da falha)."""
    versao = VERSAO_TRANSCRICAO if tipo == "transcricao" else VERSAO_PROMPT
    chave = hashlib.sha256(f"{MODELO}|{versao}|{tipo}|{chave_entrada}".encode()).hexdigest()
    guardada = con.execute("SELECT resposta FROM respostas_llm WHERE chave = ?", (chave,)).fetchone()
    if guardada:
        return guardada[0], None
    chave_secreta = chave_api()
    if not chave_secreta:
        return None, "sem chave da API (ANTHROPIC_API_KEY) e sem resposta guardada para esta coleta"
    import anthropic  # so importa quando vai chamar: quem so le respostas guardadas nao precisa do pacote
    config = {"effort": ESFORCO, **({"format": {"type": "json_schema", "schema": formato}} if formato else {})}
    try:
        resposta = anthropic.Anthropic(api_key=chave_secreta).messages.create(
            model=MODELO, max_tokens=max_tokens, output_config=config,
            messages=[{"role": "user", "content": conteudo}])
    except anthropic.APIError as erro:
        return None, f"erro na API do modelo: {str(erro)[:200]}"
    if resposta.stop_reason in ("max_tokens", "refusal"):
        return None, f"resposta incompleta do modelo (stop_reason={resposta.stop_reason})"
    texto = "".join(b.text for b in resposta.content if b.type == "text")
    con.execute("INSERT INTO respostas_llm (chave, tipo, modelo, versao_prompt, execucao_id, entidade_id, resposta, "
                "tokens_entrada, tokens_saida, criado_em) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (chave, tipo, MODELO, versao, execucao_id, eid, texto, resposta.usage.input_tokens,
                 resposta.usage.output_tokens, banco.agora()))
    con.commit()
    return texto, None


def verificar_trecho(trecho, texto_fonte):
    """True se o trecho citado existe na fonte. Compara sem acento, sem caixa e sem diferenca de espacos
    (o texto de PDF quebra linhas no meio da frase). Se o modelo usar reticencias, cada parte precisa existir."""
    partes = [p for p in re.split(r"\.\.\.|…", v.normalizar(trecho)) if len(p.strip()) >= 10]  # "20 dias uteis" = 13
    alvo = v.normalizar(texto_fonte)
    return bool(partes) and all(p.strip(" \"'") in alvo for p in partes)


def classificar(comprovados, tem_pagina_legivel):
    """Status a partir do numero de subitens comprovados (citacao conferida)."""
    if comprovados == len(SUBITENS):
        return "atende"
    if comprovados > 0:
        return "parcial"
    return "nao_atende" if tem_pagina_legivel else None


def avaliar_15_4(con, execucao_id, eid, artefatos, criterio_id):
    """Devolve o mesmo formato das regras de verificacoes.py, com "evidencias" (uma por subitem comprovado)
    e "nota". None se nao ha nenhuma fonte; {"nao_evidencia": motivo} se nao deu para avaliar."""
    # 1. fontes de texto, sem repeticao (o mesmo HTML pode vir da descoberta e do cadastro)
    fontes, vistos, avisos = [], set(), []
    for a in artefatos:
        e_pagina = a["tipo"] == "html" and (a["criterio_id"] == criterio_id or a["papel"].startswith("descoberta_esic"))
        e_pdf = a["papel"] == "anexo_texto"
        e_imagem = a["papel"].endswith("_imagem")
        if not (e_pagina or e_pdf or e_imagem) or not a["arquivo"].exists():
            continue
        if PAGINA_NAO_ENCONTRADA.search(a["url_final"] or a["url"] or ""):
            avisos.append(f"pagina nao encontrada ignorada: {a['url_final'] or a['url']}")
            continue
        if e_imagem:
            corpo = a["arquivo"].read_bytes()
            if len(corpo) > MAX_BYTES_IMAGEM:
                avisos.append(f"imagem acima de {MAX_BYTES_IMAGEM // 1_000_000} MB ignorada: {a['arquivo'].name}")
                continue
            tipo_midia = "image/png" if corpo.startswith(b"\x89PNG") else "image/jpeg"
            texto, falha = chamar(con, "transcricao", [
                {"type": "image", "source": {"type": "base64", "media_type": tipo_midia,
                                             "data": base64.b64encode(corpo).decode()}},
                {"type": "text", "text": PROMPT_TRANSCRICAO}], a["hash"], execucao_id, eid)
            if falha:
                return {"nao_evidencia": f"transcricao de {a['arquivo'].name}: {falha}"}
            if texto.strip().upper().startswith("SEM TEXTO"):
                continue
            tipo_fonte = "imagem (transcricao)"
        elif e_pdf:
            texto, tipo_fonte = a["arquivo"].read_text(encoding="utf-8"), "pdf"
        else:
            texto, tipo_fonte = v.texto_da_sopa(v.sopa_sem_script(a["arquivo"].read_text(encoding="utf-8"))), "pagina"
        assinatura = hashlib.sha256(v.normalizar(texto).encode()).hexdigest()
        if len(v.normalizar(texto)) < 50 or assinatura in vistos:
            continue
        vistos.add(assinatura)
        if len(texto) > MAX_CARACTERES_FONTE:
            avisos.append(f"{a['arquivo'].name} cortado em {MAX_CARACTERES_FONTE} caracteres (tinha {len(texto)})")
            texto = texto[:MAX_CARACTERES_FONTE]
        fontes.append({"id": f"F{len(fontes) + 1}", "tipo": tipo_fonte, "artefato": a, "texto": v.mascarar(texto),
                       "url": a["url_final"] or a["url"]})
    if not fontes:
        return None

    # 2. avaliacao: uma chamada com todas as fontes
    entrada = PROMPT_AVALIACAO + "\n\n".join(
        f"[{f['id']}] tipo: {f['tipo']} | endereco: {f['url']}\n{f['texto']}" for f in fontes)
    texto, falha = chamar(con, "avaliacao", entrada, hashlib.sha256(entrada.encode()).hexdigest(), execucao_id, eid,
                          formato=ESQUEMA_RESPOSTA, max_tokens=8000)
    if falha:
        return {"nao_evidencia": falha}
    resposta = json.loads(texto)

    # 3. verificacao de cada citacao no texto da fonte citada
    por_id = {f["id"]: f for f in fontes}
    subitens, evidencias = {}, []
    for nome in SUBITENS:
        r = resposta[nome]
        fonte = por_id.get(r["fonte"].strip())
        verificado = bool(r["atende"] and fonte and verificar_trecho(r["trecho"], fonte["texto"]))
        subitens[nome] = {"atende_segundo_llm": r["atende"], "comprovado": verificado, "fonte": r["fonte"],
                          "tipo_fonte": fonte["tipo"] if fonte else None, "trecho": v.mascarar(r["trecho"]),
                          "observacao": r["observacao"]}
        if r["atende"] and not verificado:
            subitens[nome]["observacao"] += " | CITACAO NAO ENCONTRADA NA FONTE: subitem nao comprovado"
        if verificado:
            evidencias.append((fonte["artefato"], f"[{nome}] {r['trecho']}"))
    comprovados = sum(s["comprovado"] for s in subitens.values())
    tem_pagina_legivel = any(f["tipo"] == "pagina" and len(f["texto"]) >= 200 for f in fontes)
    status = classificar(comprovados, tem_pagina_legivel)
    if status is None:
        return {"nao_evidencia": "nenhum subitem comprovado e nenhuma pagina do e-SIC legivel"}
    faltam = [n for n, s in subitens.items() if not s["comprovado"]]
    return {
        "status": status, "nota": comprovados / len(SUBITENS), "evidencias": evidencias,
        "justificativa": f"LLM com citacao conferida: {comprovados} de {len(SUBITENS)} subitens"
                         + (f"; faltam: {', '.join(faltam)}" if faltam else ""),
        "trecho": " | ".join(t for _, t in evidencias),
        "detalhe": {"subitens": subitens, "subitens_comprovados": comprovados,
                    "tipo_prazo_recursal": resposta["tipo_prazo_recursal"], "modelo": MODELO, "esforco": ESFORCO,
                    "versao_prompt": VERSAO_PROMPT, "avisos": avisos,
                    "fontes": [{"id": f["id"], "tipo": f["tipo"], "url": f["url"], "arquivo": f["artefato"]["arquivo"].name,
                                "caracteres": len(f["texto"])} for f in fontes]},
    }
