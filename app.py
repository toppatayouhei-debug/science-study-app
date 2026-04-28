import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. デザイン設定
# ==========================================
st.set_page_config(page_title="理系には、勝ち方がある", page_icon="🧬", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }
.header-container {
    text-align: center;
    margin-top: 10px;
    margin-bottom: 25px;
}
.science-icon {
    font-size: 3rem;
    margin-bottom: 5px;
}
.main-title {
    color: #1e3a8a;
    font-size: 2.2rem;
    font-weight: 800;
    margin: 0;
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
    margin-bottom: 15px !important;
}
.highlight { color: #ff9800 !important; font-weight: bold !important; }
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
.stMarkdown p { font-size: 1.1rem !important; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データ読み込み関数
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    try:
        df = pd.read_csv(file_map[subject], encoding="utf-8-sig").dropna(how='all')
        df.columns = df.columns.str.strip()
        # 数学の場合、バックスラッシュが消えないようにエスケープ処理を事前に行う
        if "数学" in subject:
            df = df.replace(r'\\', r'\\\\', regex=True)
        return df
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
        return pd.DataFrame()

# ヘッダー表示
st.markdown("""
<div class="header-container">
    <div class="science-icon">🧬🧪⚛️</div>
    <div class="main-title">理系には、勝ち方がある</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if sub == "選択してください":
    st.markdown("""
    <div class="concept-section">
        <strong>■ Goal</strong><br>
        ・<b>英単語</b>：リーディングで「見て意味がわかる」単語を増やす。<br>
        ・<b>数学</b>：入試数学の定石を定着させ、基礎力をつける。<br><br>
        <strong>■ Strategy</strong><br>
        ① 入試問題を解くための「基本」を即答できるレベルにする。<br>
        ② 形を見た瞬間に解き方が思い浮かぶようにする。<br>
        ③ 解き方の「型」の習得が目標です。
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df_raw = load_data(sub)
if df_raw.empty:
    st.warning(f"「{sub}」用のCSVファイルが見つかりません。")
    st.stop()

# ==========================================
# 3. フィルタリング設定
# ==========================================
if sub == "システム英単語":
    lv_map = {"すべて":"All", "Fundamental (1-600)":"Fundamental", "Essential (601-1200)":"Essential", "Advanced (1201-1700)":"Advanced", "Final (1701-2027)":"Final"}
    selected_filter = st.sidebar.radio("レベル", list(lv_map.keys()))
    filter_keyword, filter_col = lv_map[selected_filter], "level"
else:
    all_cats = df_raw["category"].unique().tolist()
    priority_cats = [c for c in all_cats if any(kw in str(c) for kw in ["微分", "積分", "極限"])]
    other_cats = [c for c in all_cats if c not in priority_cats]
    cats = ["すべて"] + sorted(priority_cats) + sorted(other_cats)
    selected_filter = st.sidebar.radio("分野", cats)
    filter_keyword, filter_col = selected_filter, "category"

# セッション管理
if "current_sub" not in st.session_state or st.session_state.current_sub != sub or st.session_state.get("last_filter") != selected_filter:
    st.session_state.current_sub = sub
    st.session_state.last_filter = selected_filter
    df_f = df_raw.copy()
    if selected_filter != "すべて":
        df_f = df_raw[df_raw[filter_col].astype(str).str.contains(filter_keyword, case=False, na=False)]
    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty:
    st.warning("該当する問題がありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. 表示ロジック
# ==========================================

# --- 英単語 ---
if sub == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        st.session_state.correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != st.session_state.correct]
        st.session_state.choices = random.sample([st.session_state.correct] + random.sample(dummies, min(3, len(dummies))), 4)
    
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
            if "choices" in st.session_state: del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

# --- 数学 ---
else:
    st.markdown(f'<div class="card blue-card">【{row["category"]}】例題</div>', unsafe_allow_html=True)
    
    # 問題文のレンダリング
    q_text = str(row["question"])
    st.markdown(q_text)
    
    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.write("**💡 定石・方針**")
        st.info(str(row['strategy']))
        
        st.write("**【解答・略解】**")
        ans_raw = str(row["answer"])
        
        # 数式表示の修正：$を取り除き、$$で囲むことで分数を大きく表示
        clean_ans = ans_raw.replace('$', '')
        
        # 数式記号が含まれる場合、ディスプレイモード（$$）で表示
        if any(c in clean_ans for c in ['\\', '^', '_', '{', '}', 'int', 'lim', 'frac', 'log', 'sin', 'cos', 'tan']):
            # 改行を入れることで確実にディスプレイ形式を適用
            st.markdown(f"$$\n{clean_ans}\n$$")
        else:
            st.write(ans_raw)
        
        if "explanation" in row and pd.notna(row["explanation"]):
            st.write("**📝 ポイント解説**")
            exp_text = str(row["explanation"])
            # 解説内でも数式が表示されるようにする
            st.info(exp_text)
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()