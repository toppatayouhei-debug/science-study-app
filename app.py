import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. デザイン設定
# ==========================================
st.set_page_config(page_title="理系には、勝ち方がある", page_icon="🧬")

st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }
.main-title {
    color: #1e3a8a;
    font-size: 2.2rem;
    font-weight: 800;
    text-align: center;
    margin-top: 10px;
    margin-bottom: 20px;
}
.concept-section {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #1e3a8a;
    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 20px;
}
.card { 
    background-color: white !important; 
    padding: 15px 20px !important; 
    border-radius: 12px !important; 
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important; 
    margin-bottom: 10px !important;
}
.highlight { color: #ff9800 !important; font-weight: bold !important; }
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 補助関数
# ==========================================
def format_math_text(text):
    if pd.isna(text): return ""
    text = str(text).strip().replace("−", "-").replace("　", " ")
    if text.startswith("$") and text.endswith("$"): return text
    clean_text = text.replace("$", "").strip()
    keywords = ["\\", "^", "_", "{", "}", "/", "sin", "cos", "tan", "log", "int", "theta", "pi", "exp", "sqrt"]
    is_math = any(k in clean_text.lower() for k in keywords) or any(c in clean_text for c in ["+", "=", "(", ")"])
    return f"${clean_text}$" if is_math else clean_text

def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3_integration.csv"
    }
    try:
        df = pd.read_csv(file_map[subject], encoding="utf-8-sig").dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 3. メイン画面表示
# ==========================================
st.markdown('<div class="main-title">理系には、勝ち方がある</div>', unsafe_allow_html=True)

st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）"])

if sub == "選択してください":
    st.markdown(f"""
    <div class="concept-section">
        <strong>■ アプリの目的</strong><br>
        入試数学の計算パターン（定石）を反射レベルで定着させ、応用問題に割く思考リソースを最大化する。<br><br>
        <strong>■ 学習の手順</strong><br>
        1. <b>選択</b>：サイドバーから分野（微分・積分）を選ぶ。<br>
        2. <b>想起</b>：問題に対し、使うべき定石（公式・置換・変形）を瞬時に導き出す。<br>
        3. <b>確認</b>：解答と照らし合わせ、ズレを修正する。
    </div>
    """, unsafe_allow_html=True)
    st.info("← 左のサイドバーから科目を選択してください。")
    st.stop()

# --- データロード ---
df_raw = load_data(sub)
if df_raw.empty:
    st.warning("CSVファイルが見つかりません。")
    st.stop()

# --- フィルター設定 ---
if sub == "システム英単語":
    lv_map = {"すべて":"All", "Fundamental (1-600)":"Fundamental", "Essential (601-1200)":"Essential", "Advanced (1201-1700)":"Advanced", "Final (1701-2027)":"Final"}
    selected_filter = st.sidebar.radio("レベル", list(lv_map.keys()))
    filter_keyword, filter_col = lv_map[selected_filter], "level"
else:
    cats = ["すべて"] + sorted(df_raw["category"].unique().tolist())
    selected_filter = st.sidebar.radio("分野", cats)
    filter_keyword, filter_col = selected_filter, "category"

# --- セッション管理 ---
if "current_sub" not in st.session_state or st.session_state.current_sub != sub or st.session_state.get("last_filter") != selected_filter:
    st.session_state.current_sub, st.session_state.last_filter = sub, selected_filter
    df_f = df_raw.copy()
    if selected_filter != "すべて":
        df_f = df_raw[df_raw[filter_col].astype(str).str.contains(filter_keyword, case=False, na=False)]
    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True)
    st.session_state.idx, st.session_state.answered = 0, False

if st.session_state.df.empty:
    st.warning("該当する問題がありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. コンテンツ表示
# ==========================================
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
        if st.session_state.selected == st.session_state.correct: st.success("正解")
        else: st.error(f"正解：{st.session_state.correct}")
        st.write(f"意味：{row['all_answers']}")
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

elif sub == "入試数学の定石（数Ⅲ）":
    is_diff = "微分" in str(row["category"])
    task = "次の関数を微分せよ：" if is_diff else "次の不定積分を求めよ："
    st.markdown(f'<div class="card blue-card">【{row["category"]}】{task}</div>', unsafe_allow_html=True)
    
    if is_diff: st.latex(r"y = " + str(row["question"]))
    else: st.latex(r"\int " + str(row["question"]) + r" \, dx")
    
    if not st.session_state.answered:
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.write("**💡 定石：**")
        st.markdown(format_math_text(row['strategy']))
        st.write("**【解答】**")
        ans_raw = str(row["answer"])
        if re.search(r'[ぁ-んァ-ヶ亜-熙]', ans_raw):
            st.markdown(format_math_text(ans_raw))
        else:
            prefix = "y' = " if is_diff else ""
            st.latex(prefix + ans_raw.replace("$", "").strip())
        
        if "explanation" in row and pd.notna(row["explanation"]):
            st.write("---")
            st.markdown(f"**📝 解説:**")
            st.markdown(format_math_text(row["explanation"]))
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()