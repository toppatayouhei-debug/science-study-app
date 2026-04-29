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
# 2. 数式処理エンジン：究極版
# ==========================================
def total_math_cleaner(text, is_block=False):
    if not text or pd.isna(text): return ""
    t = str(text).replace('\\', '').replace('displaystyle', '')

    # 1. 数列の三点リーダー (dots) を LaTeX 形式へ
    t = t.replace('dots', r'\dots')

    # 2. 平方根 (sqrt)
    t = re.sub(r'sqrt\s*\((.*?)\)', r'\\sqrt{\1}', t)
    t = re.sub(r'sqrt\s*([0-9a-zA-Z]+)', r'\\sqrt{\1}', t)
    
    # 3. 指数 (肩)
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', lambda m: f"^{{{m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()}}}{m.group(1)[len(m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()):]}", t)

    # 4. 組合せ・度数
    t = t.replace('circ', r'^{\circ}')
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 5. 分数
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 6. 数学関数
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'alpha', 'beta', 'gamma', 'i']
    for f in funcs:
        t = re.sub(rf'\b{f}\b', rf'\\{f}', t)
    
    return t.strip()

def elegant_render(text):
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # 文章中の数字（整数・小数・分数形式）をすべて数式フォント ($ $) に変換
    # 例: 123 -> $123$, 0.5 -> $0.5$
    def digit_replacer(match):
        return f" ${match.group(0)}$ "
    
    # まずカッコ内の数式を処理
    parts = re.split(r'(\(.*?\))', raw)
    final_output = []
    
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            inner = p[1:-1].strip()
            final_output.append(f" ${total_math_cleaner(inner)}$ ")
        else:
            # カッコの外側：
            # 1. 不要な文字の置換
            clean_p = p.replace('\\', '').replace('dots', '…').replace('circ', '°').replace('sqrt', '√')
            # 2. 数字をすべて数式フォント化
            clean_p = re.sub(r'\b\d+(\.\d+)?\b', digit_replacer, clean_p)
            final_output.append(clean_p)
            
    return "".join(final_output)

# ==========================================
# 3. アプリケーションロジック
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
    st.info("サイドバーから科目を選択して開始してください。")
    st.stop()

df_raw = load_data(subject)

if subject == "システム英単語":
    choice = st.sidebar.radio("レベル", ["すべて"] + list(df_raw["level"].unique()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["level"] == choice]
else:
    choice = st.sidebar.radio("分野", ["すべて"] + list(df_raw["category"].unique()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["category"] == choice]

current_key = f"{subject}_{choice}"
if "session_key" not in st.session_state or st.session_state.session_key != current_key:
    st.session_state.session_key = current_key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty: st.stop()
row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. メイン表示
# ==========================================
if subject != "システム英単語":
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    st.latex(rf"\displaystyle {total_math_cleaner(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("解法を確認する"):
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
