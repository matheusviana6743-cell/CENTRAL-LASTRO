from pathlib import Path
import re

p = Path('central_lastro.py')
s = p.read_text()

def rep(old, new, n=1):
    global s
    if old not in s:
        raise SystemExit('Pattern not found: ' + old[:120].replace('\n', ' '))
    s = s.replace(old, new, n)

# Keep legacy records financially active as won.
rep("    c.commit()\n    c.close()\n\n    # CSRF para POSTs autenticados", "    c.execute(\"UPDATE action_records SET status='GANHADA' WHERE status='FINALIZADA'\")\n\n    c.commit()\n    c.close()\n\n    # CSRF para POSTs autenticados")

# Dashboard: only won actions affect financial totals.
rep("        FROM action_records\n        '''\n    )[0]['v']", "        FROM action_records\n        WHERE status='GANHADA'\n        '''\n    )[0]['v']", 1)
rep("        WHERE week_start=?\n        ''',\n        (ws,)\n    )[0]['v']", "        WHERE week_start=?\n        AND status='GANHADA'\n        ''',\n        (ws,)\n    )[0]['v']", 1)

# Dashboard charts/statistics.
marker = "    action_cards = []\n"
extra = """    week_participants = getall('''SELECT COALESCE(SUM(participant_pool),0) v FROM action_records WHERE week_start=? AND status='GANHADA' ''', (ws,))[0]['v']
    week_won = getall('''SELECT COUNT(*) n FROM action_records WHERE week_start=? AND status='GANHADA' ''', (ws,))[0]['n']
    week_lost = getall('''SELECT COUNT(*) n FROM action_records WHERE week_start=? AND status='PERDIDA' ''', (ws,))[0]['n']
    total_week_actions = week_won + week_lost
    won_pct = round(week_won * 100 / total_week_actions, 1) if total_week_actions else 0
    lost_pct = round(week_lost * 100 / total_week_actions, 1) if total_week_actions else 0
    family_total = float(week_total or 0)
    participant_total = float(week_participants or 0)
    financial_total = family_total + participant_total
    family_pct = round(family_total * 100 / financial_total, 1) if financial_total else 50
    participant_pct = round(participant_total * 100 / financial_total, 1) if financial_total else 50

"""
if marker not in s or 'week_participants = getall' in s:
    raise SystemExit('Dashboard marker missing or already changed')
s = s.replace(marker, extra + marker, 1)

marker = "        <div class=\"section\">\n\n            <h2>\n                Ações da semana\n            </h2>"
chart = """        <div class="section">
            <div class="cards3">
                <div class="card">
                    <div class="label">Resultado das ações · semana</div>
                    <div style="height:18px;background:#211b0c;border-radius:999px;overflow:hidden;margin:14px 0 8px"><div style="height:100%;width:{won_pct}%;background:var(--gold);float:left"></div><div style="height:100%;width:{lost_pct}%;background:#71312e;float:left"></div></div>
                    <div class="split"><span class="status-ok">Ganhadas: {week_won} · {won_pct}%</span><span class="status-no">Perdidas: {week_lost} · {lost_pct}%</span></div>
                </div>
                <div class="card">
                    <div class="label">Divisão financeira · ganhadas</div>
                    <div style="width:150px;height:150px;border-radius:50%;margin:16px auto;background:conic-gradient(var(--gold) 0 {family_pct}%, #5b4a22 {family_pct}% 100%);display:grid;place-items:center"><div style="width:92px;height:92px;border-radius:50%;background:#0b0b09;display:grid;place-items:center;text-align:center;font-weight:800">{family_pct}%<br><span class="muted" style="font-size:10px">FAMÍLIA</span></div></div>
                    <div class="split"><span>Família: {family_pct}%</span><span>Participantes: {participant_pct}%</span></div>
                </div>
                <div class="card">
                    <div class="label">Valores da semana</div>
                    <p>Família: <b>{money(family_total)}</b></p>
                    <p>Participantes: <b>{money(participant_total)}</b></p>
                    <p class="muted">Ações perdidas não movimentam o painel financeiro.</p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Ações da semana</h2>"""
rep(marker, chart, 1)

