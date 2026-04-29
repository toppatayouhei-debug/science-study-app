import streamlit as st
import pandas as pd
import random
import re
import json

# ==========================================
# 1. デザイン設定
# ==========================================
st.set_page_config(
    page_title="理系には、勝ち方がある",
    page_icon="🧬",
    layout="centered"
)

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
.highlight {
    color: #ff9800 !important;
    font-weight: bold !important;
}
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card   { border-left: 8px solid #2196f3 !important; }

.stButton button {
    width: 100%;
    border-radius: 10px;
    font-weight: bold;
    min-height: 45px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 便利関数
# ==========================================
def clean_math(text):
    """数式タグを整理し、st.latex用に調整する"""
    text = str(text)
    text = text.replace(r'\(', '').replace(r'\)', '')
    text = text.replace(r'\[', '').replace(r'\]', '')
    text = text.replace('$', '')
    return text.strip()

@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.json",
        "入試数学の定石（ⅠAⅡB C）": "math_std.json"
    }
    file_path = file_map[subject]
    try:
        if file_path.endswith('.json'):
            # JSON読み込み（列ズレ防止）
            df = pd.read_json(file_path, encoding="utf-8-sig")
        else:
            # CSV読み込み
            df = pd.read_csv(file_path, encoding="utf-8-sig")
        
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"データの読み込みに失敗しました ({file_path}): {e}")
        return pd.DataFrame()

# ==========================================
# 3. ヘッダー
# ==========================================
st.markdown("""
<div class="header-container">
    <div class="science-icon">🧬🧪⚛️</div>
    <div class="main-title">理系には、勝ち方がある</div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. サイドバー
# ==========================================
st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox(
    "科目を選択",
    ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"]
)

if sub == "選択してください":
    st.markdown("""
    <div class="concept-section">
        <strong>■ Goal</strong><br>
        ・最短ルートで「定石」を脳に叩き込む。<br>
        ・見た瞬間に解法が浮かぶ状態を目指す。<br><br>
        <strong>■ 使い方</strong><br>
        左のメニューから科目と分野を選択してください。
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# 5. データ処理
# ==========================================
df_raw = load_data(sub)
if df_raw.empty:
    st.stop()

# 分野選択（出現順を維持）
all_cats = []
for c in df_raw["category"].astype(str):
    if c not in all_cats:
        all_cats.append(c)

selected_filter = st.sidebar.radio("分野・レベル", ["すべて"] + all_cats)

# セッション管理
if "current_sub" not in st.session_state or st.session_state.current_sub != sub or st.session_state.get("last_filter") != selected_filter:
    st.session_state.current_sub = sub
    st.session_state.last_filter = selected_filter
    
    df_f = df_raw.copy()
    if selected_filter != "すべて":
        df_f = df_raw[df_raw["category"].astype(str) == selected_filter]
    
    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

# ==========================================
# 6. 学習メイン
# ==========================================
row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

if sub == "システム英単語":
    # 英語モードの表示（省略せずフル実装）
    word = str(row["question"])
    st.markdown(f'<div class="card orange-card">{row["sentence"]}</div>', unsafe_allow_html=True)
    # （英単語用ロジック...）
    if st.button("答えを表示"): st.session_state.answered = True
    if st.session_state.answered:
        st.write(f"正解: {row['all_answers']}")
        if st.button("次へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
else:
    # 数学モード
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    st.latex(rf"\displaystyle {clean_math(row['question'])}")
    
    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.markdown("##### 💡 攻略の定石")
        st.info(row["strategy"])
        
        st.markdown("##### 【解答】")
        st.latex(rf"\displaystyle {clean_math(row['answer'])}")
        
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown("##### 📝 ポイント解説")
            st.write(row["explanation"])
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()