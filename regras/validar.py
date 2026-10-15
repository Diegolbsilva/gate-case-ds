"""Validacao dos resultados (par. 15, 16 e 18 do enunciado: validar a IA, qualidade dos resultados, avaliar os proprios resultados).

Le o banco e os arquivos de configuracao; nao acessa portal nem chama o LLM. Rodar depois de
regras.avaliar nas execucoes a validar (o avaliar grava as avaliacoes e o score de cada execucao).

Referencias:
- interna: config/gabarito.yaml (avaliacao manual). O 4.6 so tem gabarito nos dias conferidos a mao.
- externa: config/referencias.yaml (selos do PNTP exibidos nos portais).

Medidas:
1. Concordancia nas celulas conclusivas, por criterio: quando o sistema da veredito, quantas vezes acerta.
2. Taxa de inconclusivos (e indisponiveis), por criterio: quantas vezes o sistema se abstem.
3. Matriz sistema x gabarito: como erra. O erro mais grave e o falso Nao atende (acusa sem prova).
4. Estabilidade: a mesma celula da o mesmo status em execucoes diferentes (4.6 fica fora: muda com o dia).
5. Faixa do score x selo do PNTP: a ordem das entidades bate com a referencia externa?

Uso:  python -m regras.validar                      (todas as execucoes completas das 5 entidades)
      python -m regras.validar --execucoes 16 19 25
Saida em tabelas Markdown, prontas para a documentacao.
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

from coletor import banco

RAIZ = Path(__file__).resolve().parent.parent
CRITERIOS = ["1.2", "4.1", "4.6", "12.1", "15.4", "16.2"]
STATUS = ["atende", "parcial", "nao_atende", "inconclusivo", "indisponivel"]
SEM_VEREDITO = ("inconclusivo", "indisponivel")
ORDEM_FAIXAS = ["Diamante", "Ouro", "Prata", "Elevado", "Intermediario", "Basico", "Inicial", "Inexistente"]

parser = argparse.ArgumentParser()
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--gabarito", default=RAIZ / "config" / "gabarito.yaml")
parser.add_argument("--referencias", default=RAIZ / "config" / "referencias.yaml")
parser.add_argument("--execucoes", type=int, nargs="*")
args = parser.parse_args()

con = banco.conectar(Path(args.dados) / "gate.db")
gabarito = yaml.safe_load(Path(args.gabarito).read_text(encoding="utf-8"))
selos = yaml.safe_load(Path(args.referencias).read_text(encoding="utf-8"))["selos_pntp"]
execucoes = args.execucoes or [r[0] for r in con.execute(
    "SELECT id FROM execucoes WHERE status = 'concluida' AND observacao LIKE 'Execucao completa%' "
    "AND observacao NOT LIKE '%(so %' ORDER BY id")]

celulas = []  # (execucao, data, entidade, criterio, sistema, gabarito ou None)
for e in execucoes:
    data = con.execute("SELECT substr(iniciada_em, 1, 10) FROM execucoes WHERE id = ?", (e,)).fetchone()[0]
    for eid, codigo, status in con.execute(
            "SELECT a.entidade_id, k.codigo, a.status FROM avaliacoes a JOIN criterios k ON k.id = a.criterio_id "
            "WHERE a.execucao_id = ? ORDER BY a.id", (e,)):
        esperado = gabarito.get(eid, {}).get(codigo)
        if isinstance(esperado, dict):  # gabarito com data (4.6): so vale no dia conferido
            esperado = esperado.get(data)
        celulas.append((e, data, eid, codigo, status, esperado))
if not celulas:
    raise SystemExit("Nenhuma avaliacao nas execucoes pedidas: rode antes python -m regras.avaliar --execucao N")

print(f"# Validacao: execucoes {', '.join(map(str, execucoes))} "
      f"({', '.join(sorted({c[1] for c in celulas}))})\n")

# 1 e 2. concordancia e abstencao por criterio
print("## Concordancia com o gabarito, por criterio\n")
print("| Criterio | Celulas com gabarito | Sem veredito (inconclusivo/indisponivel) | Conclusivas | Acertos | "
      "Concordancia nas conclusivas | Taxa sem veredito |")
print("|---|---|---|---|---|---|---|")
total = Counter()
for codigo in CRITERIOS:
    com_gab = [c for c in celulas if c[3] == codigo and c[5] is not None]
    sem = sum(c[4] in SEM_VEREDITO for c in com_gab)
    conclusivas = [c for c in com_gab if c[4] not in SEM_VEREDITO]
    acertos = sum(c[4] == c[5] for c in conclusivas)
    total.update(n=len(com_gab), sem=sem, conc=len(conclusivas), ac=acertos)
    print(f"| {codigo} | {len(com_gab)} | {sem} | {len(conclusivas)} | {acertos} | "
          f"{acertos / len(conclusivas):.0%} | {sem / len(com_gab):.0%} |" if com_gab else f"| {codigo} | 0 | - | - | - | - | - |")
print(f"| **Total** | {total['n']} | {total['sem']} | {total['conc']} | {total['ac']} | "
      f"{total['ac'] / max(total['conc'], 1):.0%} | {total['sem'] / max(total['n'], 1):.0%} |\n")

print("## Concordancia por execucao\n")
print("| Execucao | Data | Celulas com gabarito | Conclusivas | Acertos | Concordancia nas conclusivas | Sem veredito |")
print("|---|---|---|---|---|---|---|")
for e in execucoes:
    com_gab = [c for c in celulas if c[0] == e and c[5] is not None]
    conclusivas = [c for c in com_gab if c[4] not in SEM_VEREDITO]
    acertos = sum(c[4] == c[5] for c in conclusivas)
    data = next((c[1] for c in celulas if c[0] == e), "-")
    print(f"| {e} | {data} | {len(com_gab)} | {len(conclusivas)} | {acertos} | "
          f"{acertos / max(len(conclusivas), 1):.0%} | {len(com_gab) - len(conclusivas)} |")

# 3. matriz e lista de divergencias
print("\n## Matriz sistema x gabarito (todas as celulas com gabarito)\n")
gab_status = ["atende", "parcial", "nao_atende"]
print("| Sistema \\ Gabarito | " + " | ".join(gab_status) + " |")
print("|---|" + "---|" * len(gab_status))
matriz = Counter((c[4], c[5]) for c in celulas if c[5] is not None)
for s in STATUS:
    print(f"| {s} | " + " | ".join(str(matriz[(s, g)]) for g in gab_status) + " |")
falso_nao_atende = sum(matriz[("nao_atende", g)] for g in gab_status if g != "nao_atende")
print(f"\nFalso Nao atende (sistema acusa, gabarito nao): {falso_nao_atende}\n")

divergentes = [c for c in celulas if c[5] is not None and c[4] != c[5]]
print("## Divergencias\n")
if divergentes:
    print("| Execucao | Entidade | Criterio | Sistema | Gabarito | Justificativa do sistema |")
    print("|---|---|---|---|---|---|")
    for e, data, eid, codigo, status, esperado in divergentes:
        just = con.execute("SELECT a.justificativa FROM avaliacoes a JOIN criterios k ON k.id = a.criterio_id "
                           "WHERE a.execucao_id = ? AND a.entidade_id = ? AND k.codigo = ?", (e, eid, codigo)).fetchone()[0]
        print(f"| {e} | {eid} | {codigo} | {status} | {esperado} | {(just or '')[:120].replace('|', '/')} |")
else:
    print("Nenhuma.")

# 4. estabilidade (4.6 fora: o status certo muda com o dia)
print("\n## Estabilidade entre execucoes (sem o 4.6)\n")
por_celula = defaultdict(list)
for e, data, eid, codigo, status, _ in celulas:
    if codigo != "4.6":
        por_celula[(eid, codigo)].append((e, status))
estaveis = [k for k, v in por_celula.items() if len({s for _, s in v}) == 1]
print(f"Celulas com o mesmo status em todas as execucoes: {len(estaveis)} de {len(por_celula)}\n")
instaveis = {k: v for k, v in por_celula.items() if k not in estaveis}
if instaveis:
    print("| Entidade | Criterio | Status por execucao |")
    print("|---|---|---|")
    for (eid, codigo), v in sorted(instaveis.items()):
        print(f"| {eid} | {codigo} | {'; '.join(f'{e}: {s}' for e, s in v)} |")

# 5. faixa do score x selo do PNTP
print("\n## Faixa do sistema x selo do PNTP\n")
print("| Entidade | Selo PNTP | " + " | ".join(f"Execucao {e}" for e in execucoes) + " |")
print("|---|---|" + "---|" * len(execucoes))
faixas = {}
for eid in sorted({c[2] for c in celulas}):
    linha = []
    for e in execucoes:
        r = con.execute("SELECT score, detalhe_json FROM scores WHERE execucao_id = ? AND entidade_id = ?", (e, eid)).fetchone()
        if r:
            d = json.loads(r[1])
            f = d["faixa"]
            faixas[(eid, e)] = f
            linha.append(f"{r[0] * 100:.1f} ({f}{', provisoria' if d.get('faixa_provisoria') else ''})")
        else:
            linha.append("-")
    selo = selos.get(eid)
    print(f"| {eid} | {(selo['selo'] + (' ' + str(selo['ano']) if selo.get('ano') else '')) if selo else '-'} | "
          + " | ".join(linha) + " |")

ultima = execucoes[-1]
com_selo = [eid for eid in selos if (eid, ultima) in faixas]
pares = [(a, b) for i, a in enumerate(com_selo) for b in com_selo[i + 1:]]
# par concordante: a ordem pelo selo e a ordem pela faixa do sistema nao se contradizem (empate no sistema nao contradiz)
concordantes = sum(
    (ORDEM_FAIXAS.index(selos[a]["selo"]) - ORDEM_FAIXAS.index(selos[b]["selo"]))
    * (ORDEM_FAIXAS.index(faixas[(a, ultima)]) - ORDEM_FAIXAS.index(faixas[(b, ultima)])) >= 0 for a, b in pares)
mesma_faixa = sum(faixas[(eid, ultima)] == selos[eid]["selo"] for eid in com_selo)
print(f"\nExecucao {ultima}: faixa igual ao selo em {mesma_faixa} de {len(com_selo)} entidades; "
      f"pares de entidades sem inversao de ordem: {concordantes} de {len(pares)}")
con.close()
