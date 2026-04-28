import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. ページ設定 & 強制黒文字CSS
# ==========================================
st.set_page_config(page_title="理系学習アプリ", page_icon="🧬")

st.markdown("""
<style>
/* 背景を薄いグレーに */
.stApp { background:#f0f2f5; }

/* カードの設定：背景は白、文字は絶対黒 */
.card { 
    background-color: white !important; 
    padding: 25px; 
    border-radius: 18px; 
    box-shadow: 0 4px 15px rgba(0,0,0,0.1); 
    margin-bottom: 1rem; 
}

/* ★ここが重要：数式(Latex)の文字色を強制的に黒にする */
.stLatex { 
    color: #000000 !important; 
}

/* その他デザイン */
.orange-card { border-left: 8px solid #ff9800; }
.blue-card   { border-left: 8px solid #2196f3; }
.stButton button { width: 100%; border-radius: 12px; font-weight: 800; min-height: 50px; }
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }

/* 答えのテキストなども念のため黒に固定 */
.stMarkdown, p, div { color: #111111 !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データの準備
# ==========================================
def load_data(subject):
    if subject == "システム英単語":
        try:
            return pd.read_csv("final_tango_list.csv", encoding="utf-8-sig").dropna(how='all')
        except:
            return pd.DataFrame()
    else:
        # 数学データ
        return pd.DataFrame([
            {"question": r"x \cos x", "strategy": "部分積分法", "answer": r"x \sin x + \cos x + C"},
            {"question": r"\frac{f'(x)}{f(x)}", "strategy": "対数積分法", "answer": r"\log |f(x)| + C"},
            {"question": r"\sin^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"}
        ])

# ==========================================
# 3. メイン処理
# ==========================================
st.sidebar.title("🧬 理系学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if sub == "選択してください":
    st.info("← サイドバーから科目を選択してください。")
    st.stop()

# 初期化
if "current_sub" not in st.session_state or st.session_state.current_sub != sub:
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.session_state.current_sub = sub
    st.session_state.idx = 0
    st.session_state.answered = False
    df = load_data(sub)
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)

df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)
row = df.iloc[idx % len(df)]

# ==========================================
# 4. 表示：英単語
# ==========================================
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

    st.markdown('<div class="tango-btn">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        with (c1 if i % 2 == 0 else c2):
            if st.button(val, key=f"t_{idx}_{i}", disabled=st.session_state.answered):
                st.session_state.selected, st.session_state.answered = val, True
                st.rerun()
    
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"正解：{st.session_state.correct}")
        st.write(f"**意味:** {row['all_answers']}")
        st.write(f"**訳:** {row['translation']}")
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. 表示：数学
# ==========================================
elif sub == "数Ⅲ積分 定石":
    st.markdown('<div class="card blue-card">', unsafe_allow_html=True)
    # 積分記号をつけて表示
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