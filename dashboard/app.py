"""Dashboard (par. 10 do enunciado: visao geral, visao por entidade e evolucao).

Le os dados pelas mesmas funcoes da API (api/app.py): o que o dashboard mostra e exatamente o que a API devolve,
sem uma segunda copia das consultas. Somente leitura.

Uso, na raiz do projeto:  streamlit run dashboard/app.py
"""
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from api import app as api  # noqa: E402

# Status: cor reservada de estado + simbolo + texto (a cor nunca carrega o significado sozinha).
STATUS = {
    "atende": ("✔ Atende", "#0ca30c"),
    "parcial": ("◐ Parcial", "#fab219"),
    "nao_atende": ("✖ Não atende", "#d03b3b"),
    "inconclusivo": ("? Inconclusivo", "#a8a7a1"),
    "indisponivel": ("⚠ Indisponível", "#ec835a"),
    "nao_aplicavel": ("⊘ Não aplicável", "#d8d7d2"),
}
# Faixas do PNTP, da melhor para a pior (config/score.yaml): eixo fixo da distribuicao, inclusive faixas vazias.
FAIXAS = [f["nome"] for f in api.CFG_SCORE["faixas"]]
SEM_VEREDITO = ("inconclusivo", "indisponivel")
# Cor fixa por entidade (paleta categorica, em ordem): a cor segue a entidade em qualquer filtro.
CORES_ENTIDADES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]

st.set_page_config(page_title="GATE: transparência municipal", layout="wide")

try:
    entidades = api.listar_entidades()
    criterios = api.listar_criterios()
except Exception as erro:  # banco ausente ou sem execucao avaliada
    st.error(f"Sem dados para exibir: {getattr(erro, 'detail', erro)}")
    st.stop()
if not entidades or entidades[0].get("ultima_execucao") is None:
    st.warning("Nenhuma execução oficial avaliada. Rode o coletor e as regras antes.")
    st.stop()

nomes = {e["id"]: e["municipio"] for e in entidades}
cor_de = {eid: CORES_ENTIDADES[i % len(CORES_ENTIDADES)] for i, eid in enumerate(sorted(nomes))}
escala_cor = alt.Scale(domain=[nomes[e] for e in sorted(nomes)], range=[cor_de[e] for e in sorted(nomes)])
descricao = {c["codigo"]: c["descricao"] for c in criterios}

pagina = st.sidebar.radio("Visão", ["Visão geral", "Por entidade", "Evolução"])
st.sidebar.caption(f"Execução {entidades[0]['ultima_execucao']} · coleta de {entidades[0]['avaliado_em']}")
st.sidebar.caption(f"Fonte dos dados: {api.FONTE}")
st.sidebar.caption("Faixa com * = provisória: um critério essencial não pôde ser verificado nesta execução.")


# Nomes das faixas com acento so na exibicao (no config e no banco ficam sem acento, como identificadores)
NOME_FAIXA = {"Intermediario": "Intermediário", "Basico": "Básico"}


def faixa_texto(e):
    return f"{NOME_FAIXA.get(e.get('faixa'), e.get('faixa') or '-')}{' *' if e.get('faixa_provisoria') else ''}"


def pintar(valor):
    for rotulo, cor in STATUS.values():
        if valor == rotulo:
            return f"background-color: {cor}33"  # mesma cor de estado, clara, com o texto em tinta normal
    return ""


