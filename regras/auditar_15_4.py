"""Mostra, para conferencia humana, o que o LLM respondeu no 15.4 de uma execucao: cada subitem, a fonte
citada (pagina, PDF ou imagem), o trecho e se a citacao foi encontrada na fonte. Nao chama a API.

Uso, na raiz do projeto:  python -m regras.auditar_15_4 --execucao 25
"""
import argparse
import json
from pathlib import Path

from coletor import banco

RAIZ = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--execucao", type=int, required=True)
args = parser.parse_args()

con = banco.conectar(Path(args.dados) / "gate.db")
for eid, status, detalhe in con.execute(
        "SELECT a.entidade_id, a.status, a.detalhe_json FROM avaliacoes a JOIN criterios k ON k.id = a.criterio_id "
        "WHERE a.execucao_id = ? AND k.codigo = '15.4' ORDER BY a.id", (args.execucao,)):
    d = json.loads(detalhe or "{}")
    print(f"\n=== {eid}: {status} ({d.get('subitens_comprovados', '-')} de 5) | prazo recursal achado: "
          f"{d.get('tipo_prazo_recursal', '-')}")
    for f in d.get("fontes", []):
        print(f"  {f['id']:4} {f['tipo']:21} {f['caracteres']:>6} caract. | {f['arquivo']} | {f['url'][:70]}")
    for aviso in d.get("avisos", []):
        print(f"  aviso: {aviso}")
    for nome, s in d.get("subitens", {}).items():
        marca = "OK " if s["comprovado"] else ("XX " if s["atende_segundo_llm"] else "-- ")
        print(f"  {marca}{nome:21} {s['fonte'] or '':4} {s['tipo_fonte'] or '':21} {s['trecho'][:110]!r}")
        if not s["comprovado"]:
            print(f"       {s['observacao'][:150]}")

entrada, saida, chamadas = con.execute(
    "SELECT SUM(tokens_entrada), SUM(tokens_saida), COUNT(*) FROM respostas_llm WHERE execucao_id = ?",
    (args.execucao,)).fetchone()
print(f"\nChamadas ao modelo guardadas desta execucao: {chamadas}; tokens de entrada: {entrada}; de saida: {saida}")
print("Legenda: OK = citacao conferida na fonte; XX = o LLM disse que atende, mas o trecho nao existe na fonte; "
      "-- = o LLM disse que nao atende")
