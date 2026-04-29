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
# 2. ロジック関数 (再安定化版)
# ==========================================
def clean_math(text):
    """数式生データをLaTeX形式へ徹底変換"""
    if not text or pd.isna(text): return ""
    text = str(text)
    # LaTeXコマンドの重複・不要タグを除去
    text = text.replace(r'\displaystyle', '').replace(r'\\', '\\')
    text = text.replace(r'\(', '').replace(r'\)', '').replace(r'\[', '').replace(r'\]', '').replace('$', '')
    # 累乗: ^2 -> ^{2}
    text = re.sub(r'\^([0-9a-zA-Z\(\)\{\}\-]+)', r'^{\1}', text)
    # 基本関数
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'sqrt']
    for f in funcs:
        text = re.sub(rf'(?<!\\)\b{f}\b', rf'\\{f}', text)
    return text.strip()

def render_mixed_content(text, is_strategy=False):
    """
    文章と数式を判別してレンダリング。
    文章中の文字(i, y等)がバックスラッシュ付きで表示されるのを防ぐ。
    """
    if not text or pd.isna(text): return
    raw_text = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # 行ごとに処理
    lines = raw_text.split('\n')
    for line in lines:
        line = line.strip()
        if not line: continue
            
        # その行全体が1つの数式 ( ... ) の場合
        if re.fullmatch(r'\(.*?\)[。、.,]?', line):
            formula_match = re.search(r'\((.*?)\)', line)
            if formula_match:
                f_val = formula_match.group(1)
                suffix = line.replace(f"({f_val})", "").strip()
                # 独立行として大きく表示
                st.latex(rf"\displaystyle {clean_math(f_val)} \text{{{suffix}}}")
        else:
            # 文章中に数式 ( ... ) が混在している場合
            parts = re.split(r'(\(.*?\))', line)
            md_text = ""
            for part in parts:
                if part.startswith('(') and part.endswith(')'):
                    inner = part[1:-1].strip()
                    # インライン数式として結合
                    md_text += f" ${clean_math(inner)}$ "
                else:
                    # 地の文のバックスラッシュを物理除去
                    md_text += part.replace('\\', '').replace('displaystyle', '')
            
            # 定石エリア(st.info内)か解説エリアかで出し分け
            if is_strategy:
                # 定石の中では1つのブロックとして扱うため、ここではテキストのみを一旦返す
                return md_text
            else:
                st.markdown(md_text)

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
        return pd.DataFrame()

# ==========================================
# 3. アプリケーション本体
# ==========================================
st.markdown('<div class="header-container"><div class="main-title">理系には、勝ち方がある</div></div>', unsafe_allow_html=True)

sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if sub == "選択してください":
    st.markdown("左のサイドバーから学習したい科目を選択してください。")
    st.stop()

df_raw = load_data(sub)
if df_raw.empty: st.stop()

# フィルタリング (仕様通り)
if sub == "システム英単語":
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter_val, filter_col = lv_map[filter_label], "level"
else:
    all_cats = []
    for c in df_raw["category"].astype(str):
        if c not in all_cats: all_cats.append(c)
    filter_label = st.sidebar.radio("分野・単元選択", ["すべて"] + all_cats)
    current_filter_val, filter_col = filter_label, "category"

if "current_sub" not in st.session_state or st.session_state.current_sub != sub or st.session_state.get("last_filter") != filter_label:
    st.session_state.current_sub, st.session_state.last_filter = sub, filter_label
    df_f = df_raw.copy() if filter_label == "すべて" else df_raw[df_raw[filter_col].astype(str).str.contains(current_filter_val, case=False, na=False)]
    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True) if not df_f.empty else pd.DataFrame()
    st.session_state.idx, st.session_state.answered = 0, False
    if "choices" in st.session_state: del st.session_state["choices"]

if st.session_state.df.empty:
    st.error("データがありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. メイン画面
# ==========================================
if sub == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummy_pool = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
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
    # 【修正】問題文の式を latex で表示
    st.latex(rf"\displaystyle {clean_math(row['question'])}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.markdown("##### 💡 攻略の定石")
        # 定石部分も数式に対応
        st.info(render_mixed_content(row["strategy"], is_strategy=True) or row["strategy"])
        
        st.markdown("##### 【解答】")
        st.latex(rf"\displaystyle {clean_math(row['answer'])}")

        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown("##### 📝 ポイント解説")
            render_mixed_content(row["explanation"])

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
