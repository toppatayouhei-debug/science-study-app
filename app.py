import streamlit as st
import pandas as pd
import random
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
# 2. 数式レンダリング（完全安全版）
# ==========================================
def render_math(text):
    """
    LaTeXを一切壊さずにそのまま表示する
    """
    if text is None or pd.isna(text):
        return ""

    text = str(text)

    # 改行だけ整形（数式は絶対触らない）
    text = text.replace("\\n", "\n")

    # ( ) を軽く数式扱いしたい場合のみ
    # → 中身は一切変更しない
    text = re.sub(r'\((.*?)\)', r'$\1$', text)

    return text


# ==========================================
# 3. 解説UI（関数化）
# ==========================================
def show_strategy(text):
    st.markdown("### 💡 攻略の定石")
    st.markdown(render_math(text))


def show_explanation(text):
    st.markdown("### 📝 ポイント解説")
    st.markdown(render_math(text))


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

    file_path = file_map.get(subject)
    if not file_path:
        return pd.DataFrame()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)

    try:
        df = pd.read_csv(full_path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return pd.DataFrame()


# ==========================================
# 5. UI
# ==========================================
st.title("理系には、勝ち方がある")

subject = st.sidebar.selectbox(
    "科目を選択",
    ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"]
)

if subject == "選択してください":
    st.stop()

df = load_data(subject)

if df.empty:
    st.error("データがありません")
    st.stop()

cats = ["すべて"] + list(df["category"].dropna().unique())
choice = st.sidebar.radio("分野", cats)

if choice != "すべて":
    df = df[df["category"] == choice]

if "idx" not in st.session_state:
    st.session_state.idx = 0
    st.session_state.answered = False

row = df.iloc[st.session_state.idx % len(df)]

# ==========================================
# 6. 表示
# ==========================================
st.markdown(f"""
<div class="card blue-card">
【{row.get('category','')}】
</div>
""", unsafe_allow_html=True)

st.markdown("## " + render_math(row["question"]))

if not st.session_state.answered:
    if st.button("解法・定石を見る"):
        st.session_state.answered = True
        st.rerun()

else:
    st.markdown("---")

    show_strategy(row.get("strategy", ""))

    st.markdown("### 【解答】")
    st.markdown(render_math(row.get("answer", "")))

    if "explanation" in row and pd.notna(row["explanation"]):
        show_explanation(row["explanation"])

    if st.button("次へ"):
        st.session_state.idx += 1
        st.session_state.answered = False
        st.rerun()
