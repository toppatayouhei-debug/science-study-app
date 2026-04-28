import streamlit as st
import pandas as pd
import random
import re

# ==================================================
# 1. 基本設定
# ==================================================
st.set_page_config(
    page_title="理系特化型・定石マスター",
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
# 2. データ読み込み
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
# 3. サイドバーとロジック
# ==================================================
st.sidebar.title("🧬 理系学習メニュー")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if subject == "選択してください":
    st.info("← サイドバーから科目を選択して開始してください。")
    st.stop()

raw_df = load_csv(subject)
if raw_df.empty:
    st.warning(f"{subject} のCSVファイルが見つかりません。")
    st.stop()

df = raw_df
sel_level_key = "すべて"

if subject == "システム英単語":
    # 指示通りの表記に変更
    levels_map = {
        "すべて": "All",
        "Fundamental (1-600)": "Fundamental",
        "Essential (601-1200)": "Essential",
        "Advanced (1201-1700)": "Advanced",
        "Final (1701-2027)": "Final"
    }
    sel_level_key = st.sidebar.radio("レベル選択", list(levels_map.keys()))
    
    if sel_level_key != "すべて":
        keyword = levels_map[sel_level_key]
        df = raw_df[raw_df["level"].astype(str).str.contains(keyword, case=False, na=False)]

# 科目やフィルターが変わったらリセット
if st.session_state.get("current_subject") != subject or st.session_state.get("current_filter") != sel_level_key:
    reset_engine()
    st.session_state.current_subject = subject
    st.session_state.current_filter = sel_level_key
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if idx >= len(active_df):
    st.balloons()
    st.success("🎉 お疲れ様でした！全問終了です！")
    if st.button("最初からやり直す"):
        reset_engine()
        st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 4. メインUI
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
        if st.session_state.selected == st.session_state.correct: st.success("✨ 正解！")
        else: st.error(f"❌ 不正解... 正解は：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n文意：{row['translation']}")
        if st.button("次の問題へ"):
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
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.info(f"💡 定石：{row['strategy']}")
        st.latex(row["answer"])
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()