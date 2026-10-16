"""Teste rapido da API sobre o banco real (dados/gate.db), sem subir servidor.

Uso, na raiz do projeto:  python -m api.teste_api
Cada linha mostra o endpoint, o codigo HTTP e um resumo da resposta.
"""
from fastapi.testclient import TestClient

from api.app import app

cliente = TestClient(app)
entidades = cliente.get("/entidades").json()
print(f"/entidades: {len(entidades)} entidades")
for e in entidades:
    print(f"  {e['id']:22} score {e.get('score')} faixa {e.get('faixa')}{' (provisoria)' if e.get('faixa_provisoria') else ''} "
          f"cobertura {e.get('cobertura')}")
for e in entidades:
    d = cliente.get(f"/entidades/{e['id']}")
    c = cliente.get(f"/entidades/{e['id']}/criterios")
    print(f"/entidades/{e['id']}: HTTP {d.status_code}, aplicaveis {d.json().get('criterios_aplicaveis')}; "
          f"/criterios: HTTP {c.status_code}, {[(x['codigo'], x['status_mais_recente']) for x in c.json()]}")
    a = cliente.get(f"/entidades/{e['id']}/avaliacao")
    h = cliente.get(f"/entidades/{e['id']}/historico")
    print(f"/entidades/{e['id']}/avaliacao: HTTP {a.status_code}, {len(a.json().get('criterios', []))} criterios, "
          f"{sum(len(c['evidencias']) for c in a.json().get('criterios', []))} evidencias, confianca: "
          f"{[(c['codigo'], c['confianca'] and c['confianca']['nivel']) for c in a.json().get('criterios', [])]}")
    print(f"/entidades/{e['id']}/historico: HTTP {h.status_code}, {len(h.json().get('execucoes', []))} execucoes, "
          f"mudancas: {[(m['criterio'], m['de'], m['para'], m['execucao']) for m in h.json().get('mudancas', [])]}")
print(f"/criterios: {[c['codigo'] for c in cliente.get('/criterios').json()]}")
execucoes = cliente.get("/execucoes").json()
print(f"/execucoes: {[x['id'] for x in execucoes['execucoes']]} (fonte: {execucoes['fonte']})")
print(f"/entidades/nao_existe/avaliacao: HTTP {cliente.get('/entidades/nao_existe/avaliacao').status_code} (esperado 404)")
