from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
import pickle
from pathlib import Path

MODEL_PATH = Path("./models/classifier.pkl")

CATEGORIES = {
    "Infrastructure": "Public Works Department",
    "Healthcare": "Department of Health",
    "Education": "Department of Education",
    "Safety & Security": "Police / Home Department",
    "Environment": "Environment Department",
    "Water & Sanitation": "Water Board",
    "Electricity": "Electricity Board",
    "Transportation": "Transport Department",
    "Administrative": "General Administration",
    "Other": "Grievance Cell",
}

SEED_DATA = [
    ("The road has deep potholes causing accidents", "Infrastructure"),
    ("Street lights are broken on main road", "Infrastructure"),
    ("Bridge is cracking and dangerous", "Infrastructure"),
    ("Government hospital has no doctors", "Healthcare"),
    ("Medicine supply has been stopped", "Healthcare"),
    ("Ambulance not responding to emergency", "Healthcare"),
    ("School has no teachers for mathematics", "Education"),
    ("School building roof is leaking", "Education"),
    ("Mid-day meal food is poor quality", "Education"),
    ("Frequent thefts and police unresponsive", "Safety & Security"),
    ("Eve-teasing incidents near school increasing", "Safety & Security"),
    ("Drug peddling near children park", "Safety & Security"),
    ("Factory dumping waste into river", "Environment"),
    ("Illegal mining destroying forest", "Environment"),
    ("Plastic burning causing health issues", "Environment"),
    ("Water supply cut off for 5 days", "Water & Sanitation"),
    ("Drinking water contains mud", "Water & Sanitation"),
    ("Drainage blocked and overflowing", "Water & Sanitation"),
    ("Power cuts lasting 8 hours daily", "Electricity"),
    ("Electric pole is falling and dangerous", "Electricity"),
    ("Electricity bill is incorrect", "Electricity"),
    ("Bus service on route stopped without notice", "Transportation"),
    ("Auto rickshaw drivers refusing meter", "Transportation"),
    ("Potholes on highway causing accidents", "Transportation"),
    ("Pension has been stopped without reason", "Administrative"),
    ("Land record documents not updated", "Administrative"),
    ("Ration card application rejected", "Administrative"),
    ("Noise from loudspeakers disturbing residents", "Other"),
    ("Stray dogs attacking people in park", "Other"),
    ("Unauthorized food stall operating without licence", "Other"),
]

_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is not None:
        return _pipeline

    if MODEL_PATH.exists():
        with open(MODEL_PATH, "rb") as f:
            _pipeline = pickle.load(f)
        return _pipeline

    texts = [t for t, _ in SEED_DATA]
    labels = [l for _, l in SEED_DATA]

    _pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        ("clf", LogisticRegression(max_iter=1000, C=1.0)),
    ])
    _pipeline.fit(texts, labels)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(_pipeline, f)

    return _pipeline


def classify_complaint(text: str) -> dict:
    pipeline = _get_pipeline()
    category = pipeline.predict([text])[0]
    probs = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_.tolist()
    confidence = float(probs[classes.index(category)])
    department = CATEGORIES.get(category, "Grievance Cell")
    all_scores = {classes[i]: float(probs[i]) for i in range(len(classes))}

    return {
        "category": category,
        "department": department,
        "confidence": round(confidence, 4),
        "all_scores": all_scores,
    }
