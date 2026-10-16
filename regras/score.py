"""Score de cada entidade numa execucao, a partir das avaliacoes ja gravadas (regras/avaliar.py).

Metodologia (config/score.yaml e docs/documentacao_tecnica.md, secao 6):
1. Nota de cada criterio, de 0 a 1: Atende = 1; Nao atende = 0; Parcial = nota gradual pelo detalhe da regra
   (4.1: informacoes achadas / 4; 12.1: 1 - atraso / 3; 15.4: subitens comprovados / 5; 1.2 e 4.6: 0,5);
   Indisponivel = 0,5 (punicao leve: o site fora do ar e falha da entidade).
2. Inconclusivo e Nao aplicavel ficam FORA do calculo (Inconclusivo e limitacao do sistema, nao falha da entidade) e aparecem
   como cobertura: criterios que entraram / criterios aplicaveis.
3. Score = soma(peso x nota) / soma(pesos dos criterios que entraram). Pesos do PNTP por classificacao.
4. Faixa do PNTP: Diamante, Ouro e Prata exigem 100% dos essenciais atendidos.
5. Para a discussao do par. 5 (problemas da media simples), grava tambem duas medias sem peso:
   - media simples binaria: % de criterios com Atende (o jeito mais comum de resumir um checklist);
   - media simples das notas: as notas graduais, sem peso (separa o efeito da nota gradual do efeito do peso).

Uso:  python -m regras.score --execucao 25   (tambem e chamado no fim de regras.avaliar)
"""
import argparse
import json
from pathlib import Path

import yaml

from coletor import banco

RAIZ = Path(__file__).resolve().parent.parent
FORA_DO_CALCULO = ("inconclusivo", "nao_aplicavel")


def nota_do_criterio(codigo, status, nota_gravada, detalhe, cfg):
    """Nota de 0 a 1, ou None se o criterio fica fora do calculo."""
    if status in FORA_DO_CALCULO:
        return None
    if status == "atende":
        return 1.0
    if status == "nao_atende":
        return 0.0
    if status == "indisponivel":
        return cfg["nota_indisponivel"]
    # parcial: nota gradual a partir do detalhe gravado pela regra
    if codigo == "4.1":
        return (bool(detalhe.get("numero_empenho")) + len(detalhe.get("fases", []))) / 4
    if codigo == "12.1":
        return max(0.0, 1 - detalhe.get("quadrimestres_de_atraso", 0) / cfg["quadrimestres_para_zerar_12_1"])
    if codigo == "15.4":
        return nota_gravada if nota_gravada is not None else detalhe.get("subitens_comprovados", 0) / 5
    if codigo == "1.2":
        return cfg["nota_parcial_1_2"]
    if codigo == "4.6":
        return cfg["nota_parcial_4_6"]
    return 0.5  # criterio novo sem nota gradual definida: ponto medio, ate haver decisao


def faixa(score_pct, essenciais_completos, cfg):
    for f in cfg["faixas"]:
        if score_pct >= f["minimo"] and (essenciais_completos or not f["exige_essenciais"]):
            return f["nome"]
    return "Inexistente"


