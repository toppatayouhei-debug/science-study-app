import streamlit as st
import pandas as pd
import random
import re

# 1. ページ設定（これだけは必須）
st.set_page_config(page_title="理系学習アプリ", page_icon="🧬")

# 2. 強制リフレッシュCSS（キャッシュ対策）
st.markdown("""
<style>
.stApp { background:#f8fafc; }
.card { 
    background:white !important; padding:25px; border-radius:18px; 
    box-shadow:0 4px 15px rgba(0,0,0,0.1); margin-bottom:1rem; 
    color: #111 !important; border-left: 8px solid #2196f3;
}
.stButton button { width: 100%; border-radius: 12px; font-weight: 800; min-height: 50px; }
</style>
""", unsafe_allow_html=True)

# 3. データの定義（直接書き込む！）
def load_math():
    return [
        {"q": r"x \cos x", "s": "部分積分法", "a": r"x \sin x + \cos x + C"},
        {"q": r"\frac{f'(x)}{f(x)}", "s": "対数積分法", "a": r"\log |f(x)| + C"},
        {"q": r"\sin^2 x", "s": "半角の公式で次数下げ", "a": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"}
    ]

# 4. メインロジック（ここを一番シンプルにしました）
st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if sub == "数Ⅲ積分 定石":
    # 以前のゴミデータを強制削除
    if "math_idx" not in st.session_state:
        st.session_state.math_idx = 0
        st.session_state.math_ans = False

    data = load_math()
    idx = st.session_state.math_idx % len(data)
    row = data[idx]

    # --- 表示 ---
    st.write("### 数Ⅲ積分：定石確認")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.latex(r"\int " + row["q"] + r" \, dx")
    st.markdown('</div>', unsafe_allow_html=True)

    if not st.session_state.math_ans:
        if st.button("解答を確認する"):
            st.session_state.math_ans = True
            st.rerun()
    else:
        st.success(f"💡 定石：{row['s']}")
        st.latex(row["a"])
        if st.button("次の問題へ"):
            st.session_state.math_idx += 1
            st.session_state.math_ans = False
            st.rerun()

elif sub == "システム英単語":
    try:
        df = pd.read_csv("final_tango_list.csv", encoding="utf-8-sig")
        st.write("### システム英単語モード")
        # 最小限の表示
        row_e = df.sample(1).iloc[0]
        st.info(f"例文: {row_e['sentence']}")
        st.write(f"意味: {row_e['all_answers']}")
        if st.button("次の単語"):
            st.rerun()
    except:
        st.error("英単語CSVが読み込めません。GitHubにあるか確認してください。")

else:
    st.info("←左のサイドバーから「数Ⅲ積分 定石」を選んでください！")