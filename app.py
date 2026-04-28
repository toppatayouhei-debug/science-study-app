import streamlit as st
import pandas as pd
import random
import re

# ==================================================
# 1. Page Config & CSS
# ==================================================
st.set_page_config(
    page_title="Science Study App",
    page_icon="🧬",
    layout="centered"
)

st.markdown("""
<style>
.stApp { background:#f8fafc; }
.card { 
    background:white; 
    padding:22px; 
    border-radius:18px; 
    box-shadow:0 4px 15px rgba(0,0,0,0.05); 
    margin-bottom:1rem; 
    color: #111 !important; 
}
.orange-card { border-left: 8px solid #ff9800; }
.blue-card   { border-left: 8px solid #2196f3; }
.stButton button { 
    width: 100%; 
    border-radius: 12px; 
    font-weight: 800; 
    min-height: 50px; 
}
.tango-btn button { 
    background-color: #fff4e6 !important; 
    color: #ff9800 !important; 
    border: 2px solid #ff9800 !important; 
}
</style>
""", unsafe_allow_html=True)

def reset_engine():
    for k in ["df", "idx", "answered", "choices", "correct", "selected"]:
        if k in st.session_state:
            del st.session_state[k]

# ==================================================
# 2. Data Loading
# ==================================================
@st.cache_data
def load_csv(name):
    files = {
        "システム英単語": "final_tango_list.csv",
        "数Ⅲ積分 定石": "math3_integration.csv"
    }
    try:
        df = pd.read_csv(files[name], encoding="utf-8-sig")
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# ==================================================
# 3. Sidebar & Logic
# ==================================================
st.sidebar.title("🧬 Science Menu")
subject = st.sidebar.selectbox("Subject", ["Select", "システム英単語", "数Ⅲ積分 定石"])

if subject == "Select":
    st.info("← Please select a subject from sidebar.")
    st.stop()

raw_df = load_csv(subject)
if raw_df.empty:
    st.warning(f"File for {subject} not found. Please check CSV.")
    st.stop()

df = raw_df
sel_level = "All"
if subject == "システム英単語":
    levels = {"All":"All", "1-600":"Fundamental", "601-1200":"Essential", "1201-1700":"Advanced", "1701-2027":"Final"}
    sel_level = st.sidebar.radio("Level", list(levels.keys()))
    if sel_level != "All":
        df = raw_df[raw_df["level"].astype(str).str.contains(levels[sel_level], case=False, na=False)]

if st.session_state.get("current_subject") != subject or st.session_state.get("current_filter") != str(sel_level):
    reset_engine()
    st.session_state.current_subject = subject
    st.session_state.current_filter = str(sel_level)
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if idx >= len(active_df):
    st.balloons()
    st.success("🎉 Completed!")
    if st.button("Restart"):
        reset_engine()
        st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 4. Main UI
# ==================================================
if subject == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct

    st.markdown('<div class="tango-btn">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, val in enumerate(st.session_state.get("choices", [])):
        with (c1 if i % 2 == 0 else c2):
            if st.button(val, key=f"btn_{idx}_{i}", disabled=st.session_state.get("answered", False)):
                st.session_state.selected, st.session_state.answered = val, True
                st.rerun()
    
    if st.session_state.get("answered"):
        if st.session_state.selected == st.session_state.correct: st.success("✨ Correct!")
        else: st.error(f"❌ Incorrect... Correct: {st.session_state.correct}")
        st.info(f"Meaning: {row['all_answers']}\nTranslation: {row['translation']}")
        if st.button("Next"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif subject == "数Ⅲ積分 定石":
    st.markdown('<div class="card blue-card">', unsafe_allow_html=True)
    st.latex(row["question"])
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.get("answered", False):
        if st.button("Check Answer"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.info(f"💡 Strategy: {row['strategy']}")
        st.latex(row["answer"])
        if st.button("Next"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()