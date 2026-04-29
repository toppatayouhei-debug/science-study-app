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
# 2. 徹底安全・置換エンジン (安定性重視)
# ==========================================
def total_math_cleaner(text, is_block=False):
    if not text or pd.isna(text): return ""
    # 一旦バックスラッシュを消去し、綺麗な状態から再構築
    t = str(text).replace('\\', '').replace('displaystyle', '').replace('$', '')

    # --- A. 単純置換（エラーが起きない最も安全な方法） ---
    t = t.replace('int', r'\int')
    t = t.replace('vec', r'\vec')
    t = t.replace('sqrt', r'\sqrt')
    t = t.replace('times', r'\times')
    t = t.replace('cdot', r'\cdot')
    t = t.replace('dots', r'\dots')
    t = t.replace('circ', r'^{\circ}')
    t = t.replace('infty', r'\infty')

    # --- B. 構造修正（正規表現は最小限に） ---
    # 指数（肩）を {} で保護
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', r'^{\1}', t)
    
    # 組合せ
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 分数（問題・解答用）
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # --- C. 数学関数（バックスラッシュ付与） ---
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'alpha', 'beta', 'gamma', 'dx', 'dt']
    for f in funcs:
        # 重複付与を防ぎつつバックスラッシュを付ける
        t = re.sub(rf'(?<!\\)\b{f}\b', rf'\\{f}', t)
    
    # 虚数単位 i (文末や数字の後の i を数式化)
    t = re.sub(r'(\d+|\b)i\b', r'\1 i ', t)

    return t.strip()

def elegant_render(text):
    """地の文の数字や記号を整える"""
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # カッコ分割
    parts = re.split(r'(\(.*?\))', raw)
    final_output = []
    
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            inner = p[1:-1].strip()
            final_output.append(f" ${total_math_cleaner(inner)}$ ")
        else:
            # 地文の記号置換
            cp = p.replace('\\', '')
            replace_map = {
                'int': '∫', 'vec': '→', 'sqrt': '√', 
                'times': '×', 'dots': '…', 'circ': '°', 'infty': '∞'
            }
            for k, v in replace_map.items():
                cp = cp.replace(k, v)
            
            # 数字の数式フォント化
            cp = re.sub(r'\b\d+(\.\d+)?\b', r' $\0$ ', cp)
            final_output.append(cp)
            
    return "".join(final_output)

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

st.title("理系には、勝ち方がある")
subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"])

if subject == "選択してください":
    st.info("サイドバーから科目を選択してください。")
    st.stop()

df_raw = load_data(subject)
cats = ["すべて"] + list(df_raw["category"].unique() if "category" in df_raw.columns else df_raw["level"].unique())
choice = st.sidebar.radio("分野・レベル選択", cats)
df_filtered = df_raw if choice == "すべて" else df_raw[(df_raw.get("category") == choice) | (df_raw.get("level") == choice)]

current_key = f"{subject}_{choice}"
if "session_key" not in st.session_state or st.session_state.session_key != current_key:
    st.session_state.session_key = current_key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty: st.stop()
row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. 表示
# ==========================================
if subject != "システム英単語":
    st.markdown(f'<div class="card blue-card">【{row.get("category", "問題")}】</div>', unsafe_allow_html=True)
    st.latex(rf"\displaystyle {total_math_cleaner(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("解法・定石を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.info(f"💡 **攻略の定石**\n\n{elegant_render(row['strategy'])}")
        st.latex(rf"\displaystyle {total_math_cleaner(row['answer'], is_block=True)}")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{elegant_render(row['explanation'])}")
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
else:
    # 英単語簡易表示
    st.write(f"### {row['sentence']}")
    if st.button("正解を表示"): st.success(row['all_answers'])
    if st.button("次へ"): st.session_state.idx += 1; st.rerun()
