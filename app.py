import streamlit as st
import pandas as pd
import random
import re
import os

# ==========================================
# 1. デザイン設定 (一切の変更なし)
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
    background-color: white !important;
    padding: 20px !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important;
}
.highlight { color: #ff9800 !important; font-weight: bold !important; }
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
# 2. 便利関数 (インライン対応・最終版)
# ==========================================
def clean_math(text):
    """数式生データをLaTeXに変換"""
    if not text: return ""
    text = str(text)
    
    # 不要なエスケープの除去
    text = text.replace(r'\\', '\\').replace(r'\displaystyle', '')
    text = text.replace(r'\(', '').replace(r'\)', '').replace(r'\[', '').replace(r'\]', '').replace('$', '')

    # 累乗: x^2 -> x^{2}
    text = re.sub(r'\^([0-9a-zA-Z\(\)\{\}\-]+)', r'^{\1}', text)
    
    # 三角関数・数学記号
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'i']
    for f in funcs:
        text = re.sub(rf'(?<!\\)\b{f}\b', rf'\\{f}', text)

    # 平方根・分数
    text = re.sub(r'sqrt\((.*?)\)', r'\\sqrt{\1}', text)
    text = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', text)

    return text.strip()

def render_explanation(text):
    """インライン数式と独立行数式を判別してレンダリング"""
    if pd.isna(text): return
    
    # アイコン除去と改行正規化
    raw_text = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # 1. まず行ごとに分割
    lines = raw_text.split('\n')
    
    for line in lines:
        if not line.strip():
            continue
            
        # 2. その行が「(数式)」のみで構成されているかチェック
        # 例: "(sin^2 + cos^2 = 1)" は中央揃え、 "角度 (theta) が" はインライン
        if re.fullmatch(r'\(.*?\)[。、.,]?', line.strip()):
            # 独立行として美しく中央表示
            formula = re.search(r'\((.*?)\)', line).group(1)
            suffix = line.strip().replace(f"({formula})", "")
            st.latex(rf"\displaystyle {clean_math(formula)} \text{{{suffix}}}")
        else:
            # 文章中に数式が混在している場合 (インライン表示)
            # 全体をMarkdownとして構成し、数式部分を $...$ で囲う
            parts = re.split(r'(\(.*?\))', line)
            combined_md = ""
            for part in parts:
                if part.startswith('(') and part.endswith(')'):
                    formula = part[1:-1].strip()
                    combined_md += f" ${clean_math(formula)}$ "
                else:
                    # テキスト中のバックスラッシュは除去
                    combined_md += part.replace('\\', '').replace('displaystyle', '')
            
            st.markdown(combined_md)

@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    file_path = file_map.get(subject)
    if not file_path: return pd.DataFrame()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(current_dir, file_path)
    try:
        df = pd.read_csv(full_path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"データの読み込みに失敗しました ({file_path}): {e}")
        return pd.DataFrame()

# ==========================================
# 3. ヘッダー & サイドバー
# ==========================================
st.markdown(
    '<div class="header-container"><div class="main-title">理系には、勝ち方がある</div></div>',
    unsafe_allow_html=True
)

st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox(
    "科目を選択",
    ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"]
)

if sub == "選択してください":
    st.markdown("左のサイドバーから学習したい科目を選択してください。")
    st.stop()

# ==========================================
# 4. データ準備
# ==========================================
df_raw = load_data(sub)
if df_raw.empty:
    st.warning("データファイルが見つかりません。")
    st.stop()

if sub == "システム英単語":
    lv_map = {
        "すべて": "All", "Fundamental (1-600)": "Fundamental",
        "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced",
        "Final (1701-2027)": "Final"
    }
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter_val = lv_map[filter_label]
    filter_col = "level"
else:
    all_cats = []
    for c in df_raw["category"].astype(str):
        if c not in all_cats: all_cats.append(c)
    filter_label = st.sidebar.radio("分野・単元選択", ["すべて"] + all_cats)
    current_filter_val = filter_label
    filter_col = "category"

if (
    "current_sub" not in st.session_state
    or st.session_state.current_sub != sub
    or st.session_state.get("last_filter") != filter_label
):
    st.session_state.current_sub = sub
    st.session_state.last_filter = filter_label
    df_filtered = df_raw.copy() if filter_label == "すべて" else df_raw[df_raw[filter_col].astype(str).str.contains(current_filter_val, case=False, na=False)]
    
    if df_filtered.empty:
        st.session_state.df = pd.DataFrame()
    else:
        st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False
    if "choices" in st.session_state: del st.session_state["choices"]

if st.session_state.df.empty:
    st.error(f"該当データがありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 5. メイン画面
# ==========================================
if sub == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)

    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummy_pool = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        if len(dummy_pool) < 3: dummy_pool += ["(dummy)"] * (3 - len(dummy_pool))
        choices = random.sample([correct] + random.sample(dummy_pool, 3), 4)
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct

    cols = st.columns(2)
    for i, choice in enumerate(st.session_state.choices):
        with (cols[0] if i % 2 == 0 else cols[1]):
            if st.button(choice, key=f"btn_{i}", disabled=st.session_state.answered):
                st.session_state.selected, st.session_state.answered = choice, True
                st.rerun()

    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("Correct!")
        else: st.error(f"Incorrect... 正解：{st.session_state.correct}")
        st.write(f"**意味:** {row['all_answers']}")
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            del st.session_state["choices"]
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
            render_explanation(row["explanation"])

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()