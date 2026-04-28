import streamlit as st
import pandas as pd
import random
import re

# 1. ページ設定
st.set_page_config(page_title="理系定石マスター", page_icon="🧬")

st.markdown("""
<style>
.stApp { background:#f8fafc; }
.card { background:white; padding:22px; border-radius:18px; box-shadow:0 4px 15px rgba(0,0,0,0.05); margin-bottom:1rem; color: #111 !important; }
.orange-card { border-left: 8px solid #ff9800; }
.blue-card   { border-left: 8px solid #2196f3; }
.stButton button { width: 100%; border-radius: 12px; font-weight: 800; min-height: 50px; }
</style>
""", unsafe_allow_html=True)

# 2. データ準備
def get_math_data():
    return pd.DataFrame([
        {"question": r"x \cos x", "strategy": "部分積分法", "answer": r"x \sin x + \cos x + C"},
        {"question": r"\frac{f'(x)}{f(x)}", "strategy": "対数積分法", "answer": r"\log |f(x)| + C"},
        {"question": r"\sin^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"}
    ])

def load_english_data():
    try:
        return pd.read_csv("final_tango_list.csv", encoding="utf-8-sig").dropna(how='all')
    except:
        return pd.DataFrame()

# 3. メイン処理
st.sidebar.title("🧬 理系学習メニュー")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if subject == "選択してください":
    st.info("← サイドバーから科目を選択してください。")
    st.stop()

# 状態の初期化
if "current_sub" not in st.session_state or st.session_state.current_sub != subject:
    st.session_state.current_sub = subject
    st.session_state.idx = 0
    st.session_state.answered = False
    if subject == "システム英単語":
        st.session_state.df = load_english_data().sample(frac=1).reset_index(drop=True)
    else:
        st.session_state.df = get_math_data().sample(frac=1).reset_index(drop=True)

df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if df.empty:
    st.warning("データが読み込めませんでした。")
    st.stop()

row = df.iloc[idx]

# 4. 表示（数学）
if subject == "数Ⅲ積分 定石":
    st.markdown('<div class="card blue-card">', unsafe_allow_html=True)
    st.latex(r"\int " + str(row["question"]) + r" \, dx")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.answered:
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.info(f"💡 定石：{row['strategy']}")
        st.latex(str(row["answer"]))
        if st.button("次の問題へ"):
            st.session_state.idx = (st.session_state.idx + 1) % len(df)
            st.session_state.answered = False
            st.rerun()

# 5. 表示（英単語）
elif subject == "システム英単語":
    st.markdown(f'<div class="card orange-card">{row.get("sentence", "No Sentence")}</div>', unsafe_allow_html=True)
    st.write(f"問題: {row.get('question', 'Error')}")
    if st.button("次の英単語へ"):
        st.session_state.idx = (st.session_state.idx + 1) % len(df)
        st.rerun()