# Remove Bandido/Polícia choice from action cards and registration.
rep('''                <p class="muted">\n                    Bandidos:\n                    {data.get("bandits","—")}\n                    ·\n                    Policiais:\n                    {data.get("police","—")}\n                </p>\n''', '''                <p class="muted">\n                    Participantes: {data.get("bandits","—")}\n                </p>\n''', 1)
rep("""            side = request.form.get(
                f'side_{mid}',
                'BANDIDO'
            )

""", '', 1)
rep("""            side = request.form.get(
                f'external_side_{i}',
                'BANDIDO'
            )

""", '', 1)
rep("                    side,\n                    participant_eligible\n", "                    'BANDIDO',\n                    participant_eligible\n", 2)

old_counts = """        b = sum(
            1
            for x in participants
            if x[3] == 'BANDIDO'
        )

        p = sum(
            1
            for x in participants
            if x[3] == 'POLICIAL'
        )
"""
rep(old_counts, "        b = len(participants)\n", 1)
old_validate = """        if (
            not check_count(
                rules.get('bandits'),
                b
            )
            or
            not check_count(
                rules.get('police'),
                p
            )
        ):

            flash(
                f'Quantidade inválida. '
                f'Bandidos: {b}. '
                f'Policiais: {p}.',
                'error'
            )

            return redirect(
                request.url
            )
"""
rep(old_validate, """        if not check_count(rules.get('bandits'), b):
            flash(f'Quantidade inválida. Participantes: {b}.', 'error')
            return redirect(request.url)

        result_status = request.form.get('status', 'GANHADA').upper()
        if result_status not in ('GANHADA', 'PERDIDA'):
            flash('Resultado da ação inválido.', 'error')
            return redirect(request.url)
""", 1)

# Lost actions save history but create no financial movement.
rep("""            family = round(
                value * .5,
                2
            )

            pool = round(
                value - family,
                2
            )
""", """            family = round(value * .5, 2) if result_status == 'GANHADA' else 0
            pool = round(value - family, 2) if result_status == 'GANHADA' else 0
""", 1)
rep("                if x[4]\n            ]", "                if x[4] and result_status == 'GANHADA'\n            ]", 1)
rep("                    created_at\n                )\n                VALUES(?,?,?,?,?,?,?,?)", "                    created_at,\n                    status\n                )\n                VALUES(?,?,?,?,?,?,?,?,?)", 1)
rep("                    session['uid'],\n                    now()\n                )\n            ).lastrowid", "                    session['uid'],\n                    now(),\n                    result_status\n                )\n            ).lastrowid", 1)
start = s.find("            c.execute(\n                '''\n                INSERT INTO financial_transactions(", s.find("rid = c.execute"))
end = s.find("            idx = 0", start)
if start < 0 or end < 0:
    raise SystemExit('Financial transaction block not found')
block = s[start:end]
block = '\n'.join(('    '+line) if line else line for line in block.splitlines())
s = s[:start] + "            if result_status == 'GANHADA':\n\n" + block + "\n" + s[end:]
rep("                ok = bool(participant_eligible)", "                ok = bool(participant_eligible) and result_status == 'GANHADA'", 1)
rep("                    'Não elegível para a divisão',", "                    ('Ação perdida' if result_status == 'PERDIDA' else 'Não elegível para a divisão'),", 1)

# Remove team selectors in registration HTML.
s = re.sub(r"\n                        <div class=\"field\">\n\n                            <label>\n                                Equipe\n                            </label>\n\n                            <select\n                                class=\"select\"\n                                data-side\n                            >.*?                            </select>\n\n                        </div>\n", "\n", s, count=1, flags=re.S)
s = re.sub(r"\n                        <div class=\"field\">\n\n                            <label>\n                                Equipe\n                            </label>\n\n                            <select\n                                class=\"select\"\n                                name=\"external_side_\$\{\{i\}\}\"\n                            >.*?                            </select>\n\n                        </div>\n", "\n", s, count=1, flags=re.S)
rep('                <option value="0">Não elegível</option>\n                <option value="1">Elegível</option>', '                <option value="1">Participa da divisão</option>\n                <option value="0">Não participa da divisão</option>', 2)
rep("        let side =\n            r.querySelector(\n                '[data-side]'\n            );\n\n", '', 1)
rep("        side.name =\n            'side_' + s.value;\n\n", '', 1)

# Result page: show status for all participants.
old = re.search(r"    ok = ''.join\(.*?\n    return shell\(", s, re.S)
if not old:
    raise SystemExit('Result participant block not found')
