import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. ページ設定 & デザイン
# ==========================================
st.set_page_config(page_title="理系学習アプリ", page_icon="🧬", layout="centered")

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
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }
</style>
""", unsafe_allow_html=True)

def reset_engine():
    for k in ["df", "idx", "answered", "choices", "correct", "selected"]:
        if k in st.session_state: del st.session_state[k]

# ==========================================
# 2. データの読み込み
# ==========================================
def load_data(subject):
    if subject == "システム英単語":
        try:
            # 成功していたCSV読み込みを復活
            return pd.read_csv("final_tango_list.csv", encoding="utf-8-sig").dropna(how='all')
        except:
            return pd.DataFrame()
    else:
        # 数学は100%動くようにコード内に直接埋め込み
        return pd.DataFrame([
            {"question": r"x \cos x", "strategy": "部分積分法", "answer": r"x \sin x + \cos x + C"},
            {"question": r"\frac{f'(x)}{f(x)}", "strategy": "対数積分法", "answer": r"\log |f(x)| + C"},
            {"question": r"\sin^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"}
        ])

# ==========================================
# 3. 学習ロジック
# ==========================================
st.sidebar.title("🧬 理系学習メニュー")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if subject == "選択してください":
    st.info("← サイドバーから科目を選択して開始してください。")
    st.stop()

# 科目が変わった、または初回実行時の処理
if "current_sub" not in st.session_state or st.session_state.current_sub != subject:
    reset_engine()
    st.session_state.current_sub = subject
    df = load_data(subject)
    
    # 【英単語のレベル分けを完全復活】
    if subject == "システム英単語" and not df.empty:
        levels_map = {
            "すべて": "All", 
            "Fundamental (1-600)": "Fundamental", 
            "Essential (601-1200)": "Essential", 
            "Advanced (1201-1700)": "Advanced", 
            "Final (1701-2027)": "Final"
        }
        # ラジオボタンはサイドバーに固定
        sel_level = st.sidebar.radio("レベル選択", list(levels_map.keys()))
        if sel_level != "すべて":
            df = df[df["level"].astype(str).str.contains(levels_map[sel_level], case=False, na=False)]
    
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0

# 現在のデータを取得
active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if active_df.empty:
    st.warning("データが見つかりません。")
    st.stop()

if idx >= len(active_df):
    st.balloons(); st.success("🎉 全問終了です！")
    if st.button("もう一度最初から"): reset_engine(); st.rerun()
    st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==========================================
# 4. 表示セクション
# ==========================================
if subject == "システム英単語":
    # 英単語クイズのUIを復元
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
    for i, val in enumerate(st.session_state.choices):
        with (c1 if i % 2 == 0 else c2):
            if st.button(val, key=f"tango_{idx}_{i}", disabled=st.session_state.get("answered", False)):
                st.session_state.selected, st.session_state.answered = val, True
                st.rerun()
    
    if st.session_state.get("answered"):
        if st.session_state.selected == st.session_state.correct: st.success("✨ 正解！")
        else: st.error(f"❌ 正解は：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif subject == "数Ⅲ積分 定石":
    # 数学のUI
    st.markdown('<div class="card blue-card">', unsafe_allow_html=True)
    st.latex(r"\int " + str(row["question"]) + r" \, dx")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.get("answered", False):
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.info(f"💡 定石：{row['strategy']}")
        st.latex(str(row["answer"]))
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()