import streamlit as st
import pandas as pd
import re
import os

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
# 2. 数式修正版（完全安定版）
# ==========================================
def clean_formula(text):
    """CSVの数式文字列をLaTeXとして正しく整形"""
    if pd.isna(text):
        return ""

    t = str(text).strip()

    # $ や \( \) を除去
    t = t.replace("$", "")
    t = t.replace(r"\(", "")
    t = t.replace(r"\)", "")
    t = t.replace(r"\[", "")
    t = t.replace(r"\]", "")

    # 基本変換
    t = t.replace("theta", r"\theta")
    t = t.replace("pi", r"\pi")
    t = t.replace("sin", r"\sin")
    t = t.replace("cos", r"\cos")
    t = t.replace("tan", r"\tan")
    t = t.replace("log", r"\log")
    t = t.replace("ln", r"\ln")
    t = t.replace("sqrt", r"\sqrt")
    t = t.replace("int", r"\int")
    t = t.replace("infty", r"\infty")

    # 指数変換 x^2 → x^{2}
    t = re.sub(r'([a-zA-Z0-9\)\}])\^([0-9a-zA-Z]+)', r'\1^{\2}', t)

    return t


def text_with_inline_math(text):
    """
    日本語文中の x^2=9 のような式だけ数式化
    """
    if pd.isna(text):
        return ""

    s = str(text)

    # x^2=9 や 2x+1=0 などを $...$ に変換
    pattern = r'([a-zA-Z0-9+\-*/=^(){} ]*[=^][a-zA-Z0-9+\-*/=^(){} ]+)'

    def repl(m):
        expr = m.group(1).strip()
        expr = clean_formula(expr)
        return f"${expr}$"

    return re.sub(pattern, repl, s)

# ==========================================
# 3. データ読み込み
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
        full = os.path.join(current_dir, file_path)
        df = pd.read_csv(full, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 4. UI
# ==========================================
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
    df_raw["category"].dropna().unique()
    if "category" in df_raw.columns
    else df_raw["level"].dropna().unique()
)

choice = st.sidebar.radio("分野・レベル選択", cats)

if choice == "すべて":
    df_filtered = df_raw
else:
    if "category" in df_raw.columns:
        df_filtered = df_raw[df_raw["category"] == choice]
    else:
        df_filtered = df_raw[df_raw["level"] == choice]

# ==========================================
# 5. セッション管理
# ==========================================
key = f"{subject}_{choice}"

if "session_key" not in st.session_state or st.session_state.session_key != key:
    st.session_state.session_key = key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty:
    st.stop()

row = st.session_state.df.iloc[
    st.session_state.idx % len(st.session_state.df)
]

# ==========================================
# 6. 数学表示
# ==========================================
if subject != "システム英単語":

    st.markdown(
        f'<div class="card blue-card">【{row["category"]}】</div>',
        unsafe_allow_html=True
    )

    # 問題文（サイズ普通）
    st.markdown(text_with_inline_math(row["question"]))

    if not st.session_state.answered:
        if st.button("解法・定石を確認する"):
            st.session_state.answered = True
            st.rerun()

    else:
        st.markdown("---")

        st.info("💡 攻略の定石\n\n" + str(row["strategy"]))

        st.markdown("##### 【解答】")
        st.latex(clean_formula(row["answer"]))

        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(
                "📝 ポイント解説\n\n" +
                text_with_inline_math(row["explanation"])
            )

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
