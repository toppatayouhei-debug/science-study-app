import streamlit as st
import pandas as pd
import random
import re

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

.stMarkdown p {
    font-size: 1.1rem !important;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データ読み込み
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }

    try:
        # CSV読み込みの安定化
        df = pd.read_csv(
            file_map[subject],
            encoding="utf-8-sig",
            sep=None,
            engine='python'
        ).dropna(how="all")

        df.columns = df.columns.str.strip()

        # category 修正
        if "category" in df.columns:
            df["category"] = (
                df["category"]
                .astype(str)
                .str.strip()
                .str.replace('"', '', regex=False)
                .str.replace("”", "", regex=False)
            )

        # 数式列のクリーニング（読み込み段階での保護）
        for col in ["question", "strategy", "answer", "explanation"]:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace("$$", "$", regex=False)
                    .str.replace("\\\\", "\\", regex=False)
                    .str.strip()
                )
        return df

    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return pd.DataFrame()

def clean_math(text):
    text = str(text)
    # $が含まれている場合は取り除き、バックスラッシュを整理
    text = text.replace("$", "")
    # CSVからの読み込み時にエスケープされている場合があるため整理
    text = text.replace("\\\\", "\\")
    return text.strip()

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
    [
        "選択してください",
        "システム英単語",
        "入試数学の定石（数Ⅲ）",
        "入試数学の定石（ⅠAⅡB C）"
    ]
)

# ==========================================
# 初期画面
# ==========================================
if sub == "選択してください":
    # 修正点：unsafe_allow_html=Trueでstrongタグ等を有効化
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

# ==========================================
# 5. データ取得
# ==========================================
df_raw = load_data(sub)

if df_raw.empty:
    st.warning(f"「{sub}」用のデータが見つかりません。")
    st.stop()

# ==========================================
# 6. フィルタ
# ==========================================
if sub == "システム英単語":
    lv_map = {
        "すべて": "All",
        "Fundamental (1-600)": "Fundamental",
        "Essential (601-1200)": "Essential",
        "Advanced (1201-1700)": "Advanced",
        "Final (1701-2027)": "Final"
    }
    selected_filter = st.sidebar.radio("レベル", list(lv_map.keys()))
    filter_keyword = lv_map[selected_filter]
    filter_col = "level"

else:
    # 修正点：sorted()を使いつつ、出現順（dict.fromkeys）で並びの崩れを防ぐ
    # 元のCSVの並び順を優先したい場合は sorted を外してください
    all_cats = list(dict.fromkeys(df_raw["category"].dropna().astype(str).tolist()))
    
    priority_cats = [c for c in all_cats if any(kw in c for kw in ["微分", "積分", "極限"])]
    other_cats = [c for c in all_cats if c not in priority_cats]
    
    # ここで並び替え。元の順序を壊したくない場合は cats = ["すべて"] + all_cats に変更
    cats = ["すべて"] + sorted(priority_cats) + sorted(other_cats)

    selected_filter = st.sidebar.radio("分野", cats)
    filter_keyword = selected_filter
    filter_col = "category"

# ==========================================
# 7. セッション初期化
# ==========================================
reset_needed = (
    "current_sub" not in st.session_state
    or st.session_state.current_sub != sub
    or st.session_state.get("last_filter") != selected_filter
)

if reset_needed:
    st.session_state.current_sub = sub
    st.session_state.last_filter = selected_filter
    df_f = df_raw.copy()

    if selected_filter != "すべて":
        df_f = df_raw[
            df_raw[filter_col].astype(str).str.contains(filter_keyword, case=False, na=False)
        ]

    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

    if "choices" in st.session_state:
        del st.session_state["choices"]

if st.session_state.df.empty:
    st.warning("該当する問題がありません。")
    st.stop()

row = st.session_state.df.iloc[
    st.session_state.idx % len(st.session_state.df)
]

# ==========================================
# 8. 英単語モード
# ==========================================
if sub == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(
        re.escape(word),
        f"<span class='highlight'>{word}</span>",
        str(row["sentence"]),
        flags=re.IGNORECASE
    )

    st.markdown(
        f'<div class="card orange-card">{sentence}</div>',
        unsafe_allow_html=True
    )

    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(3, len(dummies)))
        random.shuffle(choices)

        st.session_state.correct = correct
        st.session_state.choices = choices

    c1, c2 = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        with c1 if i % 2 == 0 else c2:
            if st.button(val, key=f"t_{st.session_state.idx}_{i}", disabled=st.session_state.answered):
                st.session_state.selected = val
                st.session_state.answered = True
                st.rerun()

    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct:
            st.success("正解")
        else:
            st.error(f"正解：{st.session_state.correct}")

        st.write(f"意味：{row['all_answers']}")
        if st.button("次の問題へ"):
            if "choices" in st.session_state:
                del st.session_state["choices"]
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

# ==========================================
# 9. 数学モード
# ==========================================
else:
    st.markdown(
        f'<div class="card blue-card">【{row["category"]}】例題</div>',
        unsafe_allow_html=True
    )

    # 修正点：LaTeXが確実にレンダリングされるよう \displaystyle を付与
    q_text = clean_math(row["question"])
    st.latex(rf"\displaystyle {q_text}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.write("**💡 定石・方針**")
        strat_text = clean_math(row["strategy"])
        
        # 修正点：バックスラッシュがあればLaTeX、なければinfoで表示
        if "\\" in strat_text:
            st.latex(rf"\displaystyle {strat_text}")
        else:
            st.info(strat_text)

        st.write("**【解答・略解】**")
        ans_text = clean_math(row["answer"])
        if any(c in ans_text for c in ['\\', '^', '_', '{', 'frac']):
            st.latex(rf"\displaystyle {ans_text}")
        else:
            st.write(ans_text)

        if "explanation" in row and pd.notna(row["explanation"]):
            st.write("**📝 ポイント解説**")
            exp_text = clean_math(row["explanation"])
            if "\\" in exp_text:
                st.latex(rf"\displaystyle {exp_text}")
            else:
                st.info(exp_text)

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()