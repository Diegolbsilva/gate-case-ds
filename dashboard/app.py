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
    "nao_aplicavel": ("– Não aplicável", "#d8d7d2"),
}
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


def faixa_texto(e):
    return f"{e.get('faixa') or '-'}{' *' if e.get('faixa_provisoria') else ''}"


def pintar(valor):
    for rotulo, cor in STATUS.values():
        if valor == rotulo:
            return f"background-color: {cor}33"  # mesma cor de estado, clara, com o texto em tinta normal
    return ""


if pagina == "Visão geral":
    st.title("Conformidade dos portais da transparência")
    col = st.columns(4)
    col[0].metric("Entidades avaliadas", len(entidades))
    col[1].metric("Maior score", f"{max(e.get('score') or 0 for e in entidades):.1f}")
    col[2].metric("Menor score", f"{min(e.get('score') or 0 for e in entidades):.1f}")
    col[3].metric("Com essencial pendente", sum(1 for e in entidades if e.get("essenciais_pendentes")))

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

    st.subheader("Situação por critério")
    linhas = []
    for e in entidades:
        avaliacao = api.avaliacao_mais_recente(e["id"])
        linha = {"Entidade": nomes[e["id"]]}
        for c in avaliacao["criterios"]:
            linha[c["codigo"]] = STATUS.get(c["status"], (c["status"], ""))[0]
        linhas.append(linha)
    matriz = pd.DataFrame(linhas)[["Entidade"] + [c["codigo"] for c in criterios]]
    st.dataframe(matriz.style.map(pintar), hide_index=True, width="stretch")
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
    col[1].metric("Faixa", f"{s.get('faixa') or '-'}{' *' if s.get('faixa_provisoria') else ''}")
    col[2].metric("Cobertura", s.get("cobertura") or "-")
    col[3].metric("Média simples (% de Atende)", f"{s.get('media_simples_binaria') or 0:.1f}")
    if s.get("essenciais_pendentes"):
        st.warning("Essenciais pendentes: " + ", ".join(s["essenciais_pendentes"]))
    if s.get("essenciais_nao_verificados"):
        st.info("Essenciais não verificados nesta execução (faixa provisória): " + ", ".join(s["essenciais_nao_verificados"]))
    st.caption(f"Execução {avaliacao['execucao']['id']} · coleta de {avaliacao['execucao']['iniciada_em']} · "
               f"código {avaliacao['execucao']['versao_codigo']}")

    for c in sorted(avaliacao["criterios"], key=lambda c: float(c["codigo"])):
        rotulo = STATUS.get(c["status"], (c["status"], ""))[0]
        nota = "" if c["nota"] is None else f" · nota {c['nota']:.2f}"
        with st.expander(f"{c['codigo']} · {rotulo}{nota} · {descricao.get(c['codigo'], '')}"):
            st.write(c["justificativa"])
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
                           "Score": x.get("score"), "Faixa": f"{x.get('faixa')}{' *' if x.get('faixa_provisoria') else ''}",
                           "Versão do código": x["versao_codigo"]})
        for m in h["mudancas"]:
            mudancas.append({"Data": m["data"][:10], "Execução": m["execucao"], "Entidade": nomes[eid], "Critério": m["criterio"],
                             "De": STATUS.get(m["de"], (m["de"],))[0], "Para": STATUS.get(m["para"], (m["para"],))[0],
                             "Sentido": m["sentido"],
                             "Mesma versão do código": "sim" if m["mesma_versao_do_codigo"] else "não (pode ser efeito do sistema)"})
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
