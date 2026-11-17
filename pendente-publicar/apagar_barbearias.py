# Apaga da Vercel os projetos de barbearia que não serão mais usados.
# FICAM: PH du Corte (phducorte, phducortebarber, phsucessadabarber), ML Barbearia, GG Barbearia e Galacha.
# Uso:
#   python3 pendente-publicar/apagar_barbearias.py            -> só MOSTRA o que seria apagado
#   python3 pendente-publicar/apagar_barbearias.py --apagar   -> apaga de verdade (não tem volta)
import json, subprocess, sys

APAGAR = ['adonisbarbearia', 'alexbarber', 'alexbarber01', 'alexbarber-five', 'barbeariaandersonsantos',
          'barbeariamarineti', 'casadocavalheiro', 'cortedosamigos', 'elitebarbearia', 'elitebarbearia-flax',
          'elitebarbeer', 'martinsbarbearia', 'wlbarbearia']
MANTER = ['phducorte', 'phducortebarber', 'phsucessadabarber', 'mlbarbearia', 'ggbarbearia', 'galachabarbershop']


def api(m, u):
    r = subprocess.run(['curl', '-sS', '-X', m, 'https://api.vercel.com' + u], capture_output=True, text=True).stdout
    return json.loads(r) if r.strip() else {}


projs, nxt = [], None
while True:
    d = api('GET', '/v9/projects?limit=100' + ('&until=%s' % nxt if nxt else ''))
    if 'error' in d:
        sys.exit('Vercel recusou: %s' % d['error'].get('message'))
    projs += d.get('projects', [])
    nxt = (d.get('pagination') or {}).get('next')
    if not nxt:
        break

alvo = []
for p in projs:
    if p['name'] in MANTER:
        continue
    if p['name'] in APAGAR:
        alvo.append(p)

print('Projetos encontrados na conta:', len(projs))
print('MANTIDOS (barbearia):', [p['name'] for p in projs if p['name'] in MANTER])
print('SERÃO APAGADOS:', [p['name'] for p in alvo])
if '--apagar' not in sys.argv:
    print('\nNada foi apagado. Para apagar de verdade, rode de novo com --apagar')
    sys.exit()
for p in alvo:
    r = subprocess.run(['curl', '-sS', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'DELETE',
                        'https://api.vercel.com/v9/projects/' + p['id']], capture_output=True, text=True).stdout
    print('apagado' if r in ('200', '204') else 'ERRO ' + r, p['name'])
