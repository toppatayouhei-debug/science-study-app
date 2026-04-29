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
# 2. 数式エンジンの再定義 (最重要)
# ==========================================
def latex_engine(text, is_block=False):
    """生データを純粋なLaTeXコマンドに変換する"""
    if not text: return ""
    t = str(text)
    
    # 物理的なゴミ・不要なエスケープの除去
    t = t.replace(r'\displaystyle', '').replace(r'\\', '\\')
    t = t.replace(r'\(', '').replace(r'\)', '').replace(r'\[', '').replace(r'\]', '').replace('$', '')
    
    # 1. 組合せ記法の変換 ( _{n}C_{r} -> {}_{n}C_{r} )
    t = re.sub(r'_?\{?([nN\d]+)\}?C_?\{?([rR\d]+)\}?', r'{}_{\1}C_{\2}', t)
    
    # 2. 累乗の正規化 ( ^2 -> ^{2} )
    t = re.sub(r'\^([0-9a-zA-Z\(\)\{\}\-\+]+)', r'^{\1}', t)
    
    # 3. 関数にバックスラッシュを付与 (重複防止)
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'sqrt', 'circ']
    for f in funcs:
        t = re.sub(rf'(?<!\\)\b{f}\b', rf'\\{f}', t)
    
    # 4. ブロック表示時のみ分数を \frac 化
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)
    
    return t.strip()

def render_content(text):
    """
    文章中の (数式) を確実に $数式$ に変換し、
    地文のバックスラッシュを徹底的に排除する。
    """
    if not text or pd.isna(text): return ""
    
    # 全体の前処理
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # ( ... ) で囲まれた部分を LaTeX 用に置換
    def process_match(m):
        inner = m.group(1).strip()
        # カッコ内は latex_engine を通して $ で囲む
        return f"${latex_engine(inner, is_block=False)}$"

    # 文章全体に対して数式抽出・変換を適用
    processed = re.sub(r'\((.*?)\)', process_match, raw)
    
    # 地文（$記号の外側）に残ったバックスラッシュを消去
    segments = processed.split('$')
    final_parts = []
    for i, seg in enumerate(segments):
        if i % 2 == 0: # テキスト部分
            # 地文のバックスラッシュや中途半端なコマンドを消去
            clean_seg = seg.replace('\\', '').replace('displaystyle', '')
            final_parts.append(clean_seg)
        else: # 数式部分
            final_parts.append(f"${seg}$")
            
    return "".join(final_parts)

@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    file_path = file_map.get(subject)
    if not file_path: return pd.DataFrame()
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        df = pd.read_csv(os.path.join(current_dir, file_path), encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except:
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

# フィルタリング
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
# 4. レンダリング実行
# ==========================================
if sub == "システム英単語":
    # 英語モード (仕様維持)
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
            st.session_state.idx += 1; st.session_state.answered = False; del st.session_state["choices"]; st.rerun()
else:
    # 数学モード
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    # 問題・解答は st.latex (独立ブロック)
    st.latex(rf"\displaystyle {latex_engine(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.markdown("##### 💡 攻略の定石")
        # 定石・解説はハイブリッドレンダリング
        st.info(render_content(row["strategy"]))
        
        st.markdown("##### 【解答】")
        st.latex(rf"\displaystyle {latex_engine(row['answer'], is_block=True)}")

        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown("##### 📝 ポイント解説")
            st.markdown(render_content(row["explanation"]))

        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
