import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. デザイン設定 (CSS)
# ==========================================
st.set_page_config(page_title="理系学習アプリ", page_icon="🧬")

st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }

/* 指示文を入れるための枠 */
.card { 
    background-color: white !important; 
    padding: 15px 20px !important; 
    border-radius: 12px !important; 
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important; 
    margin-bottom: 10px !important;
    color: #111111 !important;
}

/* オレンジハイライト（英単語用） */
.highlight {
    color: #ff9800 !important;
    font-weight: bold !important;
}

.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データの定義
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
# 3. メイン処理
# ==========================================
st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if sub == "選択してください":
    st.info("← サイドバーから科目を選択してください。")
    st.stop()

# --- サイドバーのレベル選択 ---
selected_level = "すべて"
if sub == "システム英単語":
    lv_map = {
        "すべて": "All",
        "Fundamental (1-600)": "Fundamental",
        "Essential (601-1200)": "Essential",
        "Advanced (1201-1700)": "Advanced",
        "Final (1701-2027)": "Final"
    }
    selected_level = st.sidebar.radio("レベルを選択", list(lv_map.keys()))

# --- 初期化 & データ抽出 ---
if "current_sub" not in st.session_state or st.session_state.current_sub != sub or st.session_state.get("last_level") != selected_level:
    for key in list(st.session_state.keys()):
        if key not in ["current_sub", "last_level"]: del st.session_state[key]
    
    st.session_state.current_sub = sub
    st.session_state.last_level = selected_level
    
    df_raw = load_data(sub)
    if sub == "システム英単語" and not df_raw.empty and selected_level != "すべて":
        keyword = lv_map[selected_level]
        df_raw = df_raw[df_raw["level"].astype(str).str.contains(keyword, case=False, na=False)]
    
    st.session_state.df = df_raw.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

df = st.session_state.get("df", pd.DataFrame())
if df.empty:
    st.warning("データが見つかりません。")
    st.stop()

row = df.iloc[st.session_state.idx % len(df)]

# --- 英単語表示 ---
if sub == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
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
            if st.button(val, key=f"t_{st.session_state.idx}_{i}", disabled=st.session_state.answered):
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

# --- 数学表示 (レイアウト変更版) ---
elif sub == "数Ⅲ積分 定石":
    # 枠には指示文だけ入れる
    st.markdown('<div class="card blue-card">次の不定積分を求めよ：</div>', unsafe_allow_html=True)
    
    # 数式は枠の外で、Streamlitの正規機能を使って表示（これで確実に綺麗に出る）
    st.latex(r"\int " + str(row["question"]) + r" \, dx")
    
    if not st.session_state.answered:
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.info(f"💡 定石：{row['strategy']}")
        st.write("**【解答】**")
        st.latex(str(row["answer"]))
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()