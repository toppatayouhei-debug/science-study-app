import streamlit as st
import pandas as pd
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
# 2. 究極安定・単一行レンダリングエンジン
# ==========================================
def total_math_cleaner(text):
    """数式パーツをLaTeXへ安全変換"""
    if not text:
        return ""

    t = str(text).strip()
    t = t.replace('$', '')
    t = t.replace('displaystyle', '')

    # 関数
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp']
    for f in funcs:
        t = re.sub(rf'\b{f}\b', rf'\\{f}', t)

    # 記号
    t = re.sub(r'\btheta\b', r'\\theta', t)
    t = re.sub(r'\bpi\b', r'\\pi', t)
    t = re.sub(r'\binfty\b', r'\\infty', t)
    t = re.sub(r'\bint\b', r'\\int', t)
    t = re.sub(r'\btimes\b', r'\\times', t)
    t = re.sub(r'\bdots\b', r'\\dots', t)

    # sqrt(x)
    t = re.sub(r'sqrt\s*\((.*?)\)', r'\\sqrt{\1}', t)

    # x^2 → x^{2}
    t = re.sub(r'\^([0-9a-zA-Z]+)', r'^{\1}', t)

    # 1/2 → \frac{1}{2}
    t = re.sub(r'(?<![a-zA-Z0-9}])(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # dx
    t = t.replace('dx', r'\,dx')
    t = t.replace('dt', r'\,dt')

    return t.strip()


def unified_render(text, is_main=False):
    """日本語文中の(数式)だけLaTeX化"""
    if not text or pd.isna(text):
        return ""

    raw = str(text).replace('\u3000', ' ').replace('\xa0', ' ').strip()

    def repl(match):
        inner = match.group(1).strip()
        cleaned = total_math_cleaner(inner)
        style = r"\displaystyle " if is_main else ""
        return f"${style}{cleaned}$"

    # ( ) 内のみ数式化
    processed = re.sub(r'\((.*?)\)', repl, raw)

    return processed

# ==========================================
# 3. アプリロジック
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }

    file_path = file_map.get(subject)
    if not file_path:
        return pd.DataFrame()

    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(current_dir, file_path), encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

st.title("理系には、勝ち方がある")

subject = st.sidebar.selectbox(
    "科目を選択",
    ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"]
)

if subject == "選択してください":
    st.info("サイドバーから開始してください。")
    st.stop()

df_raw = load_data(subject)

cats = ["すべて"] + list(
    df_raw["category"].unique()
    if "category" in df_raw.columns
    else df_raw["level"].unique()
)

choice = st.sidebar.radio("分野・レベル選択", cats)

df_filtered = df_raw if choice == "すべて" else df_raw[
    (df_raw.get("category") == choice) |
    (df_raw.get("level") == choice)
]

current_key = f"{subject}_{choice}"

if "session_key" not in st.session_state or st.session_state.session_key != current_key:
    st.session_state.session_key = current_key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty:
    st.stop()

row = st.session_state.df.iloc[
    st.session_state.idx % len(st.session_state.df)
]

# ==========================================
# 4. 表示
# ==========================================
if subject != "システム英単語":

    st.markdown(
        f'<div class="card blue-card">【{row.get("category", "問題")}】</div>',
        unsafe_allow_html=True
    )

    # 問題文サイズ修正（通常サイズ）
    st.markdown(unified_render(row["question"], is_main=True))

    if not st.session_state.answered:

        if st.button("解法・定石を確認する"):
            st.session_state.answered = True
            st.rerun()

    else:
        st.markdown("---")

        st.info(
            f"💡 **攻略の定石**\n\n{unified_render(row['strategy'])}"
        )

        st.markdown("##### 【解答】")
        st.markdown(unified_render(row["answer"], is_main=True))

        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(
                f"📝 **ポイント解説**\n\n{unified_render(row['explanation'])}"
            )

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
