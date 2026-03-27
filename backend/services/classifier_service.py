"""
Complaint classifier using TensorFlow + Universal Sentence Encoder.
On first run, it trains a small Dense model on synthetic seed data
and saves it to ./models/complaint_classifier/.
Subsequent runs load from disk.
"""

import os
import json
import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from pathlib import Path

MODEL_DIR = Path("./models/complaint_classifier")
LABELS_PATH = MODEL_DIR / "labels.json"

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
    # Infrastructure
    ("The road in my area has deep potholes and causes accidents daily", "Infrastructure"),
    ("Street lights are broken on main road for 3 weeks", "Infrastructure"),
    ("The bridge near the river is cracking and dangerous to cross", "Infrastructure"),
    ("Construction debris blocking the footpath for months", "Infrastructure"),
    ("Public toilet near bus stand is non-functional and unhygienic", "Infrastructure"),
    # Healthcare
    ("Government hospital has no doctors available on weekends", "Healthcare"),
    ("Medicine supply in primary health center has been stopped", "Healthcare"),
    ("Ambulance service is not responding to emergency calls", "Healthcare"),
    ("Vaccination camp was cancelled without any notice", "Healthcare"),
    ("Hospital staff is demanding bribe before treating patients", "Healthcare"),
    # Education
    ("Government school has no teachers for mathematics class", "Education"),
    ("School building roof is leaking and classrooms are flooded", "Education"),
    ("Mid-day meal scheme food is of very poor quality", "Education"),
    ("Children are not receiving free textbooks as promised", "Education"),
    ("School has no proper toilets for girl students", "Education"),
    # Safety & Security
    ("There are frequent thefts in our colony and police are unresponsive", "Safety & Security"),
    ("Eve-teasing incidents near school are increasing", "Safety & Security"),
    ("Illegal gambling is happening openly near the market", "Safety & Security"),
    ("Domestic violence case is being ignored by local police", "Safety & Security"),
    ("Drug peddling is going on near the children's park", "Safety & Security"),
    ("My mobile phone was stolen at the bus stand", "Safety & Security"),
    ("Theft occurred at the railway station, wallet was pickpocketed", "Safety & Security"),
    ("Chain snatching incident happened near market area", "Safety & Security"),
    ("My house was burgled while we were away", "Safety & Security"),
    ("Robbery at knifepoint on the main road at night", "Safety & Security"),
    ("Someone broke into my shop and stole cash", "Safety & Security"),
    ("Mobile phone snatched by two men on a bike", "Safety & Security"),
    ("Pickpocket stole my purse in a crowded bus", "Safety & Security"),
    ("Fraud person cheated elderly citizen of savings", "Safety & Security"),
    ("Online scam and cyber fraud reported, police not responding", "Safety & Security"),
    # Environment
    ("Factory is dumping chemical waste into the river", "Environment"),
    ("Illegal mining is destroying the forest near our village", "Environment"),
    ("Plastic burning near residential area causing health issues", "Environment"),
    ("Sewage water is overflowing into drinking water source", "Environment"),
    ("Noise pollution from illegal quarry exceeds safe limits", "Environment"),
    # Water & Sanitation
    ("Water supply has been cut off for 5 days in our ward", "Water & Sanitation"),
    ("Drinking water supply contains mud and is unfit for use", "Water & Sanitation"),
    ("Drainage is blocked and overflowing into homes", "Water & Sanitation"),
    ("No water tanker provided despite repeated complaints", "Water & Sanitation"),
    ("Water pipe is broken and water is wasting for two weeks", "Water & Sanitation"),
    # Electricity
    ("Power cuts lasting 8 hours daily affecting our business", "Electricity"),
    ("Electric pole is falling and is a danger to children", "Electricity"),
    ("Electricity bill amount is incorrect and overbilled", "Electricity"),
    ("New connection applied 6 months ago but not given yet", "Electricity"),
    ("Transformer has not been repaired after breakdown", "Electricity"),
    # Transportation
    ("Bus timings are irregular and passengers are stranded", "Transportation"),
    ("No bus shelter at the stop despite heavy rain", "Transportation"),
    ("Driver was rash driving and endangering passengers", "Transportation"),
    ("Train platform has no proper lighting at night", "Transportation"),
    ("Bus service on route 42 has been stopped without notice", "Transportation"),
    ("Auto rickshaw drivers are refusing to use meter", "Transportation"),
    ("Railway station has no wheelchair access for disabled people", "Transportation"),
    ("Potholes on highway are causing accidents and deaths", "Transportation"),
    ("Overloaded school buses are endangering children lives", "Transportation"),
    # Administrative
    ("My pension has been stopped without any reason given", "Administrative"),
    ("Land record documents have not been updated despite payment", "Administrative"),
    ("Ration card application rejected without explanation", "Administrative"),
    ("Birth certificate application pending for over 3 months", "Administrative"),
    ("Caste certificate is not being issued to eligible citizens", "Administrative"),
    # Other
    ("Noise from loudspeakers at night is disturbing residents", "Other"),
    ("Stray dogs in large numbers attacking people in park", "Other"),
    ("Unauthorized food stall is operating without licence", "Other"),
    ("Tree fell on road blocking traffic but no one clearing it", "Other"),
    ("Community hall booked but key not provided on event day", "Other"),
]

_model = None
_embed = None
_label_map = None


def _get_embed():
    global _embed
    if _embed is None:
        print("[Classifier] Loading Universal Sentence Encoder…")
        _embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder/4")
        print("[Classifier] USE loaded.")
    return _embed


def _build_and_train():
    embed = _get_embed()
    label_names = list(CATEGORIES.keys())
    label_to_idx = {l: i for i, l in enumerate(label_names)}

    texts = [t for t, _ in SEED_DATA]
    labels = [label_to_idx[l] for _, l in SEED_DATA]

    embeddings = embed(texts).numpy()
    labels_arr = np.array(labels)

    model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation="relu", input_shape=(512,)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(len(label_names), activation="softmax"),
    ])
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    model.fit(embeddings, labels_arr, epochs=40, batch_size=8, verbose=0)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model.save(str(MODEL_DIR / "complaint_classifier.keras"))
    with open(LABELS_PATH, "w") as f:
        json.dump(label_names, f)

    print(f"[Classifier] Model trained & saved to {MODEL_DIR}")
    return model, label_names


def _load_model():
    global _model, _label_map
    if _model is not None:
        return _model, _label_map

    if MODEL_DIR.exists() and LABELS_PATH.exists():
        print("[Classifier] Loading saved model…")
        _model = tf.keras.models.load_model(str(MODEL_DIR / "complaint_classifier.keras"))
        with open(LABELS_PATH) as f:
            _label_map = json.load(f)
    else:
        _model, _label_map = _build_and_train()

    return _model, _label_map


def classify_complaint(text: str) -> dict:
    """
    Classify a complaint text.
    Returns: { category, department, confidence, all_scores }
    """
    model, label_names = _load_model()
    embed = _get_embed()

    vec = embed([text]).numpy()
    probs = model.predict(vec, verbose=0)[0]

    top_idx = int(np.argmax(probs))
    category = label_names[top_idx]
    confidence = float(probs[top_idx])
    department = CATEGORIES.get(category, "Grievance Cell")

    all_scores = {label_names[i]: float(probs[i]) for i in range(len(label_names))}

    return {
        "category": category,
        "department": department,
        "confidence": round(confidence, 4),
        "all_scores": all_scores,
    }
