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
.header-container { text-align: center; margin-bottom: 25px; }
.main-title { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; }
.card {
    background-color: white !important; padding: 20px !important;
    border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
}
.highlight { color: #ff9800 !important; font-weight: bold !important; }
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card   { border-left: 8px solid #2196f3 !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 便利関数
# ==========================================
def clean_math(text):
    """数式タグを整理し、st.latex用に調整する"""
    text = str(text)
    # LaTeX表示を阻害する記号をクリーニング
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
    file_path = file_map.get(subject)
    if not file_path:
        return pd.DataFrame()
    
    try:
        if file_path.endswith('.json'):
            df = pd.read_json(file_path, encoding="utf-8-sig")
        else:
            df = pd.read_csv(file_path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"データの読み込みに失敗しました ({file_path}): {e}")
        return pd.DataFrame()

# ==========================================
# 3. ヘッダー & サイドバー
# ==========================================
st.markdown('<div class="header-container"><div class="main-title">理系には、勝ち方がある</div></div>', unsafe_allow_html=True)

st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox(
    "科目を選択",
    ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"]
)

if sub == "選択してください":
    st.markdown("左のサイドバーから学習したい科目を選択してください。")
    st.stop()

# ==========================================
# 4. データ準備とフィルタリング
# ==========================================
df_raw = load_data(sub)
if df_raw.empty:
    st.warning("データファイルが見つかりません。")
    st.stop()

# フィルタ項目の設定
if sub == "システム英単語":
    lv_map = {
        "すべて": "All",
        "Fundamental (1-600)": "Fundamental",
        "Essential (601-1200)": "Essential",
        "Advanced (1201-1700)": "Advanced",
        "Final (1701-2027)": "Final"
    }
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter_val = lv_map[filter_label]
    filter_col = "level"
else:
    all_cats = []
    for c in df_raw["category"].astype(str):
        if c not in all_cats:
            all_cats.append(c)
    filter_label = st.sidebar.radio("分野・単元選択", ["すべて"] + all_cats)
    current_filter_val = filter_label
    filter_col = "category"

# セッション状態の初期化・更新（科目の変更またはフィルタの変更を検知）
if "current_sub" not in st.session_state or st.session_state.current_sub != sub or st.session_state.get("last_filter") != filter_label:
    st.session_state.current_sub = sub
    st.session_state.last_filter = filter_label
    
    # フィルタリングの実行
    if filter_label == "すべて":
        df_filtered = df_raw.copy()
    else:
        # 部分一致検索（英単語のレベル名などの揺れに対応）
        df_filtered = df_raw[df_raw[filter_col].astype(str).str.contains(current_filter_val, case=False, na=False)]
    
    if df_filtered.empty:
        st.session_state.df = pd.DataFrame()
    else:
        st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    
    st.session_state.idx = 0
    st.session_state.answered = False
    if "choices" in st.session_state:
        del st.session_state["choices"]

if st.session_state.df.empty:
    st.error(f"選択された範囲（{filter_label}）に該当するデータがありません。")
    st.stop()

# 現在の問題を抽出
row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 5. 学習メイン画面
# ==========================================

# --- A. 英語モード（システム英単語） ---
if sub == "システム英単語":
    word = str(row["question"])
    # 例文内のキーワードをハイライト
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    
    # 4択肢の作成
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        
        # ダミーの作成
        dummy_pool = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        if len(dummy_pool) < 3:
            dummy_pool = dummy_pool + ["(dummy)"] * (3 - len(dummy_pool))
        
        choices = random.sample([correct] + random.sample(dummy_pool, 3), 4)
        random.shuffle(choices)
        st.session_state.choices = choices
        st.session_state.correct = correct

    # 解答ボタンの配置
    cols = st.columns(2)
    for i, choice in enumerate(st.session_state.choices):
        with (cols[0] if i % 2 == 0 else cols[1]):
            if st.button(choice, key=f"btn_{i}", disabled=st.session_state.answered):
                st.session_state.selected = choice
                st.session_state.answered = True
                st.rerun()
    
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct:
            st.success("Correct!")
        else:
            st.error(f"Incorrect... 正解：{st.session_state.correct}")
        
        st.write(f"**意味:** {row['all_answers']}")
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            del st.session_state["choices"]
            st.rerun()

# --- B. 数学モード（数Ⅲ / IAIIBC） ---
else:
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