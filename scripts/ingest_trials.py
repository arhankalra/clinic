from app import app
from extensions import db
from models import ClinicalTrial
from trial_loader import load_trials

with app.app_context():
    trials = load_trials("data/trials.json")

    for t in trials:
        if not ClinicalTrial.query.filter_by(nctid=t.nctid).first():
            db.session.add(ClinicalTrial(
                nctid=t.nctid,
                title=t.title,
                condition=t.condition,
                phase=t.phase,
                status=t.status,
                city=t.city,
                state=t.state,
                country=t.country,
                summary=t.summary
            ))

    db.session.commit()
    print("Trials ingested.")
