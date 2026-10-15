"""Testes das regras com casos pequenos, montados a partir do que foi visto nos portais reais.

Uso, na raiz do projeto:  python -m regras.teste_regras
Cada caso imprime ok ou FALHOU; no fim, o total.
"""
from datetime import date, datetime

from coletor.descoberta import extrair_candidatos, pontuar
from regras import verificacoes as v

casos = []


def caso(nome, obtido, esperado):
    casos.append(obtido == esperado)
    print(f"{'ok     ' if obtido == esperado else 'FALHOU '} {nome}: obtido={obtido!r} esperado={esperado!r}")


LONGO = "<p>" + "texto de preenchimento da pagina " * 10 + "</p>"
hoje = date(2026, 10, 13)

# dias uteis e prazos
caso("dias uteis entre 08/10 e 13/10 (12/10 feriado)", v.dias_uteis_entre(date(2026, 10, 8), hoje), 1)
caso("RGF devido em 13/10/2026", v.periodo_devido(hoje), (2026, 2))
caso("RGF devido em 15/09/2026 (2o quadrimestre ainda no prazo)", v.periodo_devido(date(2026, 9, 15)), (2026, 1))
caso("RGF devido em 10/02/2027", v.periodo_devido(date(2027, 2, 10)), (2026, 3))

# 1.2
achado_visivel = {"sucesso": 1, "visivel_sem_interacao": 1, "precisou_rolar": 1, "texto_clicado": "x", "url_destino": "u"}
caso("1.2 visivel", v.regra_1_2(achado_visivel, None)["status"], "atende")
caso("1.2 submenu", v.regra_1_2(dict(achado_visivel, visivel_sem_interacao=0), None)["status"], "parcial")
caso("1.2 nao achado, capa carregada = Nao atende", v.regra_1_2({"sucesso": 0}, LONGO)["status"], "nao_atende")
caso("1.2 nao achado, capa vazia = sem evidencia", v.regra_1_2({"sucesso": 0}, "<p>carregando</p>"), None)
caso("1.2 nao achado, capa com captcha = sem evidencia",
     v.regra_1_2({"sucesso": 0}, LONGO + "<div class='g-recaptcha'></div>"), None)
caso("1.2 nao achado, capa nem abriu = sem evidencia", v.regra_1_2(None, None), None)
banner = extrair_candidatos("<a href='/portal'><img src='b.png' alt='Portal da Transparência'></a>", "https://x/")
caso("descoberta le o alt de banner sem texto", pontuar(banner[0], "portal") if banner else None, 15)

# 4.1
largo = "<table><tr><th>Número do empenho</th><th>Valor empenhado</th><th>Valor liquidado R$</th><th>Valor pago R$</th></tr></table>"
caso("4.1 formato largo", v.regra_4_1_pagina(largo)["status"], "atende")
sem_pago = "<table><tr><th>Nº Empenho</th><th>Valor empenhado</th><th>Valor liquidado</th></tr></table>"
caso("4.1 sem pago = parcial", v.regra_4_1_pagina(sem_pago)["status"], "parcial")
caso("4.1 formulario sem tabela = sem evidencia", v.regra_4_1_pagina("<form><button>Pesquisar</button></form>" + LONGO), None)
caso("4.1 menu 'Despesas Empenhadas' fora de tabela nao conta", v.regra_4_1_pagina("<a>Despesas Empenhadas</a>" + LONGO), None)

# 4.6
coleta = datetime(2026, 10, 13, 10, 30)
caso("4.6 rotulo de dados", v.regra_4_6_pagina("Dados atualizados até: 12/10/2026" + LONGO, hoje, coleta)["status"], "atende")
caso("4.6 carimbo da hora da visita e ignorado (rodape de Japeri)",
     v.regra_4_6_pagina("dados atualizados em: 13/10/2026 10:31" + LONGO, hoje, coleta), None)
caso("4.6 dados de 08/10 avaliados em 13/10 = Atende (so 09/10 no meio; 12/10 feriado)",
     v.regra_4_6_pagina("Dados atualizados até: 08/10/2026" + LONGO, hoje, coleta)["status"], "atende")
caso("4.6 dados de 07/10 avaliados em 13/10 = Parcial (08/10 ja deveria estar publicado)",
     v.regra_4_6_pagina("Dados atualizados até: 07/10/2026" + LONGO, hoje, coleta)["status"], "parcial")
caso("4.6 data de 20 dias atras = parcial",
     v.regra_4_6_pagina("Última atualização dos dados em 23/09/2026" + LONGO, hoje, coleta)["status"], "parcial")
caso("4.6 data futura e ignorada", v.regra_4_6_pagina("Dados atualizados até: 31/10/2026" + LONGO, hoje, coleta), None)
api_0810 = {"7": {"resposta": {"despesas_detalhadas": [{"dt_doc_despesa": "2026-10-08"}]}}}
falhou = {"entidades_sem_resposta": ["PREFEITURA MUNICIPAL DE JAPERI"]}
caso("4.6 API com entidade sem resposta: Parcial nao provado vira 'nao e evidencia' (execucao 19)",
     "nao_evidencia" in v.regra_4_6_api("geosiap", api_0810, date(2026, 10, 14), falhou), True)
caso("4.6 API com entidade sem resposta: Atende continua provado",
     v.regra_4_6_api("geosiap", api_0810, hoje, falhou)["status"], "atende")
caso("4.6 API com todas respondendo: Parcial vale",
     v.regra_4_6_api("geosiap", api_0810, date(2026, 10, 14), {"entidades_sem_resposta": []})["status"], "parcial")

# 12.1
rio = ("<title>LRF Quadrimestrais Ano 2026</title><h3>Relatório de Gestão Fiscal (RGF)</h3><h4>Anexo 1</h4><p><a href='a.pdf'>1º Quadrimestre</a></p>"
       "<p><a href='b.pdf'>2º Quadrimestre</a></p><p>3º Quadrimestre – Arquivo Editável</p>")
r = v.regra_12_1_pagina(rio, hoje, "https://x/lrf-quadrimestrais-ano-2026/")
caso("12.1 Rio: 3o quadrimestre sem link nao conta", (r["status"], r["detalhe"]["listados_sem_link"]), ("atende", ["2026-Q3"]))
atrasado = "<h1>Relatório de Gestão Fiscal</h1><table><tr><td>RGF - 3º QUADRIMESTRE 2025</td><td><a>Ver arquivos</a></td></tr></table>"
r = v.regra_12_1_pagina(atrasado, hoje, "")
caso("12.1 dois quadrimestres de atraso", (r["status"], r["detalhe"]["quadrimestres_de_atraso"]), ("parcial", 2))
caso("12.1 pagina errada que so cita 'gestao fiscal' nao vira Nao atende",
     v.regra_12_1_pagina("<h1>Plano de execuções orçamentária e de gestão fiscal</h1>" + LONGO, hoje, ""), None)
caso("12.1 pagina do RGF vazia = Nao atende",
     v.regra_12_1_pagina("<h1>Relatório de Gestão Fiscal</h1>" + LONGO, hoje, "")["status"], "nao_atende")

# 16.2
caso("16.2 botao com texto", v.regra_16_2_pagina("<button>Alto contraste</button>" + LONGO)["status"], "atende")
caso("16.2 so classe CSS nao conta",
     v.regra_16_2_pagina("<div class='accessibility-contrast'></div>" + LONGO)["status"], "nao_atende")
caso("16.2 pagina vazia = sem evidencia", v.regra_16_2_pagina("<p>carregando</p>"), None)

print(f"\n{sum(casos)} de {len(casos)} casos ok")
