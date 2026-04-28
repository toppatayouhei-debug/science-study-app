import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. ページ設定 & 強力なデザイン設定 (CSS)
# ==========================================
st.set_page_config(page_title="理系学習アプリ", page_icon="🧬")

st.markdown("""
<style>
/* 全体の背景色 */
.stApp { background-color: #f0f2f5 !important; }

/* カードのデザイン */
.card { 
    background-color: white !important; 
    padding: 20px !important; 
    border-radius: 15px !important; 
    box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important; 
    margin-bottom: 15px !important; 
}

/* ★Macのダークモードでも絶対に見える設定★ */
/* 数式の周りに白い座布団を敷き、文字と図を黒に固定します */
.stLatex {
    background-color: white !important;
    padding: 12px !important;
    border-radius: 10px !important;
    display: inline-block !important;
}
.stLatex, .stLatex * {
    color: #000000 !important;
    fill: #000000 !important;
}

/* カード内のテキスト色を黒に固定 */
.card *, p, span, div, label { color: #111111 !important; }

/* 装飾用：左側の色線 */
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }

/* ボタンのデザイン */
.stButton button { 
    width: 100%; 
    border-radius: 10px; 
    font-weight: bold; 
    min-height: 45px; 
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データの読み込み関数 (数学20問増量版)
# ==========================================
def load_data(subject):
    if subject == "システム英単語":
        try:
            return pd.read_csv("final_tango_list.csv", encoding="utf-8-sig").dropna(how='all')
        except:
            return pd.DataFrame()
    else:
        # 数Ⅲ積分 定石 20選
        return pd.DataFrame([
            {"question": r"x \cos x", "strategy": "部分積分法", "answer": r"x \sin x + \cos x + C"},
            {"question": r"\frac{f'(x)}{f(x)}", "strategy": "対数積分法", "answer": r"\log |f(x)| + C"},
            {"question": r"\sin^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x - \frac{1}{4}\sin 2x + C"},
            {"question": r"\cos^2 x", "strategy": "半角の公式で次数下げ", "answer": r"\frac{1}{2}x + \frac{1}{4}\sin 2x + C"},
            {"question": r"\tan x", "strategy": "sin/cosに変えて対数積分", "answer": r"-\log |\cos x| + C"},
            {"question": r"\frac{1}{\tan x}", "strategy": "cos/sinに変えて対数積分", "answer": r"\log |\sin x| + C"},
            {"question": r"\log x", "strategy": "1・log x と考えて部分積分", "answer": r"x \log x - x + C"},
            {"question": r"\frac{1}{x \log x}", "strategy": "1/x を分子に持ってきて対数積分", "answer": r"\log |\log x| + C"},
            {"question": r"x e^{x}", "strategy": "部分積分法", "answer": r"(x-1)e^x + C"},
            {"question": r"e^x \sin x", "strategy": "2回部分積分して同型出現", "answer": r"\frac{1}{2}e^x(\sin x - \cos x) + C"},
            {"question": r"\frac{1}{x^2+a^2}", "strategy": "x = a \tan \theta と置換", "answer": r"\frac{1}{a}\tan^{-1}\frac{x}{a} + C"},
            {"question": r"\frac{1}{\sqrt{a^2-x^2}}", "strategy": "x = a \sin \theta と置換", "answer": r"\sin^{-1}\frac{x}{a} + C"},
            {"question": r"\sqrt{a^2-x^2}", "strategy": "x = a \sin \theta 置換 または 円の面積", "answer": r"x=a\sin\theta 置換"},
            {"question": r"\frac{1}{\cos x}", "strategy": "分母分子にcosをかけて置換積分", "answer": r"\frac{1}{2}\log|\frac{1+\sin x}{1-\sin x}|+C"},
            {"question": r"\sin^3 x", "strategy": "sin x(1-cos^2 x)に変形", "answer": r"-\cos x + \frac{1}{3}\cos^3 x + C"},
            {"question": r"\frac{1}{x^2-1}", "strategy": "部分分数分解", "answer": r"\frac{1}{2}\log|\frac{x-1}{x+1}|+C"},
            {"question": r"(ax+b)^n", "strategy": "そのまま積分して 1/a をかける", "answer": r"\frac{1}{a(n+1)}(ax+b)^{n+1} + C"},
            {"question": r"\frac{1}{\sqrt{x^2+A}}", "strategy": "公式：log|x+\sqrt{x^2+A}|", "answer": r"\log|x+\sqrt{x^2+A}| + C"},
            {"question": r"\frac{x}{\sqrt{1+x^2}}", "strategy": "根号の中身の微分が分子にある形", "answer": r"\sqrt{1+x^2} + C"},
            {"question": r"\tan^2 x", "strategy": "1/cos^2 x - 1 に変形", "answer": r"\tan x - x + C"}
        ])

# ==========================================
# 3. メイン処理 (サイドバー & 学習ロジック)
# ==========================================
st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if sub == "選択してください":
    st.info("← 左のサイドバーから科目を選択して開始してください。")
    st.stop()

# セッション状態の初期化
if "current_sub" not in st.session_state or st.session_state.current_sub != sub:
    for key in list(st.session_state.keys()):
        if key != "current_sub": del st.session_state[key]
    st.session_state.current_sub = sub
    
    df_raw = load_data(sub)
    
    # 英単語のレベル分けサイドバー
    if sub == "システム英単語" and not df_raw.empty:
        lv_map = {"すべて":"All", "1-600":"Fundamental", "601-1200":"Essential", "1201-1700":"Advanced", "1701-2027":"Final"}
        sel = st.sidebar.radio("レベルを選択", list(lv_map.keys()))
        if sel != "すべて":
            df_raw = df_raw[df_raw["level"].astype(str).str.contains(lv_map[sel], case=False, na=False)]
    
    st.session_state.df = df_raw.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

df = st.session_state.get("df", pd.DataFrame())
if df.empty:
    st.warning("データが見つかりません。")
    st.stop()

idx = st.session_state.idx
row = df.iloc[idx % len(df)]

# --- 英単語の表示 ---
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
        if st.session_state.selected == st.session_state.correct: 
            st.success(random.choice(["正解！その調子！", "ナイス！正解です", "完璧！", "冴えてるね！"]))
        else: 
            st.error(f"正解：{st.session_state.correct}")
        st.write(f"**意味：** {row['all_answers']}")
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

# --- 数学の表示 ---
elif sub == "数Ⅲ積分 定石":
    st.markdown('<div class="card blue-card">', unsafe_allow_html=True)
    # 積分記号を付与して表示
    st.latex(r"\int " + str(row["question"]) + r" \, dx")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not st.session_state.answered:
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown(f"**💡 解法の定石：{row['strategy']}**")
        st.latex(str(row["answer"]))
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()