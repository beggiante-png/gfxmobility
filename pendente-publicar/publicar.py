# Publica na Vercel as alterações pendentes guardadas nesta pasta.
# Uso (numa sessão com o token da Vercel salvo para api.vercel.com):
#   python3 pendente-publicar/publicar.py            -> publica só os sites que mudaram
#   python3 pendente-publicar/publicar.py --todos    -> publica todos, mesmo sem mudança
#   python3 pendente-publicar/publicar.py --novos    -> também cria sites novos
# Sites iguais ao que já está no ar são pulados (não gastam o limite de 100 deploys/dia da Vercel).
# Para cada site: envia só os arquivos alterados e cria um deploy de produção
# reaproveitando os demais arquivos (já existentes na Vercel) pelo manifest.json.
import json, os, subprocess, sys, time

B = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(B, '_body.json')


def api(method, url, data=None):
    a = ['curl', '-sS', '-X', method, 'https://api.vercel.com' + url, '-H', 'Content-Type: application/json']
    if data is not None:
        open(TMP, 'w').write(json.dumps(data)); a += ['--data', '@' + TMP]
    return json.loads(subprocess.run(a, capture_output=True).stdout or b'{}')


me = api('GET', '/v2/user')
if 'error' in me or me.get('user', {}).get('limited'):
    sys.exit('Token da Vercel ainda sem permissão (limited). Salve o token novo em api.vercel.com e abra uma sessão nova.')

def no_ar(proj):
    # Arquivos (caminho -> sha) da versão de produção que está no ar; None se não der para saber.
    dpl = ((proj.get('targets') or {}).get('production') or {}).get('id')
    if not dpl: return None
    t = api('GET', '/v6/deployments/%s/files' % dpl)
    if not isinstance(t, list): return None
    out = {}
    def walk(nodes, pre):
        for n in nodes:
            q = pre + '/' + n['name'] if pre else n['name']
            if n.get('type') == 'directory': walk(n.get('children') or [], q)
            else: out[q[4:] if q.startswith('src/') else q] = n.get('uid')
    walk(t, '')
    return out


sites = [d for d in sorted(os.listdir(B)) if os.path.isfile(os.path.join(B, d, 'manifest.json'))]
for site in sites:
    d = os.path.join(B, site); m = json.load(open(os.path.join(d, 'manifest.json')))
    ex = api('GET', '/v9/projects/' + (m.get('project') or m['name']))
    if 'error' in ex and not m.get('project') and '--novos' not in sys.argv:
        print(site, 'PULADO: site novo (rode com --novos amanhã)'); continue
    # Só publica o que mudou: se o que está no ar já é igual ao manifest, não gasta deploy do limite diário.
    if 'error' not in ex and '--todos' not in sys.argv:
        if no_ar(ex) == {f['file']: f['sha'] for f in m['files']}:
            print(site, 'sem mudanças (já está no ar)'); continue
    alt = os.path.join(d, 'alterados')
    for r, _, fs in os.walk(alt):
        for fn in fs:
            p = os.path.join(r, fn); rel = os.path.relpath(p, alt)
            ent = [f for f in m['files'] if f['file'] == rel][0]
            code = subprocess.run(['curl', '-sS', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'POST',
                                   'https://api.vercel.com/v2/files', '-H', 'Content-Type: application/octet-stream',
                                   '-H', 'x-vercel-digest: ' + ent['sha'], '--data-binary', '@' + p],
                                  capture_output=True, text=True).stdout
            print(site, 'upload', rel, code)
            if code != '200': print(site, 'falhou no upload'); break
    body = dict(name=m['name'], target='production', files=m['files'], projectSettings=dict(framework=None))
    if m.get('project'): body['project'] = m['project']
    dep = api('POST', '/v13/deployments?skipAutoDetectionConfirmation=1', body)
    did = dep.get('id')
    if not did: print(site, 'NÃO PUBLICOU:', (dep.get('error') or {}).get('message', dep)); continue
    for _ in range(60):
        s = api('GET', '/v13/deployments/' + did)
        if s.get('readyState') in ('READY', 'ERROR'): break
        time.sleep(4)
    print(site, s.get('readyState'), s.get('alias'))
if os.path.exists(TMP): os.remove(TMP)
