from pathlib import Path
import re

p = Path('central_lastro.py')
s = p.read_text()

def once(old, new):
    global s
    if old not in s:
        raise SystemExit('missing pattern: ' + old[:100])
    s = s.replace(old, new, 1)

# Preserve old financial records as successful actions.
once("    c.commit()\n    c.close()\n\n    # CSRF para POSTs autenticados", "    c.execute(\"UPDATE action_records SET status='GANHADA' WHERE status='FINALIZADA'\")\n\n    c.commit()\n    c.close()\n\n    # CSRF para POSTs autenticados")

# Dashboard financial totals ignore lost actions.
once("        FROM action_records\n        '''\n    )[0]['v']", "        FROM action_records\n        WHERE status='GANHADA'\n        '''\n    )[0]['v']")
once("        WHERE week_start=?\n        ''',\n        (ws,)\n    )[0]['v']", "        WHERE week_start=?\n        AND status='GANHADA'\n        ''',\n        (ws,)\n    )[0]['v']")

# Weekly outcome/financial percentages.
marker = "    action_cards = []\n"
extra = "    week_participants = getall(\"SELECT COALESCE(SUM(participant_pool),0) v FROM action_records WHERE week_start=? AND status='GANHADA'\", (ws,))[0]['v']\n    week_won = getall(\"SELECT COUNT(*) n FROM action_records WHERE week_start=? AND status='GANHADA'\", (ws,))[0]['n']\n    week_lost = getall(\"SELECT COUNT(*) n FROM action_records WHERE week_start=? AND status='PERDIDA'\", (ws,))[0]['n']\n    total_week_actions = week_won + week_lost\n    won_pct = round(week_won * 100 / total_week_actions, 1) if total_week_actions else 0\n    lost_pct = round(week_lost * 100 / total_week_actions, 1) if total_week_actions else 0\n    family_total = float(week_total or 0)\n    participant_total = float(week_participants or 0)\n    financial_total = family_total + participant_total\n    family_pct = round(family_total * 100 / financial_total, 1) if financial_total else 50\n    participant_pct = round(participant_total * 100 / financial_total, 1) if financial_total else 50\n\n"
if 'week_participants = getall' not in s:
    once(marker, extra + marker)

# Remove police/bandit selector from action cards.
old_card = '                <p class="muted">\n                    Bandidos:\n                    {data.get("bandits","—")}\n                    ·\n                    Policiais:\n                    {data.get("police","—")}\n                </p>\n'
new_card = '                <p class="muted">\n                    Participantes: {data.get("bandits","—")}\n                </p>\n'
once(old_card, new_card)

# Backend: all selected people are simply participants.
s = re.sub(r"\n            side = request\.form\.get\(\n                f'side_\{mid\}',\n                'BANDIDO'\n            \)\n", '\n', s, count=1)
s = re.sub(r"\n            side = request\.form\.get\(\n                f'external_side_\{i\}',\n                'BANDIDO'\n            \)\n", '\n', s, count=1)
s = s.replace('                    side,\n                    participant_eligible\n', "                    'BANDIDO',\n                    participant_eligible\n", 2)

# Replace side-count validation with participant count and result.
s = re.sub(r"        b = sum\(.*?\n        p = sum\(.*?\n", "        b = len(participants)\n", s, count=1, flags=re.S)
pat = re.compile(r"        if \(\n            not check_count\(\n                rules\.get\('bandits'\),\n                b\n            \)\n            or.*?            return redirect\(\n                request\.url\n            \)\n", re.S)
if not pat.search(s):
    raise SystemExit('side validation block not found')
s = pat.sub("        if not check_count(rules.get('bandits'), b):\n            flash(f'Quantidade inválida. Participantes: {b}.', 'error')\n            return redirect(request.url)\n\n        result_status = request.form.get('status', 'GANHADA').upper()\n        if result_status not in ('GANHADA', 'PERDIDA'):\n            flash('Resultado da ação inválido.', 'error')\n            return redirect(request.url)\n", s, count=1)

# Lost actions keep records but pay nothing.
s = re.sub(r"            family = round\(\n                value \* \.5,\n                2\n            \)\n\n            pool = round\(\n                value - family,\n                2\n            \)", "            family = round(value * .5, 2) if result_status == 'GANHADA' else 0\n            pool = round(value - family, 2) if result_status == 'GANHADA' else 0", s, count=1)
once('                if x[4]\n            ]', "                if x[4] and result_status == 'GANHADA'\n            ]")
once('                    created_at\n                )\n                VALUES(?,?,?,?,?,?,?,?)', '                    created_at,\n                    status\n                )\n                VALUES(?,?,?,?,?,?,?,?,?)')
once("                    session['uid'],\n                    now()\n                )\n            ).lastrowid", "                    session['uid'],\n                    now(),\n                    result_status\n                )\n            ).lastrowid")
start = s.find("            c.execute(\n                '''\n                INSERT INTO financial_transactions(", s.find('rid = c.execute'))
end = s.find('            idx = 0', start)
if start < 0 or end < 0:
    raise SystemExit('financial block not found')
block = s[start:end]
block = '\n'.join(('    ' + x) if x else x for x in block.splitlines())
s = s[:start] + "            if result_status == 'GANHADA':\n\n" + block + '\n' + s[end:]
once('                ok = bool(participant_eligible)', "                ok = bool(participant_eligible) and result_status == 'GANHADA'")
once("                    'Não elegível para a divisão',", "                    ('Ação perdida' if result_status == 'PERDIDA' else 'Não elegível para a divisão'),")

# Remove team selectors from the form.
s = re.sub(r"\n                        <div class=\"field\">\n\n                            <label>\n                                Equipe\n                            </label>\n\n                            <select\n                                class=\"select\"\n                                data-side\n                            >.*?                            </select>\n\n                        </div>\n", '\n', s, count=1, flags=re.S)
s = re.sub(r"\n                        <div class=\"field\">\n\n                            <label>\n                                Equipe\n                            </label>\n\n                            <select\n                                class=\"select\"\n                                name=\"external_side_\$\{\{i\}\}\"\n                            >.*?                            </select>\n\n                        </div>\n", '\n', s, count=1, flags=re.S)
s = s.replace('                <option value="0">Não elegível</option>\n                <option value="1">Elegível</option>', '                <option value="1">Participa da divisão</option>\n                <option value="0">Não participa da divisão</option>', 2)
s = s.replace("        let side =\n            r.querySelector(\n                '[data-side]'\n            );\n\n", '', 1)
s = s.replace("        side.name =\n            'side_' + s.value;\n\n", '', 1)

# Add result selector before Finalizar ação.
button = '            <button\n                class="btn section"\n                style="width:100%"\n            >\n                Finalizar ação\n            </button>'
selector = '            <div class="field section">\n                <label>Resultado da ação</label>\n                <select class="select" name="status" required>\n                    <option value="GANHADA">Ganhada</option>\n                    <option value="PERDIDA">Perdida</option>\n                </select>\n                <span class="muted">Ações perdidas ficam no histórico, mas não movimentam o painel financeiro.</span>\n            </div>\n\n' + button
once(button, selector)

p.write_text(s)
