from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from pathlib import Path
from extensions import db, migrate, login_manager, bcrypt
from models import User, Favorite, ClinicalTrial
from models import UserProfile
from sqlalchemy import case, or_


# --------------------
# App setup
# --------------------
app = Flask(__name__)

app.config["SECRET_KEY"] = "dev-secret-key"  # replace later
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["DB_PATH"] = str(Path(__file__).parent / "app.db")


# --------------------
# Initialize extensions
# --------------------
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)
bcrypt.init_app(app)

login_manager.login_view = "auth.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Routes
@app.route("/")
def index():
    return render_template("index.html")


# Profile
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()

    if request.method == "POST":
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.session.add(profile)

        profile.age = request.form.get("age")
        profile.condition = request.form.get("condition")
        profile.city = request.form.get("city")
        profile.state = request.form.get("state")
        profile.country = request.form.get("country")

        db.session.commit()
        flash("Profile updated", "success")
        return redirect(url_for("profile"))

    return render_template("profile.html", profile=profile)


# Trials search (DB-backed)
@app.route("/trials")
def trials():
    q = request.args.get("q", "").strip().lower()
    condition = request.args.get("condition", "").strip().lower()
    phase = request.args.get("phase", "").strip()
    status = request.args.get("status", "").strip()
    location = request.args.get("location", "").strip().lower()

    if not condition and current_user.is_authenticated and current_user.profile:
        if current_user.profile.condition:
            condition = current_user.profile.condition.lower()

    query = ClinicalTrial.query

    if q:
        query = query.filter(
            (ClinicalTrial.title.ilike(f"%{q}%")) |
            (ClinicalTrial.summary.ilike(f"%{q}%"))
        )

    if condition:
        query = query.filter(ClinicalTrial.condition.ilike(f"%{condition}%"))

    if phase:
        query = query.filter_by(phase=phase)

    if status:
        query = query.filter_by(status=status)

    if location:
        query = query.filter(
            (ClinicalTrial.city.ilike(f"%{location}%")) |
            (ClinicalTrial.state.ilike(f"%{location}%")) |
            (ClinicalTrial.country.ilike(f"%{location}%"))
        )

    # ranking logic
    score = case((True, 0))

    # condition relevance
    if condition:
        score += case(
            (ClinicalTrial.condition.ilike(f"%{condition}%"), 3),
            else_=0
        )

    # recruiting first
    score += case(
        (ClinicalTrial.status.ilike("%recruit%"), 2),
        else_=0
    )

    # phase preference
    score += case(
        (ClinicalTrial.phase.in_(["Phase 2", "Phase II", "Phase 3", "Phase III"]), 1),
        else_=0
    )

    # location relevance
    if location:
        score += case(
            (
                or_(
                    ClinicalTrial.city.ilike(f"%{location}%"),
                    ClinicalTrial.state.ilike(f"%{location}%"),
                    ClinicalTrial.country.ilike(f"%{location}%"),
                ),
                1
            ),
            else_=0
        )

    results = query.add_columns(score.label("score")) \
                .order_by(score.desc(), ClinicalTrial.title.asc()) \
                .all()

    # unpack rows (SQLAlchemy returns tuples)
    results = [row[0] for row in results]


    return render_template(
    "trials.html",
    trials=results,
    count=len(results),
    query={
        "q": q,
        "condition": condition,
        "phase": phase,
        "status": status,
        "location": location
    }
)



# Trial detail
@app.route("/trial/<nctid>")
def trial_detail(nctid):
    t = ClinicalTrial.query.filter_by(nctid=nctid).first()
    if not t:
        flash("Trial not found.", "error")
        return redirect(url_for("trials"))

    is_favorite = False
    if current_user.is_authenticated:
        is_favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            nctid=nctid
        ).first() is not None

    return render_template("trial_detail.html", t=t, is_favorite=is_favorite)


# Toggle favorite
@app.route("/favorite/<nctid>", methods=["POST"])
@login_required
def toggle_favorite(nctid):
    t = ClinicalTrial.query.filter_by(nctid=nctid).first()
    if not t:
        flash("Trial not found.", "error")
        return redirect(url_for("trials"))

    fav = Favorite.query.filter_by(
        user_id=current_user.id,
        nctid=nctid
    ).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash("Removed from favorites.", "info")
    else:
        db.session.add(Favorite(
            user_id=current_user.id,
            nctid=nctid
        ))
        db.session.commit()
        flash("Added to favorites!", "success")

    return redirect(request.referrer or url_for("trial_detail", nctid=nctid))


# Favorites page
@app.route("/favorites")
@login_required
def favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    fav_ids = {f.nctid for f in favs}

    trials = ClinicalTrial.query.filter(
        ClinicalTrial.nctid.in_(fav_ids)
    ).order_by(ClinicalTrial.title).all()

    return render_template("favorites.html", trials=trials)


# Swipe mode (protected)
@app.route("/swipe")
@login_required
def swipe():
    trials = ClinicalTrial.query.order_by(ClinicalTrial.title).all()
    return render_template("swipe.html", trials=trials)


# Auth blueprint
from routes.auth import auth
app.register_blueprint(auth)


if __name__ == "__main__":
    app.run(debug=True)
