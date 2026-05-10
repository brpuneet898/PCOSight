from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, PredictionResult
from functools import wraps
import joblib
import pandas as pd
import json
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "pcossight_secret_key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pcosight.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ---------------- MODEL LOADING ----------------

basic_model = None
basic_scaler = None
basic_features = None

adv_model = None
adv_features = None


def load_basic_assets():
    global basic_model, basic_scaler, basic_features

    if basic_model is None:
        basic_model = joblib.load("saved_models/basic_lr_model.pkl")
        basic_scaler = joblib.load("saved_models/basic_lr_scaler.pkl")
        basic_features = joblib.load("saved_models/basic_lr_features.pkl")


def load_advanced_assets():
    global adv_model, adv_features

    if adv_model is None:
        adv_model = joblib.load("saved_models/advanced_rf_model.pkl")
        adv_features = joblib.load("saved_models/advanced_rf_features.pkl")


def predict_basic(input_data):
    load_basic_assets()

    df = pd.DataFrame([input_data])
    df = df[basic_features]

    scaled = basic_scaler.transform(df)
    probability = float(basic_model.predict_proba(scaled)[0][1])

    return probability


def predict_advanced(input_data):
    load_advanced_assets()

    df = pd.DataFrame([input_data])
    df = df[adv_features]

    probability = float(adv_model.predict_proba(df)[0][1])

    return probability

def generate_recommendations(prediction_type, probability, input_data):
    risk_percent = round(probability * 100, 2)

    prompt = f"""
You are a women's health assistant for a PCOS screening portal.

Generate personalized recommendations based on:
Prediction type: {prediction_type}
PCOS risk probability: {risk_percent}%
User inputs: {json.dumps(input_data)}

Return ONLY valid JSON in this exact format:
{{
  "good": ["point 1", "point 2"],
  "bad": ["point 1", "point 2"],
  "improve": ["point 1", "point 2"]
}}

Rules:
- Each point must be one short bullet-level sentence.
- Be specific to the user's inputs.
- Do not diagnose PCOS.
- Do not write long paragraphs.
- Mention consulting a gynecologist only when risk or symptoms are notable.
"""

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You create short, safe, non-diagnostic health recommendations in JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,
            max_tokens=350
        )

        content = response.choices[0].message.content.strip()
        recommendations = json.loads(content)

        return {
            "good": recommendations.get("good", [])[:2],
            "bad": recommendations.get("bad", [])[:2],
            "improve": recommendations.get("improve", [])[:2]
        }

    except Exception:
        return {
            "good": ["You completed the screening inputs properly."],
            "bad": ["Some symptoms or lifestyle markers may need attention."],
            "improve": ["Use this result as screening support and consult a doctor for confirmation."]
        }


# ---------------- HELPERS ----------------

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.", "error")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def save_prediction(user_id, prediction_type, probability, input_data, recommendations):
    payload = {
        "inputs": input_data,
        "recommendations": recommendations
    }

    existing = PredictionResult.query.filter_by(
        user_id=user_id,
        prediction_type=prediction_type
    ).first()

    if existing:
        existing.probability = probability
        existing.input_data = json.dumps(payload)
    else:
        existing = PredictionResult(
            user_id=user_id,
            prediction_type=prediction_type,
            probability=probability,
            input_data=json.dumps(payload)
        )
        db.session.add(existing)

    db.session.commit()


def get_prediction(user_id, prediction_type):
    result = PredictionResult.query.filter_by(
        user_id=user_id,
        prediction_type=prediction_type
    ).first()

    if not result:
        return None

    stored = json.loads(result.input_data)

    if "inputs" in stored:
        input_data = stored.get("inputs", {})
        recommendations = stored.get("recommendations", {})
    else:
        input_data = stored
        recommendations = {}

    return {
        "probability": result.probability,
        "percentage": round(result.probability * 100, 2),
        "input_data": input_data,
        "recommendations": recommendations,
        "updated_at": result.updated_at
    }


# ---------------- ROUTES ----------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not email or not username or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered. Please login.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken. Please choose another.", "error")
            return redirect(url_for("register"))

        new_user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid username or password.", "error")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["username"] = user.username

        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/basic", methods=["GET", "POST"])
@login_required
def basic():
    user_id = session["user_id"]

    if request.method == "POST":
        input_data = {
            "Age (yrs)": float(request.form["age"]),
            "BMI": float(request.form["bmi"]),
            "Cycle(R/I)": int(request.form["cycle"]),
            "Pimples(Y/N)": int(request.form["pimples"]),
            "hair growth(Y/N)": int(request.form["hair_growth"]),
            "Hair loss(Y/N)": int(request.form["hair_loss"]),
            "Weight gain(Y/N)": int(request.form["weight_gain"]),
            "Skin darkening (Y/N)": int(request.form["skin_darkening"]),
            "Fast food (Y/N)": int(request.form["fast_food"]),
            "Reg.Exercise(Y/N)": int(request.form["regular_exercise"])
        }

        probability = predict_basic(input_data)
        recommendations = generate_recommendations("basic", probability, input_data)
        save_prediction(user_id, "basic", probability, input_data, recommendations)

        flash("Basic prediction updated successfully.", "success")
        return redirect(url_for("basic"))

    result = get_prediction(user_id, "basic")
    return render_template("basic.html", username=session.get("username"), result=result)


@app.route("/advanced", methods=["GET", "POST"])
@login_required
def advanced():
    user_id = session["user_id"]

    if request.method == "POST":
        input_data = {
            "Age (yrs)": float(request.form["age"]),
            "BMI": float(request.form["bmi"]),
            "Cycle(R/I)": int(request.form["cycle"]),
            "Pimples(Y/N)": int(request.form["pimples"]),
            "hair growth(Y/N)": int(request.form["hair_growth"]),
            "Hair loss(Y/N)": int(request.form["hair_loss"]),
            "Weight gain(Y/N)": int(request.form["weight_gain"]),
            "Skin darkening (Y/N)": int(request.form["skin_darkening"]),
            "AMH(ng/mL)": float(request.form["amh"]),
            "LH(mIU/mL)": float(request.form["lh"]),
            "FSH(mIU/mL)": float(request.form["fsh"]),
            "LH_FSH_Ratio": float(request.form["lh_fsh_ratio"]),
            "TSH (mIU/L)": float(request.form["tsh"]),
            "PRL(ng/mL)": float(request.form["prl"]),
            "RBS(mg/dl)": float(request.form["rbs"])
        }

        probability = predict_advanced(input_data)
        recommendations = generate_recommendations("advanced", probability, input_data)
        save_prediction(user_id, "advanced", probability, input_data, recommendations)

        flash("Advanced prediction updated successfully.", "success")
        return redirect(url_for("advanced"))

    result = get_prediction(user_id, "advanced")
    return render_template("advanced.html", username=session.get("username"), result=result)


@app.route("/research")
@login_required
def research():
    return render_template("research.html", username=session.get("username"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)