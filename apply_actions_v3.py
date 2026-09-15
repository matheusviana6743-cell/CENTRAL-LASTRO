from pathlib import Path
import re
p=Path('central_lastro.py'); s=p.read_text()
def once(old,new,n=1):
    global s
    if old not in s: raise SystemExit('missing: '+old[:100])
    s=s.replace(old,new,n)
once("    c.commit()\n    c.close()\n\n    # CSRF para POSTs autenticados", "    c.execute(\"UPDATE action_records SET status='GANHADA' WHERE status='FINALIZADA'\")\n\n    c.commit()\n    c.close()\n\n    # CSRF para POSTs autenticados")
once("        FROM action_records\n        '''\n    )[0]['v']", "        FROM action_records\n        WHERE status='GANHADA'\n        '''\n    )[0]['v']")
once("        WHERE week_start=?\n        ''',\n        (ws,)\n    )[0]['v']", "        WHERE week_start=?\n        AND status='GANHADA'\n        ''',\n        (ws,)\n    )[0]['v']")
marker='    action_cards = []\n'
extra="    week_participants = getall(\"SELECT COALESCE(SUM(participant_pool),0) v FROM action_records WHERE week_start=? AND status='GANHADA'\", (ws,))[0]['v']\n    week_won = getall(\"SELECT COUNT(*) n FROM action_records WHERE week_start=? AND status='GANHADA'\", (ws,))[0]['n']\n    week_lost = getall(\"SELECT COUNT(*) n FROM action_records WHERE week_start=? AND status='PERDIDA'\", (ws,))[0]['n']\n    total_week_actions = week_won + week_lost\n    won_pct = round(week_won*100/total_week_actions,1) if total_week_actions else 0\n    lost_pct = round(week_lost*100/total_week_actions,1) if total_week_actions else 0\n    family_total = float(week_total or 0)\n    participant_total = float(week_participants or 0)\n    financial_total = family_total + participant_total\n    family_pct = round(family_total*100/financial_total,1) if financial_total else 50\n    participant_pct = round(participant_total*100/financial_total,1) if financial_total else 50\n\n"
once(marker,extra+marker)
marker="        <div class=\"section\">\n\n            <h2>\n                Ações da semana\n            </h2>"
chart='''        <div class="section"><div class="cards3"><div class="card"><div class="label">Resultado das ações · semana</div><div style="height:18px;background:#211b0c;border-radius:999px;overflow:hidden;margin:14px 0 8px"><div style="height:100%;width:{won_pct}%;background:var(--gold);float:left"></div><div style="height:100%;width:{lost_pct}%;background:#71312e;float:left"></div></div><div class="split"><span class="status-ok">Ganhadas: {week_won} · {won_pct}%</span><span class="status-no">Perdidas: {week_lost} · {lost_pct}%</span></div></div><div class="card"><div class="label">Divisão financeira · ganhadas</div><div style="width:150px;height:150px;border-radius:50%;margin:16px auto;background:conic-gradient(var(--gold) 0 {family_pct}%, #5b4a22 {family_pct}% 100%);display:grid;place-items:center"><div style="width:92px;height:92px;border-radius:50%;background:#0b0b09;display:grid;place-items:center;text-align:center;font-weight:800">{family_pct}%<br><span class="muted" style="font-size:10px">FAMÍLIA</span></div></div><div class="split"><span>Família: {family_pct}%</span><span>Participantes: {participant_pct}%</span></div></div><div class="card"><div class="label">Valores da semana</div><p>Família: <b>{money(family_total)}</b></p><p>Participantes: <b>{money(participant_total)}</b></p><p class="muted">Ações perdidas não movimentam o painel financeiro.</p></div></div></div><div class="section"><h2>Ações da semana</h2>'''
once(marker,chart)
once('''                <p class="muted">\n                    Bandidos:\n                    {data.get("bandits","—")}\n                    ·\n                    Policiais:\n                    {data.get("police","—")}\n                </p>\n''','''                <p class="muted">\n                    Participantes: {data.get("bandits","—")}\n                </p>\n''')
s=re.sub(r"\n            side = request\.form\.get\(\n                f'side_\{mid\}',\n                'BANDIDO'\n            \)\n",'\n',s,count=1)
s=re.sub(r"\n            side = request\.form\.get\(\n                f'external_side_\{i\}',\n                'BANDIDO'\n            \)\n",'\n',s,count=1)
s=s.replace('                    side,\n                    participant_eligible\n',"                    'BANDIDO',\n                    participant_eligible\n",2)
once("""        b = sum(
            1
            for x in participants
            if x[3] == 'BANDIDO'
        )

        p = sum(
            1
            for x in participants
            if x[3] == 'POLICIAL'
        )
""","        b = len(participants)\n")
once("""        if (
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
""","""        if not check_count(rules.get('bandits'), b):
            flash(f'Quantidade inválida. Participantes: {b}.', 'error')
            return redirect(request.url)

        result_status = request.form.get('status', 'GANHADA').upper()
        if result_status not in ('GANHADA', 'PERDIDA'):
            flash('Resultado da ação inválido.', 'error')
            return redirect(request.url)
""")
once("""            family = round(
                value * .5,
                2
            )

            pool = round(
                value - family,
                2
            )
""","""            family = round(value * .5, 2) if result_status == 'GANHADA' else 0
            pool = round(value - family, 2) if result_status == 'GANHADA' else 0
""")
once('                if x[4]\n            ]',"                if x[4] and result_status == 'GANHADA'\n            ]")
once('                    created_at\n                )\n                VALUES(?,?,?,?,?,?,?,?)','                    created_at,\n                    status\n                )\n                VALUES(?,?,?,?,?,?,?,?,?)')
once("                    session['uid'],\n                    now()\n                )\n            ).lastrowid","                    session['uid'],\n                    now(),\n                    result_status\n                )\n            ).lastrowid")
start=s.find("            c.execute(\n                '''\n                INSERT INTO financial_transactions(",s.find('rid = c.execute'))
end=s.find('            idx = 0',start)
if start<0 or end<0: raise SystemExit('finance block missing')
block=s[start:end]
block='\n'.join(('    '+x) if x else x for x in block.splitlines())
s=s[:start]+"            if result_status == 'GANHADA':\n\n"+block+'\n'+s[end:]
once('                ok = bool(participant_eligible)',"                ok = bool(participant_eligible) and result_status == 'GANHADA'")
once("                    'Não elegível para a divisão',","                    ('Ação perdida' if result_status == 'PERDIDA' else 'Não elegível para a divisão'),")
s=re.sub(r"\n                        <div class=\"field\">\n\n                            <label>\n                                Equipe\n                            </label>\n\n                            <select\n                                class=\"select\"\n                                data-side\n                            >.*?                            </select>\n\n                        </div>\n",'\n',s,count=1,flags=re.S)
s=re.sub(r"\n                        <div class=\"field\">\n\n                            <label>\n                                Equipe\n                            </label>\n\n                            <select\n                                class=\"select\"\n                                name=\"external_side_\$\{\{i\}\}\"\n                            >.*?                            </select>\n\n                        </div>\n",'\n',s,count=1,flags=re.S)
s=s.replace('                <option value="0">Não elegível</option>\n                <option value="1">Elegível</option>','                <option value="1">Participa da divisão</option>\n                <option value="0">Não participa da divisão</option>',2)
s=s.replace("        let side =\n            r.querySelector(\n                '[data-side]'\n            );\n\n",'',1)
s=s.replace("        side.name =\n            'side_' + s.value;\n\n",'',1)
button='            <button\n                class="btn section"\n                style="width:100%"\n            >\n                Finalizar ação\n            </button>'
selector='            <div class="field section">\n                <label>Resultado da ação</label>\n                <select class="select" name="status" required>\n                    <option value="GANHADA">Ganhada</option>\n                    <option value="PERDIDA">Perdida</option>\n                </select>\n                <span class="muted">Ações perdidas ficam no histórico, mas não movimentam o painel financeiro.</span>\n            </div>\n\n'+button
once(button,selector)
p.write_text(s)
