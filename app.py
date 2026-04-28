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

# 理系らしいブルー基調のCSS
st.markdown("""
# CSS部分をこれに上書き保存
st.markdown("""
<style>
.stApp { background:#f8fafc; }
/* カードの中の文字色を「#111 (ほぼ黒)」に固定 */
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

/* ボタンの中の文字も見えにくい場合はここを調整 */
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
""", unsafe_allow_html=True)

# 状態リセット関数
def reset_engine():
    keys = ["df", "idx", "answered", "choices", "correct", "selected"]
    for k in keys:
        if k in st.session_state: del st.session_state[k]

# ==================================================
# 2. データ読み込み
# ==================================================
@st.cache_data
def load_csv(name):
    files = {
        "システム英単語": "final_tango_list.csv",
        "数Ⅲ積分 定石": "math3_integration.csv" # 後で作成
    }
    try:
        df = pd.read_csv(files[name], encoding="utf-8-sig")
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# ==================================================
# 3. メイン画面
# ==================================================
st.sidebar.title("🧬 理系学習メニュー")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if subject == "選択してください":
    st.info("左のサイドバーから学習を開始してください。")
    st.stop()

# データ読み込みと初期化
raw_df = load_csv(subject)
if raw_df.empty and subject == "数Ⅲ積分 定石":
    st.warning("数学のCSVがまだありません。作成して配置してください。")
    st.stop()

# フィルタリング（シス単のみ）
df = raw_df
if subject == "システム英単語":
    level_map = {"All":"All", "1-600":"Fundamental", "601-1200":"Essential", "1201-1700":"Advanced", "1701-2027":"Final"}
    sel_level = st.sidebar.radio("学習レベル", list(level_map.keys()))
    if sel_level != "All":
        df = raw_df[raw_df["level"].astype(str).str.contains(level_map[sel_level], case=False, na=False)]

# クイズエンジンの初期化
if st.session_state.get("current_subject") != subject or st.session_state.get("current_filter") != str(sel_level if subject == "システム英単語" else ""):
    reset_engine()
    st.session_state.current_subject = subject
    st.session_state.current_filter = str(sel_level if subject == "システム英単語" else "")
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if idx >= len(active_df):
    st.balloons()
    st.success("🎉 全問終了！")
    if st.button("最初からやり直す"):
        reset_engine()
        st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 4. クイズUI（英単語移植）
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
        else: st.error(f"❌ 不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. 数学用のプレースホルダー ---
elif subject == "数Ⅲ積分 定石":
    st.info("ここに数学の定石チェックロジックを実装します。")

