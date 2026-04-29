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
.stApp {
    background-color: #f0f2f5 !important;
}

.header-container {
    text-align: center;
    margin-bottom: 25px;
}

.main-title {
    color: #1e3a8a;
    font-size: 2.2rem;
    font-weight: 800;
}

.card {
    background-color: white !important;
    padding: 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
    margin-bottom: 18px;
}

.orange-card {
    border-left: 8px solid #ff9800 !important;
}

.blue-card {
    border-left: 8px solid #2196f3 !important;
}

.highlight {
    color: #ff9800 !important;
    font-weight: bold !important;
}

.stButton button {
    width: 100%;
    border-radius: 10px;
    font-weight: bold;
    min-height: 45px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. 数式処理
# ==========================================
def clean_math(text):
    if pd.isna(text):
        return ""

    t = str(text).strip()

    t = t.replace("$", "")
    t = t.replace(r"\(", "")
    t = t.replace(r"\)", "")
    t = t.replace(r"\[", "")
    t = t.replace(r"\]", "")

    # x^2 → x^{2}
    t = re.sub(r'([a-zA-Z0-9\)\}])\^([0-9a-zA-Z]+)', r'\1^{\2}', t)

    return t


def render_inline_math(text):
    if pd.isna(text):
        return ""

    s = str(text)

    pattern = r'([a-zA-Z0-9\\+\-*/=^{}()]+(?:\s*[=+\-*/]\s*[a-zA-Z0-9\\+\-*/=^{}()]+)+|[a-zA-Z]+\^[0-9]+)'

    def repl(m):
        expr = clean_math(m.group(1))
        return f"${expr}$"

    return re.sub(pattern, repl, s)

# ==========================================
# 4. 表示関数（追加）
# ==========================================
def show_strategy(text):
    st.markdown("##### 💡 攻略の定石")
    st.info(str(text))


def show_explanation(text):
    if pd.isna(text) or not str(text).strip():
        return

    st.markdown("##### ポイント解説")
    st.markdown(render_inline_math(text))

# ==========================================
# 5. データ読み込み
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }

    file_name = file_map.get(subject)
    if not file_name:
        return pd.DataFrame()

    try:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, file_name)

        df = pd.read_csv(path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df

    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return pd.DataFrame()

# ==========================================
# 6. UI
# ==========================================
st.title("理系には、勝ち方がある")

subject = st.sidebar.selectbox(
    "科目を選択",
    [
        "選択してください",
        "システム英単語",
        "入試数学の定石（数Ⅲ）",
        "入試数学の定石（ⅠAⅡB C）"
    ]
)

if subject == "選択してください":
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
# 7. セッション管理
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
# 8. 英単語
# ==========================================
if subject == "システム英単語":

    word = str(row["question"])
    sentence = str(row["sentence"])

    sentence = re.sub(
        re.escape(word),
        f"<span class='highlight'>{word}</span>",
        sentence,
        flags=re.IGNORECASE
    )

    st.markdown(
        f'<div class="card orange-card">{sentence}</div>',
        unsafe_allow_html=True
    )

    if "choices" not in st.session_state:

        ans_list = [
            x.strip() for x in re.split(r'[,、;]', str(row["all_answers"]))
            if x.strip()
        ]

        correct = ans_list[0]

        dummy_pool = [
            x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"]))
            if x.strip() and x.strip() != correct
        ]

        while len(dummy_pool) < 3:
            dummy_pool.append("dummy")

        choices = [correct] + random.sample(dummy_pool, 3)
        random.shuffle(choices)

        st.session_state.choices = choices
        st.session_state.correct = correct

    cols = st.columns(2)

    for i, choice in enumerate(st.session_state.choices):
        with cols[i % 2]:
            if st.button(choice, key=f"choice_{i}", disabled=st.session_state.answered):
                st.session_state.selected = choice
                st.session_state.answered = True
                st.rerun()

    if st.session_state.answered:

        if st.session_state.selected == st.session_state.correct:
            st.success("Correct!")
        else:
            st.error(f"Incorrect... 正解：{st.session_state.correct}")

        st.write(f"意味: {row['all_answers']}")

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            del st.session_state["choices"]
            st.rerun()

# ==========================================
# 9. 数学
# ==========================================
else:

    st.markdown(
        f'<div class="card blue-card">【{row["category"]}】</div>',
        unsafe_allow_html=True
    )

    st.latex(clean_math(row["question"]))

    if not st.session_state.answered:

        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()

    else:
        st.markdown("---")

        show_strategy(row["strategy"])

        st.markdown("##### 【解答】")
        st.latex(clean_math(row["answer"]))

        show_explanation(row.get("explanation", ""))

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
