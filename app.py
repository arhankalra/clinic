from flask import Flask, render_template, request, redirect, url_for, session, flash
from pathlib import Path
import json
from db import get_db, init_db
from models import Trial, load_trials

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'  # replace in production
app.config['TRIALS_JSON'] = str(Path(__file__).parent / 'data' / 'trials.sample.json')
app.config['DB_PATH'] = str(Path(__file__).parent / 'app.db')

with app.app_context():
    init_db(app.config['DB_PATH'])

@app.before_request
def ensure_user():
    if 'username' not in session:
        session['username'] = 'demo'

TRIALS = load_trials(app.config['TRIALS_JSON'])
TRIALS_BY_ID = {t.nctid: t for t in TRIALS}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/trials')
def trials():
    q = (request.args.get('q') or '').strip().lower()
    condition = (request.args.get('condition') or '').strip().lower()
    phase = (request.args.get('phase') or '').strip()
    status = (request.args.get('status') or '').strip()
    location = (request.args.get('location') or '').strip().lower()

    filtered = []
    for t in TRIALS:
        if q and (q not in t.title.lower() and q not in t.summary.lower()):
            continue
        if condition and condition not in t.condition.lower():
            continue
        if phase and phase != t.phase:
            continue
        if status and status != t.status:
            continue
        if location and (location not in t.city.lower() and location not in t.state.lower() and location not in t.country.lower()):
            continue
        filtered.append(t)

    filtered.sort(key=lambda x: x.title)

    return render_template('trials.html', trials=filtered, count=len(filtered), query={
        'q': q, 'condition': condition, 'phase': phase, 'status': status, 'location': location
    })

@app.route('/trial/<nctid>')
def trial_detail(nctid):
    t = TRIALS_BY_ID.get(nctid)
    if not t:
        flash('Trial not found.', 'error')
        return redirect(url_for('trials'))
    db = get_db()
    row = db.execute('SELECT 1 FROM favorites WHERE username=? AND nctid=?', (session['username'], nctid)).fetchone()
    is_favorite = bool(row)
    return render_template('trial_detail.html', t=t, is_favorite=is_favorite)

@app.route('/favorite/<nctid>', methods=['POST'])
def toggle_favorite(nctid):
    t = TRIALS_BY_ID.get(nctid)
    if not t:
        flash('Trial not found.', 'error')
        return redirect(url_for('trials'))
    db = get_db()
    row = db.execute('SELECT 1 FROM favorites WHERE username=? AND nctid=?', (session['username'], nctid)).fetchone()
    if row:
        db.execute('DELETE FROM favorites WHERE username=? AND nctid=?', (session['username'], nctid))
        db.commit()
        flash('Removed from favorites.', 'info')
    else:
        db.execute('INSERT INTO favorites(username, nctid) VALUES(?, ?)', (session['username'], nctid))
        db.commit()
        flash('Added to favorites!', 'success')
    return redirect(request.referrer or url_for('trial_detail', nctid=nctid))

@app.route('/favorites')
def favorites():
    db = get_db()
    rows = db.execute('SELECT nctid FROM favorites WHERE username=?', (session['username'],)).fetchall()
    fav_ids = {r['nctid'] for r in rows}
    fav_trials = [TRIALS_BY_ID[n] for n in fav_ids if n in TRIALS_BY_ID]
    fav_trials.sort(key=lambda x: x.title)
    return render_template('favorites.html', trials=fav_trials)

@app.route('/swipe')
def swipe():
    return render_template('swipe.html', trials=TRIALS)

if __name__ == '__main__':
    app.run(debug=True)