def calcular(con, execucao_id, cfg):
    """Calcula e grava o score de cada entidade da execucao. Devolve as linhas para impressao."""
    linhas = {}
    for eid, codigo, status, nota_gravada, detalhe in con.execute(
            "SELECT a.entidade_id, k.codigo, a.status, a.nota, a.detalhe_json FROM avaliacoes a "
            "JOIN criterios k ON k.id = a.criterio_id WHERE a.execucao_id = ? ORDER BY a.id", (execucao_id,)):
        linhas.setdefault(eid, []).append((codigo, status, nota_gravada, json.loads(detalhe or "{}")))

    resultado = []
    for eid, criterios in linhas.items():
        por_criterio, soma_pesos, soma = {}, 0.0, 0.0
        for codigo, status, nota_gravada, detalhe in criterios:
            classe = cfg["classificacao"].get(codigo, "recomendada")
            peso = cfg["pesos"][classe]
            nota = nota_do_criterio(codigo, status, nota_gravada, detalhe, cfg)
            por_criterio[codigo] = {"status": status, "classificacao": classe, "peso": peso,
                                    "nota": None if nota is None else round(nota, 4)}
            if nota is not None:
                soma_pesos += peso
                soma += peso * nota
        entraram = [c for c in por_criterio.values() if c["nota"] is not None]
        aplicaveis = [c for c in por_criterio.values() if c["status"] != "nao_aplicavel"]
        essenciais = {k: c for k, c in por_criterio.items() if c["classificacao"] == "essencial"}
        # Faixa (decisao de 15/10/2026): essencial com falha provada da entidade (Parcial, Nao atende, Indisponivel)
        # bloqueia Diamante/Ouro/Prata. Essencial Inconclusivo nao bloqueia (nao ha prova de culpa da entidade):
        # a faixa sai marcada como provisoria, com o criterio nao verificado.
        pendentes = [f"{k} ({c['status']})" for k, c in essenciais.items() if c["status"] not in ("atende", "inconclusivo")]
        nao_verificados = [k for k, c in essenciais.items() if c["status"] == "inconclusivo"]
        score = soma / soma_pesos if soma_pesos else None
        detalhe = {
            "criterios": por_criterio,
            "essenciais_completos": not pendentes,
            "essenciais_pendentes": pendentes,
            "essenciais_nao_verificados": nao_verificados,
            "faixa": faixa(score * 100, not pendentes, cfg) if score is not None else None,
            "faixa_provisoria": bool(nao_verificados),
            "media_simples_binaria": round(sum(c["status"] == "atende" for c in entraram) / len(entraram), 4) if entraram else None,
            "media_simples_notas": round(sum(c["nota"] for c in entraram) / len(entraram), 4) if entraram else None,
            "fora_do_calculo": [f"{k} ({c['status']})" for k, c in por_criterio.items() if c["nota"] is None],
        }
        if score is not None:
            con.execute("INSERT OR REPLACE INTO scores (execucao_id, entidade_id, score, criterios_avaliados, "
                        "criterios_aplicaveis, metodologia, detalhe_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (execucao_id, eid, round(score, 4), len(entraram), len(aplicaveis), cfg["versao"],
                         json.dumps(detalhe, ensure_ascii=False)))
        resultado.append((eid, score, len(entraram), len(aplicaveis), detalhe))
    con.commit()
    return resultado


def imprimir(resultado):
    print(f"\n{'entidade':22} {'score':>6} {'faixa':13} {'essenciais':11} {'cobertura':9} {'media bin.':>10} "
          f"{'media notas':>11}  fora do calculo / essenciais pendentes")
    for eid, score, entraram, aplicaveis, d in sorted(resultado, key=lambda r: -(r[1] or 0)):
        print(f"{eid:22} {(score or 0) * 100:6.1f} {(d['faixa'] or '-') + ('*' if d.get('faixa_provisoria') else ''):13} {'completos' if d['essenciais_completos'] else 'pendentes':11} "
              f"{entraram} de {aplicaveis:<4} {(d['media_simples_binaria'] or 0) * 100:10.1f} {(d['media_simples_notas'] or 0) * 100:11.1f}  "
              f"{', '.join(dict.fromkeys(d['fora_do_calculo'] + d['essenciais_pendentes'])) or '-'}")
    print("* faixa provisoria: algum criterio essencial ficou Inconclusivo (nao verificado) nesta execucao")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dados", default=RAIZ / "dados")
    parser.add_argument("--score", default=RAIZ / "config" / "score.yaml")
    parser.add_argument("--execucao", type=int, required=True)
    args = parser.parse_args()
    con = banco.conectar(Path(args.dados) / "gate.db")
    imprimir(calcular(con, args.execucao, yaml.safe_load(Path(args.score).read_text(encoding="utf-8"))))
    con.close()
