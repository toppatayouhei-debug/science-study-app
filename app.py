import streamlit as st
import pandas as pd
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
# 2. 徹底クリーンアップエンジン（最終・ theta & 「？」抹殺版）
# ==========================================
def total_math_cleaner(text, is_block=False):
    if not text or pd.isna(text): return ""
    
    t = str(text)
    # 1. 物理的なゴミ・特殊文字を極限まで抹消
    t = t.replace('\u3000', ' ').replace('\xa0', ' ').replace('\x00', ' ').replace('\ufeff', '')
    t = t.replace('\\ ', ' ').replace('\\', '').replace('displaystyle', '').replace('$', '')

    # 2. ギリシャ文字・数学関数の置換（ここを最優先に）
    # theta, pi 等を確実に \theta, \pi へ
    greek_and_funcs = {
        'theta': r'\theta', 'pi': r'\pi', 'alpha': r'\alpha', 'beta': r'\beta', 
        'gamma': r'\gamma', 'sin': r'\sin', 'cos': r'\cos', 'tan': r'\tan', 
        'log': r'\log', 'ln': r'\ln', 'exp': r'\exp'
    }
    for k, v in greek_and_funcs.items():
        # 単語の境界を意識しつつ置換
        t = re.sub(rf'\b{k}\b', v, t)

    # 3. 記号・演算子の変換
    t = t.replace('dx', r'\,dx').replace('dt', r'\,dt')
    t = t.replace('int', r'\int ')
    t = t.replace('vec', r'\vec ')
    t = t.replace('sqrt', r'\sqrt ')
    t = t.replace('times', r'\times ')
    t = t.replace('dots', r'\dots ')
    t = t.replace('infty', r'\infty ')
    t = t.replace('circ', r'^{\circ}')

    # 4. 構造修正 (指数・積分定数)
    t = re.sub(r'\^([0-9a-zA-Z]+)', r'^{\1}', t)
    t = t.replace('+C', ' + C').replace('-C', ' - C')

    # 5. 分数（ブロック表示用）
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 6. 虚数単位
    t = re.sub(r'(\d+|\b)i\b', r'\1 i ', t)

    # 7. 「？」の原因となる非アスキー文字を物理的に完全消去
    # LaTeXで許容される文字記号のみを通過させる（ASCII: 32-126）
    t = "".join(char for char in t if 32 <= ord(char) <= 126 or char in '^{}_\\')
    
    return t.strip()

def elegant_render(text):
    if not text or pd.isna(text): return ""
    # 特殊なゴミをここでも掃除
    raw = str(text).replace('\u3000', ' ').replace('\xa0', ' ').replace('\\n', '\n').replace('📝', '').strip()
    
    parts = re.split(r'(\(.*?\))', raw)
    final_output = []
    
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            inner = p[1:-1].strip()
            final_output.append(f" ${total_math_cleaner(inner)}$ ")
        else:
            # 地文：バックスラッシュを消し、主要記号を置換
            cp = p.replace('\\', '')
            replace_map = {
                'theta': 'θ', 'pi': 'π', 'int': '∫', 'vec': '→', 
                'sqrt': '√', 'times': '×', 'dots': '…', 'circ': '°'
            }
            for k, v in replace_map.items():
                cp = cp.replace(k, v)
            
            # 数字を数式フォント化
            cp = re.sub(r'\b\d+(\.\d+)?\b', r' $\0$ ', cp)
            final_output.append(cp)
            
    return "".join(final_output)

# ==========================================
# 3. アプリロジック
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
    # 問題文のレンダリング
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
