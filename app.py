from flask import Flask, render_template, request, redirect, url_for, flash
import json, datetime, html
from werkzeug.utils import secure_filename
import os

UPLOAD_DIR = "uploads"
ALLOWED_EXT = {'json'}
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = "change-this-secret"

RARE_BRAINROTS = {"azure_cortex", "void_spike", "golden_synapse", "obsidian_core"}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT

def parse_server_export(data):
    afk_players = []
    rare_bases = []
    players = data.get("players", [])
    bases = data.get("bases", [])
    now = datetime.datetime.utcnow()
    for p in players:
        afk_flag = False
        if p.get("afk", False):
            afk_flag = True
        else:
            last_active = p.get("last_active")
            if last_active:
                try:
                    la = datetime.datetime.fromisoformat(last_active)
                    delta = (now - la).days
                    if delta >= 2:
                        afk_flag = True
                except Exception:
                    pass
        if afk_flag:
            afk_players.append({
                "name": p.get("name"),
                "id": p.get("id"),
                "last_active": p.get("last_active"),
                "note": "flagged" if p.get("afk", False) else "last active >2 days"
            })
    for b in bases:
        owner = b.get("owner")
        items = set(b.get("brainrots", []))
        found = items.intersection(RARE_BRAINROTS)
        if found:
            rare_bases.append({
                "owner": owner,
                "base_id": b.get("id"),
                "rare_brainrots": list(found),
                "item_count": len(b.get("brainrots", []))
            })
    return {"afk_players": afk_players, "rare_bases": rare_bases}

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pasted = request.form.get('paste_json', '').strip()
        upload = request.files.get('file')
        data = None
        if pasted:
            try:
                data = json.loads(pasted)
            except Exception as e:
                flash('Invalid JSON pasted: ' + str(e))
                return redirect(url_for('index'))
        elif upload and allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
            path = os.path.join(UPLOAD_DIR, filename)
            upload.save(path)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                flash('Uploaded file is not valid JSON: ' + str(e))
                return redirect(url_for('index'))
        else:
            flash('Please paste JSON or upload a .json server export file that you own.')
            return redirect(url_for('index'))
        results = parse_server_export(data)
        return render_template('result.html', results=results)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
