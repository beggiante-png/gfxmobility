# Troca as fotos da Pizza G Três Queijos e da Pizza G Pepperoni no cardápio da La Pizza's.
# Uso: python3 pendente-publicar/lapizzas/fotos-cardapio/aplicar.py
import json, os, subprocess, time
P = 'hkqicvssabntmaoifyau'
D = os.path.dirname(os.path.abspath(__file__))
FOTOS = {'Três Queijos': 'Pizza-G-Tres-Queijos.jpg', 'Pepperoni': 'Pizza-G-Pepperoni.jpg'}


def api(m, u, data=None):
    a = ['curl', '-sS', '-X', m, 'https://api.supabase.com/v1/projects/' + P + u, '-H', 'Content-Type: application/json']
    if data is not None:
        a += ['--data', json.dumps(data)]
    return json.loads(subprocess.run(a, capture_output=True).stdout)


SK = [k['api_key'] for k in api('GET', '/api-keys?reveal=true') if k['name'] == 'service_role'][0]
upd = {}
for nome, arq in FOTOS.items():
    n = 'g_%s_%d.jpg' % (arq[8:-4].lower(), int(time.time()))
    r = subprocess.run(['curl', '-sS', '-X', 'POST', 'https://%s.supabase.co/storage/v1/object/lps/produtos/%s' % (P, n),
                        '-H', 'Authorization: Bearer ' + SK, '-H', 'apikey: ' + SK, '-H', 'Content-Type: image/jpeg',
                        '--data-binary', '@' + os.path.join(D, arq)], capture_output=True, text=True).stdout
    if '"Key"' not in r:
        raise SystemExit('Falhou o envio de %s: %s' % (arq, r))
    upd[nome] = 'https://%s.supabase.co/storage/v1/object/public/lps/produtos/%s' % (P, n)
    time.sleep(1)
m = json.dumps(upd, ensure_ascii=False).replace("'", "''")
q = ("update lps_store set products=(select jsonb_agg(case when ('%s'::jsonb) ? (e->>'name') then jsonb_set(e,'{image}',('%s'::jsonb)->(e->>'name')) else e end order by o) "
     "from jsonb_array_elements(products) with ordinality t(e,o)), updated_at=now() returning (select count(*) from jsonb_array_elements(products) e where e->>'image' like '%%/g_%%')") % (m, m)
print(api('POST', '/database/query', {'query': q}))
print('Pronto:', ', '.join(upd))
