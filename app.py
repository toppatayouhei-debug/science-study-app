import streamlit as st
import pandas as pd
import random
import re

# 1. 基本設定
st.set_page_config(page_title="理系定石マスター", page_icon="🧬", layout="centered")

st.markdown("""
<style>
.stApp { background:#f8fafc; }
.card { background:white; padding:22px; border-radius:18px; box-shadow:0 4px 15px rgba(0,0,0,0.05); margin-bottom:1rem; color: #111 !important; min-height: 100px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; }
.orange-card { border-left: 8px solid #ff9800; }
.blue-card   { border-left: 8px solid #2196f3; }
.stButton button { width: 100%; border-radius: 12px; font-weight: 800; min-height: 50px; }
</style>
""", unsafe_allow_html=True)

def reset_engine():
    for k in ["df", "idx", "answered", "choices", "correct", "selected"]:
        if k in st.session_state: del st.session_state[k]

# 2. データ（直接埋め込み形式）
def get_data(subject):
    if subject == "システム英単語":
        try:
            return pd.read_csv("final_tango_list.csv", encoding="utf-8-sig").dropna(how='all')
        except:
            return pd.DataFrame()
    else:
        # 数学のデータを辞書形式で確実に作成
        data = [
            {"question": r"x \cos x", "strategy": "部分積分法", "answer": r"x \sin x + \cos x + C"},
            {"question": r"\frac{f'(x)}{f(x)}", "strategy": "対数積分法", "answer": r"\log |f(x)| + C"},
            {"question": r"\sin^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"}
        ]
        return pd.DataFrame(data)

# 3. メイン
st.sidebar.title("🧬 理系学習メニュー")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if subject == "選択してください":
    st.info("← サイドバーから科目を選択してください。")
    st.stop()

# 科目変更時にデータをロード
if "current_sub" not in st.session_state or st.session_state.current_sub != subject:
    reset_engine()
    st.session_state.current_sub = subject
    df = get_data(subject)
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0

df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if df.empty:
    st.warning("データが見つかりません。")
    st.stop()

if idx >= len(df):
    st.balloons()
    st.success("🎉 全問終了！")
    if st.button("もう一度"):
        reset_engine()
        st.rerun()
    st.stop()

row = df.iloc[idx]
st.progress((idx + 1) / len(df))

# 4. 表示
if subject == "数Ⅲ積分 定石":
    st.markdown(f'<div class="card blue-card">', unsafe_allow_html=True)
    # 確実に表示するために st.latex ではなく、マークダウン内でも表示
    st.latex(r"\int " + str(row["question"]) + " dx")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.get("answered", False):
        if st.button("解答を確認する", key="check_btn"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.info(f"💡 定石：{row['strategy']}")
        st.latex(str(row["answer"]))
        if st.button("次の問題へ", key="next_btn"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

elif subject == "システム英単語":
    # 英単語側の表示ロジック（基本は同じ）
    st.markdown(f'<div class="card orange-card">{row["sentence"]}</div>', unsafe_allow_html=True)
    # ... (英単語のボタン処理など)
    st.write("英単語モード（中身は数学が動けば反映されます）")