new = '''    participants_html = ''.join(
        f'''<tr>
            <td>{p["member_name"] or p["external_name"]}</td>
            <td>{p["passport"] or p["external_pass"] or "—"}</td>
            <td class="{'status-ok' if r['status']=='GANHADA' else 'status-no'}">{r['status'].title()}</td>
            <td>{money(p["value_received"])}</td>
            <td>{p["reason"] or "—"}</td>
        </tr>'''
        for p in people
    )

    return shell('''
s = s[:old.start()] + new + s[old.end():]
rep('''                <div class="label">
                    Valor da ação
                </div>''', '''                <div class="label">
                    Resultado
                </div>
                <div class="metric">
                    {r["status"].title()}
                </div>
            </div>

            <div class="card">
                <div class="label">
                    Valor da ação
                </div>''', 1)
rep('<h2>\n                Participantes elegíveis\n            </h2>', '<h2>Participantes da ação</h2>', 1)
rep('<th>Equipe</th>\n                    <th>Recebeu</th>', '<th>Resultado</th>\n                    <th>Recebeu</th>', 1)
rep('                {ok}\n', '                {participants_html}\n', 1)
s = re.sub(r"\n        <div class=\"card section tablewrap\">\n\n            <h2>\n                Não elegíveis\n            </h2>.*?\n        </div>\n        '''", "\n        </div>\n        '''", s, count=1, flags=re.S)

# Member list links to profile.
rep("                <td>{m['name']}</td>", "                <td><a href=\"{url_for('member_profile', member_id=m['id'])}\">{m['name']}</a></td>", 1)

# Member profile/history.
marker = "# ============================================================\n# EDITAR MEMBRO\n# ============================================================\n"
profile = '''# ============================================================
# PERFIL DO MEMBRO
# ============================================================

@app.get('/members/<int:member_id>')
@auth
def member_profile(member_id):
    rows = getall('SELECT * FROM members WHERE id=?', (member_id,))
    if not rows:
        abort(404)
    m = rows[0]
    action_rows = getall("""
        SELECT ar.id record_id, ar.status, ar.created_at, ar.action_value, ap.value_received, a.name action_name
        FROM action_participants ap
        JOIN action_records ar ON ar.id=ap.record_id
        JOIN actions a ON a.id=ar.action_id
        WHERE ap.member_id=?
        ORDER BY ar.created_at DESC
    """, (member_id,))
    won = sum(1 for r in action_rows if r['status'] == 'GANHADA')
    lost = sum(1 for r in action_rows if r['status'] == 'PERDIDA')
    received = sum(float(r['value_received'] or 0) for r in action_rows if r['status'] == 'GANHADA')
    rows_html = ''.join(f"""
        <tr>
            <td>{r['action_name']}</td>
            <td class="{'status-ok' if r['status']=='GANHADA' else 'status-no'}">{r['status'].title()}</td>
            <td>{money(r['action_value'])}</td>
            <td>{money(r['value_received'])}</td>
            <td>{r['created_at'][:16].replace('T',' ')}</td>
            <td><a href="{url_for('result', record_id=r['record_id'])}">Abrir</a></td>
        </tr>
    """ for r in action_rows)
    return shell('Perfil · ' + m['name'], f"""
        <div class="grid">
            <div class="card"><div class="label">Cargo</div><div class="metric" style="font-size:20px">{m['cargo']}</div></div>
            <div class="card"><div class="label">Passaporte</div><div class="metric">{m['passport'] or '—'}</div></div>
            <div class="card"><div class="label">Ações ganhadas</div><div class="metric">{won}</div></div>
            <div class="card"><div class="label">Ações perdidas</div><div class="metric">{lost}</div></div>
        </div>
        <div class="card section"><div class="label">Total recebido em ações ganhadas</div><div class="metric">{money(received)}</div></div>
        <div class="card section tablewrap">
            <h2>Histórico de ações</h2>
            <table class="table">
                <tr><th>Ação</th><th>Resultado</th><th>Valor da ação</th><th>Recebeu</th><th>Data</th><th></th></tr>
                {rows_html or '<tr><td colspan="6" class="muted">Nenhuma ação registrada.</td></tr>'}
            </table>
        </div>
    """)


'''
if marker not in s:
    raise SystemExit('Member marker not found')
s = s.replace(marker, profile + marker, 1)

p.write_text(s)