if pagina == "Visão geral":
    st.title("Conformidade dos portais da transparência")
    com_score = [e for e in entidades if e.get("score") is not None]
    maior = max(e["score"] for e in com_score)
    menor = min(e["score"] for e in com_score)
    col = st.columns(4)
    col[0].metric("Entidades avaliadas", len(entidades))
    col[1].metric("Pontuação média", f"{sum(e['score'] for e in com_score) / len(com_score):.1f}")
    col[2].metric("Melhor classificação", f"{maior:.1f}")
    col[2].caption(", ".join(f"{nomes[e['id']]} ({faixa_texto(e)})" for e in com_score if e["score"] == maior))
    col[3].metric("Pior classificação", f"{menor:.1f}")
    col[3].caption(", ".join(f"{nomes[e['id']]} ({faixa_texto(e)})" for e in com_score if e["score"] == menor))

    # status de todas as celulas (entidade x criterio) da avaliacao mais recente
    avaliacoes = {e["id"]: api.avaliacao_mais_recente(e["id"]) for e in entidades}
    celulas = [c["status"] for a in avaliacoes.values() for c in a["criterios"]]
    st.subheader("Critérios atendidos e não atendidos")
    col = st.columns(5)
    col[0].metric(STATUS["atende"][0], sum(x == "atende" for x in celulas))
    col[1].metric(STATUS["parcial"][0], sum(x == "parcial" for x in celulas))
    col[2].metric(STATUS["nao_atende"][0], sum(x == "nao_atende" for x in celulas))
    col[3].metric("Sem veredito", sum(x in SEM_VEREDITO for x in celulas))
    col[4].metric(STATUS["nao_aplicavel"][0], sum(x == "nao_aplicavel" for x in celulas))
    st.caption(f"{len(celulas)} avaliações ({len(entidades)} entidades × {len(criterios)} critérios). "
               "Sem veredito = Inconclusivo (o sistema não conseguiu verificar) ou Indisponível (site fora do ar).")

    st.subheader("Score por entidade")
    tabela = pd.DataFrame([{"Entidade": nomes[e["id"]], "Score": e.get("score"), "Faixa": faixa_texto(e),
                            "Cobertura": e.get("cobertura"), "Essenciais pendentes": ", ".join(e.get("essenciais_pendentes") or []) or "-",
                            "Média simples (% de Atende)": e.get("media_simples_binaria")}
                           for e in sorted(entidades, key=lambda x: -(x.get("score") or 0))])
    st.dataframe(tabela, hide_index=True, width="stretch")

    barras = alt.Chart(tabela).mark_bar(cornerRadiusEnd=4, size=22).encode(
        x=alt.X("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Score (0 a 100)"),
        y=alt.Y("Entidade:N", sort=list(tabela["Entidade"]), title=None, axis=alt.Axis(labelLimit=200)),
        color=alt.Color("Entidade:N", scale=escala_cor, legend=None),
        tooltip=["Entidade", "Score", "Faixa", "Cobertura"])
    rotulos = barras.mark_text(align="left", dx=4).encode(text=alt.Text("Score:Q", format=".1f"),
                                                          color=alt.value("#8a8984"))  # tinta neutra legivel no tema claro e no escuro, nao a cor da serie
    st.altair_chart((barras + rotulos).properties(height=220), width="stretch")

    st.subheader("Distribuição dos scores por faixa")
    contagem = pd.DataFrame([{"Faixa": NOME_FAIXA.get(f, f), "Entidades": sum(1 for e in com_score if e.get("faixa") == f),
                              "Quais": ", ".join(nomes[e["id"]] for e in com_score if e.get("faixa") == f) or "-"}
                             for f in FAIXAS])
    dist = alt.Chart(contagem).mark_bar(cornerRadiusEnd=4, size=22, color=CORES_ENTIDADES[0]).encode(
        x=alt.X("Faixa:N", sort=[NOME_FAIXA.get(f, f) for f in FAIXAS], title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Entidades:Q", title="Entidades", axis=alt.Axis(tickMinStep=1)),
        tooltip=["Faixa", "Entidades", "Quais"])
    dist_rotulos = dist.mark_text(dy=-8).encode(text="Entidades:Q", color=alt.value("#8a8984"))
    st.altair_chart((dist + dist_rotulos).properties(height=220), width="stretch")
    st.caption("Faixas do PNTP, da melhor para a pior. Diamante, Ouro e Prata exigem todos os critérios essenciais atendidos.")

    st.subheader("Situação por critério")
    linhas = []
    for eid, avaliacao in avaliacoes.items():
        linha = {"Entidade": nomes[eid]}
        for c in avaliacao["criterios"]:
            linha[c["codigo"]] = STATUS.get(c["status"], (c["status"], ""))[0]
        linhas.append(linha)
    matriz = pd.DataFrame(linhas)[["Entidade"] + [c["codigo"] for c in criterios]]
    st.dataframe(matriz.style.map(pintar), hide_index=True, width="stretch")
    por_criterio = pd.DataFrame([{"Critério": c["codigo"], "Descrição": c["descricao"],
                                  **{STATUS[k][0]: sum(1 for a in avaliacoes.values() for x in a["criterios"]
                                                       if x["codigo"] == c["codigo"] and x["status"] == k)
                                     for k in ("atende", "parcial", "nao_atende")},
                                  "Sem veredito": sum(1 for a in avaliacoes.values() for x in a["criterios"]
                                                      if x["codigo"] == c["codigo"] and x["status"] in SEM_VEREDITO)}
                                 for c in criterios])
    with st.expander("Contagem por critério"):
        st.dataframe(por_criterio, hide_index=True, width="stretch")
    with st.expander("O que cada critério verifica"):
        st.dataframe(pd.DataFrame([{"Critério": c["codigo"], "Descrição": c["descricao"], "Fundamentação": c["fundamentacao"],
                                    "Classificação": c["classificacao"], "Peso": c["peso_score"]} for c in criterios]),
                     hide_index=True, width="stretch")

elif pagina == "Por entidade":
    eid = st.selectbox("Entidade", sorted(nomes), format_func=lambda x: nomes[x])
    avaliacao = api.avaliacao_mais_recente(eid)
    s = avaliacao["score"] or {}
    st.title(avaliacao["entidade"]["nome"])
    col = st.columns(4)
    col[0].metric("Score", f"{s.get('score', 0):.1f}")
    col[1].metric("Faixa", faixa_texto(s))
    col[2].metric("Cobertura", s.get("cobertura") or "-")
    col[3].metric("Média simples (% de Atende)", f"{s.get('media_simples_binaria') or 0:.1f}")
    if s.get("essenciais_pendentes"):
        st.warning("Essenciais pendentes: " + ", ".join(s["essenciais_pendentes"]))
    if s.get("essenciais_nao_verificados"):
        st.info("Essenciais não verificados nesta execução (faixa provisória): " + ", ".join(s["essenciais_nao_verificados"]))
    st.caption(f"Execução {avaliacao['execucao']['id']} · coleta de {avaliacao['execucao']['iniciada_em']} · "
               f"código {avaliacao['execucao']['versao_codigo']}")

    st.subheader("Critérios não atendidos")
    faltas = [c for c in sorted(avaliacao["criterios"], key=lambda c: float(c["codigo"]))
              if c["status"] in ("nao_atende", "parcial")]
    if faltas:
        st.dataframe(pd.DataFrame([{"Critério": c["codigo"], "Status": STATUS[c["status"]][0],
                                    "Nota": c["nota"] if c["nota"] is not None else s.get("criterios", {}).get(c["codigo"], {}).get("nota"),
                                    "Descrição": descricao.get(c["codigo"], ""), "Por quê": c["justificativa"]} for c in faltas])
                     .style.map(pintar, subset=["Status"]), hide_index=True, width="stretch",
                     column_config={"Nota": st.column_config.NumberColumn("Nota (0 a 1)", format="%.2f")})
    else:
        st.write("Nenhum critério com Não atende ou Parcial nesta execução.")
    sem = [f"{c['codigo']} ({STATUS[c['status']][0]})" for c in avaliacao["criterios"] if c["status"] in SEM_VEREDITO]
    if sem:
        st.caption("Sem veredito nesta execução (não entram no score): " + ", ".join(sem))

    st.subheader("Desempenho por categoria")
    # desempenho da categoria = media das notas (0 a 1) dos seus criterios que entraram no score
    cats = {}
    for c in criterios:
        nota = s.get("criterios", {}).get(c["codigo"], {}).get("nota")
        if nota is not None:
            cats.setdefault(c["categoria"], []).append((c["codigo"], nota))
    tab_cat = pd.DataFrame([{"Categoria": cat, "Critérios": ", ".join(k for k, _ in v),
                             "Desempenho (%)": round(100 * sum(n for _, n in v) / len(v), 1)} for cat, v in cats.items()]
                           ).sort_values("Desempenho (%)", ascending=False)
    if not tab_cat.empty:
        melhor, pior = tab_cat["Desempenho (%)"].max(), tab_cat["Desempenho (%)"].min()
        if melhor == pior:
            st.write(f"Todas as categorias avaliadas com o mesmo desempenho ({melhor:.0f}%).")
        else:
            st.write(f"**Melhor:** {', '.join(tab_cat[tab_cat['Desempenho (%)'] == melhor]['Categoria'])} ({melhor:.0f}%)  \n"
                     f"**Pior:** {', '.join(tab_cat[tab_cat['Desempenho (%)'] == pior]['Categoria'])} ({pior:.0f}%)")
        st.dataframe(tab_cat, hide_index=True, width="stretch", column_config={
            "Desempenho (%)": st.column_config.ProgressColumn("Desempenho (%)", min_value=0, max_value=100, format="%.0f")})
        st.caption("Desempenho = média das notas dos critérios da categoria (Atende 1, Parcial gradual, Não atende 0, "
                   "Indisponível 0,5). Critérios sem veredito ficam de fora.")

    st.subheader("Evolução histórica")
    h = api.historico(eid)
    serie = pd.DataFrame([{"Data": x["data"][:10], "Execução": x["execucao"], "Score": x.get("score"),
                           "Faixa": faixa_texto(x),
                           "Versão do código": x["versao_codigo"]} for x in h["execucoes"]])
    if len(serie) > 1:
        linha = alt.Chart(serie).mark_line(strokeWidth=2, color=cor_de[eid],
                                           point=alt.OverlayMarkDef(size=80, filled=True, color=cor_de[eid])).encode(
            x=alt.X("Data:O", title="Data da coleta", axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Score (0 a 100)"),
            tooltip=["Data", "Execução", "Score", "Faixa", "Versão do código"])
        st.altair_chart(linha.properties(height=240), width="stretch")
        st.caption(" → ".join(f"{x:.1f}" for x in serie["Score"] if x is not None))
    status_hist = pd.DataFrame([{"Critério": k, **{x["data"][:10]: STATUS.get(x["status"].get(k), ("-",))[0]
                                                   for x in h["execucoes"]}}
                                for k in sorted({k for x in h["execucoes"] for k in x["status"]}, key=float)])
    if not status_hist.empty:
        with st.expander("Status de cada critério por execução"):
            st.dataframe(status_hist.style.map(pintar), hide_index=True, width="stretch")

    st.subheader("Evidências por critério")
    for c in sorted(avaliacao["criterios"], key=lambda c: float(c["codigo"])):
        rotulo = STATUS.get(c["status"], (c["status"], ""))[0]
        nota = "" if c["nota"] is None else f" · nota {c['nota']:.2f}"
        conf = c.get("confianca")
        nivel = f" · confiança {'alta' if conf['nivel'] == 'alta' else 'média'}" if conf else ""
        with st.expander(f"{c['codigo']} · {rotulo}{nota}{nivel} · {descricao.get(c['codigo'], '')}"):
            st.write(c["justificativa"])
            if conf and conf["acerto_observado"] is not None:
                st.caption(f"Confiança {'alta' if conf['nivel'] == 'alta' else 'média'}: "
                           f"{conf['acerto_observado']:.0%} de acerto observado ({conf['base']})")
            st.caption(f"Método: {c['metodo']} · página avaliada: {c['url_avaliada'] or '-'}")
            for ev in c["evidencias"]:
                st.code(ev["trecho"] or "(sem trecho)", language=None)
                st.caption(f"Fonte: {ev['url'] or '-'} · arquivo: {Path(ev['caminho_arquivo']).name if ev['caminho_arquivo'] else '-'} · "
                           f"hash {(ev['hash_sha256'] or '')[:12]} · coletado em {ev['coletado_em']}")

else:
    st.title("Evolução")
    pontos, mudancas = [], []
    for eid in sorted(nomes):
        h = api.historico(eid)
        for x in h["execucoes"]:
            pontos.append({"Entidade": nomes[eid], "Execução": x["execucao"], "Data": x["data"][:10],
                           "Score": x.get("score"), "Faixa": faixa_texto(x),
                           "Versão do código": x["versao_codigo"]})
        for m in h["mudancas"]:
            mudancas.append({"Data": m["data"][:10], "Execução": m["execucao"], "Entidade": nomes[eid], "Critério": m["criterio"],
                             "De": STATUS.get(m["de"], (m["de"],))[0], "Para": STATUS.get(m["para"], (m["para"],))[0],
                             "Sentido": m["sentido"],
                             "Mesma versão do coletor": "sim" if m["mesma_versao_do_codigo"] else "não (pode ser efeito do sistema)"})
    df = pd.DataFrame(pontos)
    if df.empty:
        st.info("Ainda não há execuções suficientes para mostrar evolução.")
        st.stop()
    linhas = alt.Chart(df).mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=80, filled=True)).encode(
        x=alt.X("Data:O", title="Data da coleta", axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 100]), title="Score (0 a 100)"),
        color=alt.Color("Entidade:N", scale=escala_cor, legend=alt.Legend(title="Entidade", orient="bottom")),
        tooltip=["Entidade", "Data", "Execução", "Score", "Faixa", "Versão do código"])
    st.altair_chart(linhas.properties(height=320), width="stretch")
    st.caption("Mudança entre execuções com versões de código diferentes pode ser efeito do sistema (coleta ou regra), "
               "não do portal. Para comparar, as coletas antigas podem ser reavaliadas com o código atual.")

    st.subheader("O que mudou e quando")
    if mudancas:
        st.dataframe(pd.DataFrame(mudancas).sort_values(["Data", "Entidade"]), hide_index=True, width="stretch")
    else:
        st.write("Nenhuma mudança de status entre execuções.")
    with st.expander("Tabela de scores por execução"):
        st.dataframe(df.pivot_table(index="Entidade", columns="Data", values="Score"), width="stretch")
