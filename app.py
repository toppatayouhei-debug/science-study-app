import streamlit as st
import pandas as pd
import random
import re
import os

# ==========================================
# 1. ページ設定
# ==========================================
st.set_page_config(
    page_title="理系には、勝ち方がある",
    page_icon="🧬",
    layout="centered"
)

# ==========================================
# 2. デザイン
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }
.card {
    background-color: white !important;
    padding: 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
    margin-bottom: 18px;
}
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }
.highlight { color: #ff9800 !important; font-weight: bold !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 究極安定化・数式処理
# ==========================================
def total_math_cleaner(text):
    """数式パーツからノイズを徹底除去"""
    if not text or pd.isna(text): return ""
    t = str(text).replace('\\', '').replace('displaystyle', '').replace('$', '').strip()
    
    # 記号置換
    t = t.replace('theta', r'\theta ').replace('pi', r'\pi ')
    t = t.replace('sin', r'\sin ').replace('cos', r'\cos ').replace('tan', r'\tan ')
    t = t.replace('int', r'\int ').replace('vec', r'\vec ').replace('sqrt', r'\sqrt ')
    t = t.replace('times', r'\times ').replace('dots', r'\dots ').replace('infty', r'\infty ')
    t = t.replace('circ', r'^{\circ}').replace('dx', r'\,dx').replace('dt', r'\,dt')
    
    # 指数（肩）
    t = re.sub(r'\^([0-9a-zA-Z]+)', r'^{ \1 }', t)
    
    # ASCII以外のノイズ（？）を徹底除去
    t = "".join(char for char in t if 32 <= ord(char) <= 126 or char in '^{}_\\')
    return t.strip()

def unified_render(text, is_main=False):
    """日本語と数式を一つの Markdown として統合"""
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\u3000', ' ').replace('\xa0', ' ').replace('\\n', '\n').strip()
    
    def replace_with_math(match):
        inner = total_math_cleaner(match.group(1).strip())
        style = r"\displaystyle " if is_main else ""
        return f"$ {style}{inner} $"

    # ( ) 内を数式化、単独数字も数式化
    processed = re.sub(r'\((.*?)\)', replace_with_math, raw)
    processed = re.sub(r'(?<![0-9$])\b(\d+)\b(?![0-9$])', r'$ \1 $', processed)
    return processed

# ==========================================
# 4. データ読み込み
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    file_name = file_map.get(subject)
    if not file_name: return pd.DataFrame()
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(base, file_name), encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return pd.DataFrame()

# ==========================================
# 5. メインロジック
# ==========================================
st.markdown('<div class="header-container"><div class="main-title">理系には、勝ち方がある</div></div>', unsafe_allow_html=True)

st.sidebar.title("🧬 学習メニュー")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if subject == "選択してください":
    st.info("左のサイドバーから学習したい科目を選択してください。")
    st.stop()

df_raw = load_data(subject)

# --- 分野・単元選択の修正箇所 ---
if subject == "システム英単語":
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter = lv_map[filter_label]
    filter_col = "level"
else:
    # 1. 重複を除去してリスト化
    all_cats = df_raw["category"].astype(str).unique().tolist()
    # 2. 「空間ベクトル”」を除去 (完全一致と、念のためトリミング後一致の両方)
    cats = [c for c in all_cats if c.strip() != "空間ベクトル”"]
    
    filter_label = st.sidebar.radio("分野・単元選択", ["すべて"] + cats)
    current_filter = filter_label
    filter_col = "category"

# ==========================================
# 9. セッション管理 & 表示
# ==========================================
if "current_sub" not in st.session_state or st.session_state.current_sub != subject or st.session_state.get("last_filter") != filter_label:
    st.session_state.current_sub = subject
    st.session_state.last_filter = filter_label
    df = df_raw.copy() if filter_label == "すべて" else df_raw[df_raw[filter_col].astype(str).str.contains(current_filter, case=False, na=False)]
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty:
    st.error("該当データがありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# 表示ロジック（英単語/数学）
if subject == "システム英単語":
    # (既存の英単語モード処理... 変更なし)
    word = str(row["question"])
    sentence = str(row["sentence"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", sentence, flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    # ...（中略：選択肢ボタン処理）...
    # (既存のコードと同様のため省略)
else:
    # 数学モード
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    st.markdown(f"#### {unified_render(row['question'], is_main=True)}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.info(f"💡 **攻略の定石**\n\n{unified_render(row['strategy'])}")
        st.markdown("##### 【解答】")
        st.markdown(unified_render(row['answer'], is_main=True))
        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{unified_render(row['explanation'])}")
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
