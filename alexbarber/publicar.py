# Publica o site da Alex Barber na Vercel (produção).
# Uso (numa sessão com o token da Vercel salvo para api.vercel.com):
#   python3 alexbarber/publicar.py
import hashlib, json, os, subprocess, sys, time

B = os.path.dirname(os.path.abspath(__file__))
NAME = 'alexbarber'
TMP = os.path.join(B, '_body.json')


def api(method, url, data=None):
    a = ['curl', '-sS', '-X', method, 'https://api.vercel.com' + url, '-H', 'Content-Type: application/json']
    if data is not None:
        open(TMP, 'w').write(json.dumps(data)); a += ['--data', '@' + TMP]
    return json.loads(subprocess.run(a, capture_output=True).stdout or b'{}')


files = []
for r, _, fs in os.walk(B):
    for fn in sorted(fs):
        p = os.path.join(r, fn); rel = os.path.relpath(p, B)
        if fn.endswith('.py') or fn.startswith('_'):
            continue
        d = open(p, 'rb').read(); sha = hashlib.sha1(d).hexdigest()
        code = subprocess.run(['curl', '-sS', '-o', '/dev/null', '-w', '%{http_code}', '-X', 'POST',
                               'https://api.vercel.com/v2/files', '-H', 'Content-Type: application/octet-stream',
                               '-H', 'x-vercel-digest: ' + sha, '--data-binary', '@' + p],
                              capture_output=True, text=True).stdout
        print('upload', rel, code)
        if code != '200':
            sys.exit('falha no upload de ' + rel)
        files.append(dict(file=rel, sha=sha, size=len(d)))

dep = api('POST', '/v13/deployments?skipAutoDetectionConfirmation=1',
          dict(name=NAME, target='production', files=files, projectSettings=dict(framework=None)))
did = dep.get('id')
if not did:
    sys.exit(json.dumps(dep))
for _ in range(60):
    s = api('GET', '/v13/deployments/' + did)
    if s.get('readyState') in ('READY', 'ERROR'):
        break
    time.sleep(4)
print(s.get('readyState'), s.get('alias'))
if os.path.exists(TMP):
    os.remove(TMP)
