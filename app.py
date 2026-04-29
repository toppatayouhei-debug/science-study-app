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
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 徹底書き換えエンジン
# ==========================================
def total_math_cleaner(text, is_block=False):
    """
    あらゆる数式生データをLaTeXに変換。
    カッコの有無を問わず、キーワードを見つけ次第変換する。
    """
    if not text or pd.isna(text): return ""
    t = str(text).replace('\\', '').replace('displaystyle', '')

    # 1. 平方根 (sqrt3 や sqrt(3) を \sqrt{3} に)
    # 順序が大事：まずはカッコありを処理
    t = re.sub(r'sqrt\s*\((.*?)\)', r'\\sqrt{\1}', t)
    # 次にカッコなし単語を処理
    t = re.sub(r'sqrt\s*([0-9a-zA-Z]+)', r'\\sqrt{\1}', t)
    
    # 2. 指数 (肩) のガード: x^2 -> x^{2}
    # 後ろに続く式を巻き込まないよう、直後のカタマリだけを {} に入れる
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', lambda m: f"^{{{m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()}}}{m.group(1)[len(m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()):]}", t)

    # 3. 組合せ、度数
    t = t.replace('circ', r'^{\circ}')
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 4. 分数 (独立ブロックのみ)
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 5. 数学関数へのバックスラッシュ付与
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'alpha', 'beta', 'i']
    for f in funcs:
        t = re.sub(rf'\b{f}\b', rf'\\{f}', t)
    
    return t.strip()

def elegant_render(text):
    """
    文章中の ( ) を探し出し、その中身を LaTeX 化する。
    また、( ) の外側にある sqrt も文字化けしないように √ に置換する。
    """
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # 文章をカッコで分割
    parts = re.split(r'(\(.*?\))', raw)
    final_output = []
    
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            # 数式パート
            inner = p[1:-1].strip()
            final_output.append(f"${total_math_cleaner(inner)}$")
        else:
            # 地文パート：バックスラッシュを消しつつ、sqrt を √ に、circ を ° に置換
            clean_p = p.replace('\\', '').replace('sqrt', '√').replace('circ', '°')
            final_output.append(clean_p)
            
    return "".join(final_output)

# ==========================================
# 3. アプリケーションロジック (サイドバー連動版)
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
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if subject == "選択してください":
    st.info("サイドバーから科目と分野を選んでください。")
    st.stop()

df_raw = load_data(subject)

# 分野選択
if subject == "システム英単語":
    choice = st.sidebar.radio("レベル", ["すべて"] + list(df_raw["level"].unique()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["level"] == choice]
else:
    choice = st.sidebar.radio("分野", ["すべて"] + list(df_raw["category"].unique()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["category"] == choice]

# 状態の管理（サイドバーで切り替えたらリセット）
current_key = f"{subject}_{choice}"
if "session_key" not in st.session_state or st.session_state.session_key != current_key:
    st.session_state.session_key = current_key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. 表示
# ==========================================
if subject != "システム英単語":
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    # 問題文 (st.latex を使用)
    st.latex(rf"\displaystyle {total_math_cleaner(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.info(f"💡 **攻略の定石**\n\n{elegant_render(row['strategy'])}")
        
        st.markdown("##### 【解答】")
        st.latex(rf"\displaystyle {total_math_cleaner(row['answer'], is_block=True)}")

        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{elegant_render(row['explanation'])}")

        if st.button("次へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
