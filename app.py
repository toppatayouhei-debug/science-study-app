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
/* 数式フォントの微調整 */
.katex { font-size: 1.05em !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 数式・テキスト処理エンジン（完全安定版）
# ==========================================
def fix_latex_syntax(text):
    """
    生データの数式構文を、LaTeXが誤読しない形式に物理的に修正する
    """
    if not text: return ""
    t = str(text)
    
    # 1. 全体からバックスラッシュを一度消去し、必要なものだけ再付与する
    # これにより "y\ 座標" のようなゴミを消去
    t = t.replace('\\', '').replace('displaystyle', '')

    # 2. 二次関数の「肩乗り」問題を解決
    # ^ の直後が「1文字」または「数字のみ」なら {} で囲む。
    # x^2+x+1 -> x^{2}+x+1
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', lambda m: f"^{{{m.group(1).split('+')[0].split('-')[0].strip()}}}{m.group(1)[len(m.group(1).split('+')[0].split('-')[0].strip()):]}", t)
    
    # 3. 度数記号・平方根・組合せの再構成
    t = t.replace('circ', r'^{\circ}')
    t = re.sub(r'sqrt\((.*?)\)', r'\\sqrt{\1}', t)
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 4. 数学関数の復活
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi']
    for f in funcs:
        t = re.sub(rf'\b{f}\b', rf'\\{f}', t)
    
    return t.strip()

def elegant_render(text):
    """
    文章中の ( ) を数式として扱い、それ以外を地文として出す。
    """
    if not text or pd.isna(text): return ""
    
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # ( ... ) で囲まれた部分を抽出
    parts = re.split(r'(\(.*?\))', raw)
    final_output = ""
    
    for part in parts:
        if part.startswith('(') and part.endswith(')'):
            # 数式パート
            inner = part[1:-1].strip()
            # 文中の分数は 3/2 のまま美しく見せる
            final_output += f" ${fix_latex_syntax(inner)}$ "
        else:
            # 地文パート（バックスラッシュを消去）
            final_output += part.replace('\\', '').replace('circ', '°')
            
    return final_output

# ==========================================
# 3. アプリケーション本体
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
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if sub == "選択してください":
    st.stop()

df_raw = load_data(sub)
if df_raw.empty: st.stop()

# フィルタリング
if sub == "システム英単語":
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    df_f = df_raw if filter_label == "すべて" else df_raw[df_raw["level"] == lv_map[filter_label]]
else:
    all_cats = list(df_raw["category"].unique())
    filter_label = st.sidebar.radio("分野選択", ["すべて"] + all_cats)
    df_f = df_raw if filter_label == "すべて" else df_raw[df_raw["category"] == filter_label]

if "idx" not in st.session_state or st.session_state.get("last_sub") != sub:
    st.session_state.idx = 0
    st.session_state.answered = False
    st.session_state.last_sub = sub
    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True)

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# 表示処理
if sub != "システム英単語":
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    # 問題文
    st.latex(rf"\displaystyle {fix_latex_syntax(row['question'])}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.info(f"💡 **攻略の定石**\n\n{elegant_render(row['strategy'])}")
        
        st.markdown("##### 【解答】")
        # 解答エリアの分数は大きく表示
        ans = fix_latex_syntax(row['answer'])
        ans = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', ans)
        st.latex(rf"\displaystyle {ans}")

        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{elegant_render(row['explanation'])}")

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
