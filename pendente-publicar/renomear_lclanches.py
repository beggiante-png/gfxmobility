# Transforma o projeto do LC Lanches na Vercel no portfólio "Company Transformation".
# 1) renomeia o projeto lclanches -> companytransformation
# 2) adiciona o endereço companytransformation.vercel.app
# Depois rode: python3 pendente-publicar/publicar.py  (sobe o conteúdo do portfólio nesse projeto)
import json, subprocess, sys

PID = 'prj_RqM6NJzV0oAyN32vohmRbwYvdriW'  # projeto do LC Lanches
NOVO = 'companytransformation'


def api(m, u, data=None):
    a = ['curl', '-sS', '-X', m, 'https://api.vercel.com' + u, '-H', 'Content-Type: application/json']
    if data is not None:
        a += ['--data', json.dumps(data)]
    r = subprocess.run(a, capture_output=True, text=True).stdout
    return json.loads(r) if r.strip() else {}


p = api('GET', '/v9/projects/' + PID)
if 'error' in p:
    sys.exit('Não achei o projeto do LC Lanches: %s' % p['error'].get('message'))
print('Projeto atual:', p['name'])
if p['name'] != NOVO:
    r = api('PATCH', '/v9/projects/' + PID, {'name': NOVO})
    print('Renomeado para:', r.get('name') or r)
d = api('POST', '/v10/projects/%s/domains' % PID, {'name': NOVO + '.vercel.app'})
print('Endereço:', d.get('name') or (d.get('error') or {}).get('message'))
