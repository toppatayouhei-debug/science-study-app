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
# 2. 数式処理エンジン (安定版)
# ==========================================
def fix_math_format(text, is_block=False):
    if not text or pd.isna(text): return ""
    t = str(text).replace('\\', '').replace('displaystyle', '')
    
    # 指数（肩）の修正: x^2+x+1 -> x^{2}+x+1
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', lambda m: f"^{{{m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()}}}{m.group(1)[len(m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()):]}", t)
    
    # 組合せ、平方根、度数
    t = t.replace('circ', r'^{\circ}')
    t = re.sub(r'sqrt\((.*?)\)', r'\\sqrt{\1}', t)
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 独立行（問題・解答）のみ分数を \frac 化
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 数学関数
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi']
    for f in funcs:
        t = re.sub(rf'\b{f}\b', rf'\\{f}', t)
    return t.strip()

def render_mixed(text):
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    parts = re.split(r'(\(.*?\))', raw)
    res = ""
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            res += f" ${fix_math_format(p[1:-1])}$ "
        else:
            res += p.replace('\\', '').replace('circ', '°')
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
    st.info("サイドバーから科目を選択してください。")
    st.stop()

df_raw = load_data(subject)

# 分野フィルタリング
if subject == "システム英単語":
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    choice = st.sidebar.radio("レベル", list(lv_map.keys()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["level"] == lv_map[choice]]
else:
    cats = ["すべて"] + list(df_raw["category"].unique())
    choice = st.sidebar.radio("分野", cats)
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["category"] == choice]

# --- 状態のリセット（ここがサイドバー機能の肝） ---
filter_key = f"{subject}_{choice}"
if "filter_key" not in st.session_state or st.session_state.filter_key != filter_key:
    st.session_state.filter_key = filter_key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty:
    st.warning("該当するデータがありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. メインコンテンツ
# ==========================================
if subject != "システム英単語":
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    st.latex(rf"\displaystyle {fix_math_format(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.info(f"💡 **攻略の定石**\n\n{render_mixed(row['strategy'])}")
        st.latex(rf"\displaystyle {fix_math_format(row['answer'], is_block=True)}")
        
        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{render_mixed(row['explanation'])}")

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
else:
    # 英語モード
    st.write(f"**Level: {row['level']}**")
    st.markdown(f"### {row['sentence'].replace(row['question'], f'**{row[u'question']}**')}")
    if not st.session_state.answered:
        if st.button("答えを見る"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.success(f"正解: {row['all_answers']}")
        if st.button("次へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
