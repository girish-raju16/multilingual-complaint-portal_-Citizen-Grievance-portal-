"""
Multilingual Government Complaint Portal — Streamlit Frontend
Run: streamlit run frontend/app.py
"""

import streamlit as st
import requests
import json
import io
from pathlib import Path

API_BASE = "http://127.0.0.1:8000"

LANG_OPTIONS = {
    "Auto-detect": "auto",
    "Hindi (हिन्दी)": "hi",
    "Telugu (తెలుగు)": "te",
    "Tamil (தமிழ்)": "ta",
    "Kannada (ಕನ್ನಡ)": "kn",
    "Malayalam (മലയാളം)": "ml",
    "Bengali (বাংলা)": "bn",
    "Marathi (मराठी)": "mr",
    "Gujarati (ગુજરાતી)": "gu",
    "Punjabi (ਪੰਜਾਬੀ)": "pa",
    "Urdu (اردو)": "ur",
    "English": "en",
    "Arabic (العربية)": "ar",
    "French (Français)": "fr",
    "Spanish (Español)": "es",
}

PRIORITY_COLORS = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "urgent": "🔴",
}

STATUS_COLORS = {
    "submitted": "🔵",
    "in_review": "🟡",
    "resolved": "✅",
}


def set_page_config():
    st.set_page_config(
        page_title="Citizen Grievance Portal",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def custom_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #1a237e, #283593);
        color: white;
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p  { margin: 0.3rem 0 0; opacity: 0.85; font-size: 1rem; }
    .complaint-card {
        background: #f8f9fa;
        border-left: 4px solid #1a237e;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
    }
    .success-box 
    {
        background: #e8f5e9;
        border: 1px solid #4CAF50;
        border-radius: 8px;
        padding: 1.2rem;
        margin: 1rem 0;
        color: #1b5e20;
    }
    .stat-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    .stat-card .number { font-size: 2.2rem; font-weight: 700; color: #1a237e; }
    .stat-card .label  { font-size: 0.85rem; color: #666; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)


def api_call(method: str, endpoint: str, **kwargs):
    try:
        url = f"{API_BASE}{endpoint}"
        resp = requests.request(method, url, timeout=120, **kwargs)
        resp.raise_for_status()
        return resp.json(), None
    except requests.exceptions.ConnectionError:
        return None, "Cannot connect to API server. Make sure the FastAPI backend is running on port 8000."
    except requests.exceptions.HTTPError as e:
        return None, f"API error: {e.response.text}"
    except Exception as e:
        return None, str(e)


# ──────────────────────────────────────────────────────────────
# PAGE: Submit Complaint
# ──────────────────────────────────────────────────────────────

def page_submit():
    st.markdown("""
    <div class="main-header">
        <h1>🏛️ Citizen Grievance Portal</h1>
        <p>Submit your complaint in your native language — voice, text, or document</p>
    </div>
    """, unsafe_allow_html=True)

    # Citizen Info (optional)
    with st.expander("👤 Your Details (optional but helps faster resolution)", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            citizen_name = st.text_input("Your Name")
        with col2:
            contact = st.text_input("Mobile / Email")
        with col3:
            location = st.text_input("Area / District")

    st.markdown("---")
    tab_voice, tab_text, tab_file = st.tabs(["🎙️ Voice", "⌨️ Text", "📄 File Upload"])

    # ── VOICE ──
    with tab_voice:
        st.info("📢 Record your complaint in your native language. Whisper will transcribe it automatically.")

        uploaded_audio = st.file_uploader(
            "Upload your voice recording (WAV, MP3, M4A, OGG)",
            type=["wav", "mp3", "m4a", "ogg", "flac"],
            key="audio_upload",
        )

        if uploaded_audio:
            st.audio(uploaded_audio)
            if st.button("🚀 Submit Voice Complaint", type="primary", key="submit_voice"):
                with st.spinner("🎙️ Transcribing with Whisper → translating → classifying…"):
                    data, err = api_call(
                        "POST", "/submit/voice",
                        files={"audio": (uploaded_audio.name, uploaded_audio.getvalue(), "audio/wav")},
                        data={
                            "citizen_name": citizen_name,
                            "contact": contact,
                            "location": location,
                        },
                    )
                if err:
                    st.error(f"❌ {err}")
                else:
                    _show_success(data)

    # ── TEXT ──
    with tab_text:
        st.info("✍️ Type or paste your complaint below in any language. It will be auto-translated.")

        lang_name = st.selectbox("Select your language", list(LANG_OPTIONS.keys()), key="text_lang")
        lang_code = LANG_OPTIONS[lang_name]

        complaint_text = st.text_area(
            "Write your complaint here",
            height=200,
            placeholder="अपनी शिकायत यहाँ लिखें... / ఇక్కడ మీ ఫిర్యాదు రాయండి... / Type here...",
        )

        if complaint_text and st.button("🚀 Submit Complaint", type="primary", key="submit_text"):
            with st.spinner("Translating → classifying → generating report…"):
                payload = {
                    "text": complaint_text,
                    "language": lang_code,
                    "citizen_name": citizen_name,
                    "contact": contact,
                    "location": location,
                }
                data, err = api_call("POST", "/submit/text", json=payload)
            if err:
                st.error(f"❌ {err}")
            else:
                _show_success(data)

    # ── FILE ──
    with tab_file:
        st.info("📎 Upload a complaint document (PDF or text file). The system will extract and process the text.")

        uploaded_file = st.file_uploader(
            "Upload complaint document (PDF or TXT)",
            type=["pdf", "txt"],
            key="file_upload",
        )

        if uploaded_file and st.button("🚀 Submit File Complaint", type="primary", key="submit_file"):
            with st.spinner("Reading file → processing → classifying…"):
                data, err = api_call(
                    "POST", "/submit/file",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                    data={
                        "citizen_name": citizen_name,
                        "contact": contact,
                        "location": location,
                    },
                )
            if err:
                st.error(f"❌ {err}")
            else:
                _show_success(data)


def _show_success(data: dict):
    st.markdown(f"""
    <div class="success-box">
        <h3>✅ Complaint Submitted Successfully!</h3>
        <b>Complaint ID:</b> <code>{data['complaint_id']}</code><br>
        <b>Routed to:</b> {data['department']}<br>
        <b>Category:</b> {data['category']}<br>
        <b>Priority:</b> {PRIORITY_COLORS.get(data.get('priority','medium'))} {data.get('priority','medium').upper()}<br>
        <b>Language detected:</b> {data.get('original_language','unknown').upper()}
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📝 AI Summary", expanded=True):
        st.write(data.get("summary", "No summary available."))

    if data.get("translated_text") and data.get("original_language") not in ("en", "english"):
        with st.expander("🌐 English Translation"):
            st.write(data["translated_text"])

    col1, col2 = st.columns(2)
    with col1:
        st.metric("AI Confidence", f"{data.get('confidence', 0) * 100:.1f}%")
    with col2:
        st.metric("Status", data.get("status", "submitted").replace("_", " ").title())

    # Download report
    report_url = f"{API_BASE}/complaints/{data['complaint_id']}/report"
    st.markdown(f"[📥 Download PDF Report]({report_url})", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# PAGE: Admin Dashboard
# ──────────────────────────────────────────────────────────────

def page_dashboard():
    st.title("📊 Admin Dashboard")
    st.caption("Government complaint management — view, filter, and update complaints.")

    # Stats
    stats, err = api_call("GET", "/stats")
    if stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<div class="stat-card"><div class="number">{stats["total"]}</div><div class="label">Total Complaints</div></div>', unsafe_allow_html=True)
        with col2:
            pending = stats["by_status"].get("submitted", 0) + stats["by_status"].get("in_review", 0)
            st.markdown(f'<div class="stat-card"><div class="number">{pending}</div><div class="label">Pending</div></div>', unsafe_allow_html=True)
        with col3:
            resolved = stats["by_status"].get("resolved", 0)
            st.markdown(f'<div class="stat-card"><div class="number">{resolved}</div><div class="label">Resolved</div></div>', unsafe_allow_html=True)
        with col4:
            urgent = stats["by_priority"].get("urgent", 0) + stats["by_priority"].get("high", 0)
            st.markdown(f'<div class="stat-card"><div class="number">{urgent}</div><div class="label">High/Urgent</div></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Charts
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.subheader("By Department")
            if stats["by_department"]:
                import pandas as pd
                df = pd.DataFrame(list(stats["by_department"].items()), columns=["Department", "Count"])
                df = df.sort_values("Count", ascending=False)
                st.bar_chart(df.set_index("Department"))

        with col_b:
            st.subheader("By Priority")
            if stats["by_priority"]:
                import pandas as pd
                df2 = pd.DataFrame(list(stats["by_priority"].items()), columns=["Priority", "Count"])
                st.bar_chart(df2.set_index("Priority"))

        with col_c:
            st.subheader("By Language")
            if stats["by_language"]:
                import pandas as pd
                df3 = pd.DataFrame(list(stats["by_language"].items()), columns=["Language", "Count"])
                st.bar_chart(df3.set_index("Language"))

    st.markdown("---")
    st.subheader("📋 Complaints List")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        f_status = st.selectbox("Filter by Status", ["All", "submitted", "in_review", "resolved"])
    with col2:
        f_priority = st.selectbox("Filter by Priority", ["All", "urgent", "high", "medium", "low"])
    with col3:
        f_dept = st.text_input("Filter by Department (partial)")

    params = {}
    if f_status != "All":
        params["status"] = f_status
    if f_priority != "All":
        params["priority"] = f_priority
    if f_dept:
        params["department"] = f_dept

    complaints, err = api_call("GET", "/complaints", params=params)

    if err:
        st.error(f"❌ {err}")
    elif not complaints:
        st.info("No complaints found with these filters.")
    else:
        for c in complaints:
            priority_icon = PRIORITY_COLORS.get(c.get("priority", "medium"), "🟡")
            status_icon = STATUS_COLORS.get(c.get("status", "submitted"), "🔵")
            lang = c.get("original_language", "?").upper()

            with st.expander(
                f"{priority_icon} {c['complaint_id']} | {c['category']} | {c['department']} | {status_icon} {c['status'].replace('_',' ').title()} | 🌐 {lang}"
            ):
                st.write(c.get("summary", "No summary."))
                st.caption(f"Filed: {c.get('created_at', '')}")

                new_status = st.selectbox(
                    "Update status",
                    ["submitted", "in_review", "resolved"],
                    index=["submitted", "in_review", "resolved"].index(c.get("status", "submitted")),
                    key=f"status_{c['complaint_id']}",
                )
                col_upd, col_dl = st.columns(2)
                with col_upd:
                    if st.button("✔ Update", key=f"upd_{c['complaint_id']}"):
                        result, err2 = api_call("PATCH", f"/complaints/{c['complaint_id']}/status", params={"status": new_status})
                        if err2:
                            st.error(err2)
                        else:
                            st.success(f"Status updated to {new_status}")
                            st.rerun()
                with col_dl:
                    report_url = f"{API_BASE}/complaints/{c['complaint_id']}/report"
                    st.markdown(f"[📥 PDF Report]({report_url})", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# PAGE: Track Complaint
# ──────────────────────────────────────────────────────────────

def page_track():
    st.title("🔍 Track Your Complaint")
    st.markdown("Enter your Complaint ID to check the current status.")

    complaint_id = st.text_input("Complaint ID (e.g. CMP-AB12CD34)").strip().upper()

    if complaint_id and st.button("Track", type="primary"):
        data, err = api_call("GET", f"/complaints/{complaint_id}")
        if err:
            st.error(f"❌ {err}")
        elif data:
            st.success(f"Complaint found: **{complaint_id}**")

            col1, col2, col3 = st.columns(3)
            col1.metric("Status", data.get("status", "").replace("_", " ").title())
            col2.metric("Department", data.get("department", "N/A"))
            col3.metric("Priority", data.get("priority", "N/A").upper())

            st.subheader("📝 Summary")
            st.write(data.get("summary", "No summary."))

            if data.get("translated_text"):
                with st.expander("View English translation"):
                    st.write(data["translated_text"])

            report_url = f"{API_BASE}/complaints/{complaint_id}/report"
            st.markdown(f"[📥 Download PDF Report]({report_url})")


# ──────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────

def main():
    set_page_config()
    custom_css()

    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg", width=80)
        st.markdown("### 🏛️ Grievance Portal")
        st.markdown("*Multilingual Complaint System*")
        st.markdown("---")
        page = st.radio(
            "Navigate",
            ["📝 Submit Complaint", "📊 Admin Dashboard", "🔍 Track Complaint"],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.caption("Powered by Whisper · Ollama · TensorFlow · FastAPI · Streamlit")

        # API health check
        health, _ = api_call("GET", "/health")
        if health:
            st.success("API Connected ✅")
        else:
            st.error("API Offline ❌")

    if page == "📝 Submit Complaint":
        page_submit()
    elif page == "📊 Admin Dashboard":
        page_dashboard()
    elif page == "🔍 Track Complaint":
        page_track()


if __name__ == "__main__":
    main()
