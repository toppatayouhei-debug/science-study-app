import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. ページ設定
# ==========================================
st.set_page_config(page_title="理系学習アプリ", page_icon="🧬")

st.markdown("""
<style>
.stApp { background:#f8fafc; }
.card { 
    background:white; padding:22px; border-radius:18px; 
    box-shadow:0 4px 15px rgba(0,0,0,0.05); margin-bottom:1rem; 
    color: #111 !important; 
}
.orange-card { border-left: 8px solid #ff9800; }
.blue-card   { border-left: 8px solid #2196f3; }
.stButton button { width: 100%; border-radius: 12px; font-weight: 800; min-height: 50px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データの準備
# ==========================================
def get_data(subject):
    if subject == "システム英単語":
        try:
            return pd.read_csv("final_tango_list.csv", encoding="utf-8-sig").dropna(how='all')
        except:
            return pd.DataFrame()
    else:
        # 数学はコード内に直接記述（CSV不要）
        return pd.DataFrame([
            {"question": r"x \cos x", "strategy": "部分積分法", "answer": r"x \sin x + \cos x + C"},
            {"question": r"\frac{f'(x)}{f(x)}", "strategy": "対数積分法", "answer": r"\log |f(x)| + C"},
            {"question": r"\sin^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"}
        ])

# ==========================================
# 3. メイン処理
# ==========================================
st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if sub == "選択してください":
    st.info("← サイドバーから科目を選択してください。")
    st.stop()

# 状態の初期化（ここが最重要）
if "current_sub" not in st.session_state or st.session_state.current_sub != sub:
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.current_sub = sub
    st.session_state.idx = 0
    st.session_state.answered = False
    
    df = get_data(sub)
    if sub == "システム英単語" and not df.empty:
        # レベル分け
        levels = {"すべて":"All", "Fundamental (1-600)":"Fundamental", "Essential (601-1200)":"Essential", "Advanced (1201-1700)":"Advanced", "Final (1701-2027)":"Final"}
        sel = st.sidebar.radio("レベル", list(levels.keys()), key="eng_level")
        if sel != "すべて":
            df = df[df["level"].astype(str).str.contains(levels[sel], case=False, na=False)]
    
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)

# データの取得
df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if df.empty:
    st.warning("データがありません。")
    st.stop()

row = df.iloc[idx]
st.progress((idx + 1) / len(df))

# ==========================================
# 4. 表示
# ==========================================
if sub == "数Ⅲ積分 定石":
    st.markdown('<div class="card blue-card">', unsafe_allow_html=True)
    try:
        st.latex(r"\int " + str(row["question"]) + r" \, dx")
    except:
        st.write(f"問題: {row['question']}")
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

elif sub == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span style='color:#ff9800;font-weight:bold'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        st.session_state.choices = random.sample([correct] + random.sample(dummies, min(3, len(dummies))), 4)
        st.session_state.correct = correct

    c1, c2 = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        with (c1 if i % 2 == 0 else c2):
            if st.button(val, key=f"t_{idx}_{i}", disabled=st.session_state.answered):
                st.session_state.selected = val
                st.session_state.answered = True
                st.rerun()
    
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx = (st.session_state.idx + 1) % len(df)
            st.session_state.answered = False
            st.rerun()