import streamlit as st
import pandas as pd
import random
import re
import os

# ==========================================
# 1. デザイン設定
# ==========================================
st.set_page_config(page_title="理系には、勝ち方がある", page_icon="🧬", layout="centered")

st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }
.card {
    background-color: white !important;
    padding: 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
    margin-bottom: 20px;
}
.blue-card { border-left: 8px solid #2196f3 !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 数式処理エンジン (安全第一版)
# ==========================================
def fix_math_format(text, is_block=False):
    if not text or pd.isna(text): return ""
    # 生データの不要なバックスラッシュを削除
    t = str(text).replace('\\', '').replace('displaystyle', '')
    
    # 1. 平方根
    t = re.sub(r'sqrt\s*\(?([0-9a-zA-Z]+)\)?', r'\\sqrt{\1}', t)
    
    # 2. 指数（肩）の修正
    t = re.sub(r'\^([0-9a-zA-Z]+)', r'^{\1}', t)
    
    # 3. 組合せ・度数
    t = t.replace('circ', r'^{\circ}')
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 4. 分数 (ブロック表示のみ)
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 5. 数学関数へのバックスラッシュ付与
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'alpha', 'beta', 'gamma']
    for f in funcs:
        t = re.sub(rf'\b{f}\b', rf'\\{f}', t)
    
    # 虚数単位 i を安全にイタリック化
    # エラーの原因となった \mathit を避け、単純な $i$ 扱いに寄せる
    if not is_block:
        t = re.sub(r'\b(i)\b', r'i', t) # LaTeX内ではデフォルトでイタリックになるためシンプルに

    return t.strip()

def render_mixed(text):
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # ( ... ) で囲まれた部分を数式として抽出
    parts = re.split(r'(\(.*?\))', raw)
    res = ""
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            res += f" ${fix_math_format(p[1:-1])}$ "
        else:
            # 地文パート
            res += p.replace('\\', '').replace('circ', '°').replace('sqrt', '√')
    return res

# ==========================================
# 3. データ読み込み & サイドバー制御
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {"システム英単語": "final_tango_list.csv", "入試数学の定石（数Ⅲ）": "math3.csv", "入試数学の定石（ⅠAⅡB C）": "math_std.csv"}
    file_path = file_map.get(subject)
    if not file_path: return pd.DataFrame()
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(current_dir, file_path), encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

st.title("理系には、勝ち方がある")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if subject == "選択してください":
    st.info("左のサイドバーから開始してください。")
    st.stop()

df_raw = load_data(subject)

# 分野フィルタリング
if subject == "システム英単語":
    choice = st.sidebar.radio("レベル", ["すべて"] + list(df_raw["level"].unique()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["level"] == choice]
else:
    choice = st.sidebar.radio("分野", ["すべて"] + list(df_raw["category"].unique()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["category"] == choice]

# セッション状態の管理
filter_key = f"{subject}_{choice}"
if "current_key" not in st.session_state or st.session_state.current_key != filter_key:
    st.session_state.current_key = filter_key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty: st.stop()
row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. 表示
# ==========================================
if subject != "システム英単語":
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    st.latex(rf"\displaystyle {fix_math_format(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.info(f"💡 **攻略の定石**\n\n{render_mixed(row['strategy'])}")
        st.latex(rf"\displaystyle {fix_math_format(row['answer'], is_block=True)}")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{render_mixed(row['explanation'])}")
        if st.button("次へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
