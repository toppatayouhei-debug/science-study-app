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
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 数式エンジン：究極版
# ==========================================
def master_latex_cleaner(text, is_block=False):
    """
    あらゆる数式生データをLaTeXに変換。
    特に肩（指数）の問題を完全に解決する。
    """
    if not text: return ""
    t = str(text)
    
    # ゴミ取り
    t = t.replace(r'\displaystyle', '').replace(r'\\', '\\').replace('$', '')
    t = t.replace(r'\(', '').replace(r'\)', '').replace(r'\[', '').replace(r'\]', '')

    # 1. 指数 (x^2) の解決: ^ の直後の数字や文字だけを {} で囲む。
    # すべて乗ってしまう問題を防ぐため、1文字（またはカタマリ）に限定。
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', lambda m: f"^{{{m.group(1).strip()}}}", t)
    
    # 2. 組合せ (nCr) の解決
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 3. 度数記号 (60^circ)
    t = t.replace('^circ', r'^{\circ}')

    # 4. 関数にバックスラッシュを付与
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'sqrt', 'circ']
    for f in funcs:
        t = re.sub(rf'(?<!\\)\b{f}\b', rf'\\{f}', t)

    # 5. 分数 (独立行のみ)
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)
    
    return t.strip()

def super_renderer(text):
    """
    地の文にバックスラッシュを出さず、
    数式と思われる箇所を強制的に $ $ で囲む。
    """
    if not text or pd.isna(text): return ""
    
    # 改行とアイコンの正規化
    t = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # 正規表現: ( ) で囲まれた部分、または特定の数学キーワードを含む単語を抽出
    # カッコがあれば中身を、なければ数式らしき単語を $ $ 化
    def math_logic(match):
        content = match.group(0)
        if content.startswith('(') and content.endswith(')'):
            content = content[1:-1]
        return f"${master_latex_cleaner(content)}$"

    # カッコで囲まれた部分を優先して $ $ 化
    t = re.sub(r'\(.*?\)', math_logic, t)
    
    # まだ残っている「単独の変数（y座標のyなど）」や「数式単語」を $ $ 化
    # y座標 -> $y$座標, x^2 -> $x^{2}$
    t = re.sub(r'\b([xytheta]|[a-z]\^[0-9a-z]|sin|cos|tan)\b', math_logic, t)

    # 地の文に残ったバックスラッシュを除去
    segments = t.split('$')
    final = []
    for i, s in enumerate(segments):
        if i % 2 == 0:
            final.append(s.replace('\\', ''))
        else:
            final.append(f"${s}$")
            
    return "".join(final)

# ==========================================
# 3. アプリロジック (変更なし)
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

st.markdown('<div class="header-container"><div class="main-title">理系には、勝ち方がある</div></div>', unsafe_allow_html=True)
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if sub == "選択してください":
    st.markdown("左のサイドバーから学習したい科目を選択してください。")
    st.stop()

df_raw = load_data(sub)
if df_raw.empty: st.stop()

if sub == "システム英単語":
    # 英語フィルタリング
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    df_f = df_raw if filter_label == "すべて" else df_raw[df_raw["level"] == lv_map[filter_label]]
else:
    # 数学フィルタリング
    all_cats = list(df_raw["category"].unique())
    filter_label = st.sidebar.radio("分野選択", ["すべて"] + all_cats)
    df_f = df_raw if filter_label == "すべて" else df_raw[df_raw["category"] == filter_label]

if "current_sub" not in st.session_state or st.session_state.current_sub != sub or st.session_state.get("last_filter") != filter_label:
    st.session_state.current_sub, st.session_state.last_filter = sub, filter_label
    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True) if not df_f.empty else pd.DataFrame()
    st.session_state.idx, st.session_state.answered = 0, False

if st.session_state.df.empty: st.stop()
row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. 表示部
# ==========================================
if sub == "システム英単語":
    # (省略)
    st.write("英語モード")
else:
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    # 問題文
    st.latex(rf"\displaystyle {master_latex_cleaner(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.markdown("##### 💡 攻略の定石")
        st.info(super_renderer(row["strategy"]))
        
        st.markdown("##### 【解答】")
        st.latex(rf"\displaystyle {master_latex_cleaner(row['answer'], is_block=True)}")

        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown("##### 📝 ポイント解説")
            st.markdown(super_renderer(row["explanation"]))

        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
