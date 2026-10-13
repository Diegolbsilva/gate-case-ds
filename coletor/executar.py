"""Execucao completa do coletor: descoberta, APIs dos fornecedores e paginas do cadastro, numa mesma execucao.

Por que uma execucao so: a avaliacao (regras) procura a evidencia de cada criterio na ordem
descoberta > cadastro > Inconclusivo. Com as tres etapas no mesmo id de execucao, a regra le todas as
evidencias daquela rodada juntas, e o historico (§7) tem uma linha por rodada, com data e versao do codigo.

Como funciona: abre a execucao no banco e roda cada etapa como um processo separado, passando o id
(--execucao). Processo separado de proposito: se uma etapa quebrar, as outras rodam mesmo assim, e a
execucao fica marcada como 'falhou' com o nome da etapa que quebrou.
Ordem: descobrir (acha o portal e as paginas) > apis (usa o portal achado pela descoberta) > cadastro >
anexos (le as paginas do e-SIC salvas pelas etapas anteriores, segue "Ver mais detalhes" e baixa os PDFs).

Uso, na raiz do projeto, com o ambiente ativo:
    python -m coletor.executar                     (as 5 entidades)
    python -m coletor.executar --entidade japeri   (so uma, para teste)
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

import yaml

from coletor import banco

RAIZ = Path(__file__).resolve().parent.parent
ETAPAS = ["descobrir", "apis", "cadastro", "anexos"]  # anexos le as paginas do e-SIC salvas pelas anteriores

parser = argparse.ArgumentParser()
parser.add_argument("--config", default=RAIZ / "config" / "entidades.yaml")
parser.add_argument("--criterios", default=RAIZ / "config" / "criterios.yaml")
parser.add_argument("--dados", default=RAIZ / "dados")
parser.add_argument("--entidade", help="rodar so para uma entidade (id do cadastro)")
parser.add_argument("--origem", default="manual", choices=["manual", "agendada"])
args = parser.parse_args()

cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
cfg_criterios = yaml.safe_load(Path(args.criterios).read_text(encoding="utf-8"))
con = banco.conectar(Path(args.dados) / "gate.db")
banco.sincronizar_entidades(con, cfg["entidades"])
banco.sincronizar_criterios(con, cfg_criterios)

# Versao do codigo: commit atual. Se houver arquivo alterado e nao commitado, marca "+alterado",
# para o historico nao atribuir o resultado a um commit que nao e exatamente o codigo que rodou.
try:
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=RAIZ).stdout.strip()
    alterado = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                              text=True, cwd=RAIZ).stdout.strip()
    versao_codigo = (commit + ("+alterado" if alterado else "")) or None
except FileNotFoundError:
    versao_codigo = None

execucao_id = banco.iniciar_execucao(
    con, origem=args.origem, versao_checklist=cfg_criterios["versao_checklist"], versao_codigo=versao_codigo,
    observacao="Execucao completa: " + " > ".join(ETAPAS) + (f" (so {args.entidade})" if args.entidade else ""))
print(f"=== Execucao {execucao_id} (codigo {versao_codigo}) ===")

falhas, inicio = [], time.monotonic()
for etapa in ETAPAS:
    print(f"\n=== Etapa: {etapa} ===", flush=True)
    comando = [sys.executable, "-m", f"coletor.{etapa}", "--execucao", str(execucao_id),
               "--config", str(args.config), "--dados", str(args.dados)]
    if etapa == "cadastro":
        comando += ["--criterios", str(args.criterios)]
    if args.entidade:
        comando += ["--entidade", args.entidade]
    retorno = subprocess.run(comando, cwd=RAIZ).returncode
    if retorno != 0:
        falhas.append(etapa)
        print(f"!!! Etapa {etapa} terminou com erro (codigo {retorno}); seguindo para a proxima", flush=True)

status = "falhou" if falhas else "concluida"
if falhas:
    con.execute("UPDATE execucoes SET observacao = observacao || ? WHERE id = ?",
                (f". Etapas com erro: {', '.join(falhas)}", execucao_id))
banco.finalizar_execucao(con, execucao_id, status=status)

resumo = con.execute(
    "SELECT (SELECT COUNT(*) FROM artefatos WHERE execucao_id = ?), (SELECT COUNT(*) FROM descobertas WHERE "
    "execucao_id = ?), (SELECT COUNT(*) FROM ocorrencias WHERE execucao_id = ?)",
    (execucao_id, execucao_id, execucao_id)).fetchone()
print(f"\n=== Execucao {execucao_id}: {status} em {(time.monotonic() - inicio) / 60:.1f} min. "
      f"Artefatos: {resumo[0]}, passos de descoberta: {resumo[1]}, ocorrencias: {resumo[2]} ===")
con.close()
