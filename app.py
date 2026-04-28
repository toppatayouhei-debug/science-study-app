import streamlit as st
import pandas as pd
import random
import re

st.set_page_config(page_title="理系学習アプリ", page_icon="🧬")

# 【修正版CSS】MacBookのダークモードを完全に封じ込める設定
st.markdown("""
<style>
.stApp { background-color: #f8fafc !important; }
/* カードは白、文字は黒に固定 */
.card { 
    background-color: white !important; 
    padding: 20px !important; 
    border-radius: 15px !important; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; 
    margin-bottom: 15px !important; 
}
/* 数式(Latex)を強制的に黒く塗りつぶす */
.stLatex, .stLatex * {
    color: #000000 !important;
    fill: #000000 !important;
}
/* 全テキストを黒に固定 */
.card *, p, span, div { color: #111111 !important; }
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
</style>
""", unsafe_allow_html=True)

def load_data(subject):
    if subject == "システム英単語":
        try:
            return pd.read_csv("final_tango_list.csv", encoding="utf-8-sig").dropna(how='all')
        except:
            return pd.DataFrame()
    else:
        return pd.DataFrame([
            {"question": r"x \cos x", "strategy": "部分積分法", "answer": r"x \sin x + \cos x + C"},
            {"question": r"\frac{f'(x)}{f(x)}", "strategy": "対数積分法", "answer": r"\log |f(x)| + C"},
            {"question": r"\sin^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"}
        ])

st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if sub == "選択してください":
    st.info("← 左のサイドバーから科目を選択してください。")
    st.stop()

# 初期化処理
if "current_sub" not in st.session_state or st.session_state.current_sub != sub:
    for key in list(st.session_state.keys()):
        if key != "current_sub": del st.session_state[key]
    st.session_state.current_sub = sub
    
    df_raw = load_data(sub)
    # 【サイドバー復活】英単語のレベル分け
    if sub == "システム英単語" and not df_raw.empty:
        levels = {"すべて":"All", "Fundamental (1-600)":"Fundamental", "Essential (601-1200)":"Essential", "Advanced (1201-1700)":"Advanced", "Final (1701-2027)":"Final"}
        sel = st.sidebar.radio("レベルを選択", list(levels.keys()))
        if sel != "すべて":
            df_raw = df_raw[df_raw["level"].astype(str).str.contains(levels[sel], case=False, na=False)]
    
    st.session_state.df = df_raw.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if df.empty:
    st.warning("データがありません。")
    st.stop()

row = df.iloc[idx % len(df)]

if sub == "システム英単語":
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
                st.session_state.selected, st.session_state.answered = val, True
                st.rerun()
    
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"正解：{st.session_state.correct}")
        st.write(f"意味：{row['all_answers']}")
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

elif sub == "数Ⅲ積分 定石":
    st.markdown('<div class="card blue-card">', unsafe_allow_html=True)
    st.latex(r"\int " + str(row["question"]) + r" \, dx")
    st.markdown('</div>', unsafe_allow_html=True)
    if not st.session_state.answered:
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown(f"**💡 定石：{row['strategy']}**")
        st.latex(str(row["answer"]))
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()