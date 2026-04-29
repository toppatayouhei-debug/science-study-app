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
# 2. 徹底クリーンアップエンジン（安全第一・置換版）
# ==========================================
def total_math_cleaner(text, is_block=False):
    if not text or pd.isna(text): return ""
    
    # 物理的なゴミ・特殊文字を削除
    t = str(text).replace('\u3000', ' ').replace('\xa0', ' ').replace('\x00', ' ')
    t = t.replace('\\', '').replace('displaystyle', '').replace('$', '')

    # --- A. 文字列置換（replace なら PatternError は起きない） ---
    # ギリシャ文字・数学関数
    t = t.replace('theta', r'\theta ')
    t = t.replace('pi', r'\pi ')
    t = t.replace('sin', r'\sin ')
    t = t.replace('cos', r'\cos ')
    t = t.replace('tan', r'\tan ')
    
    # 記号・演算子
    t = t.replace('dx', r'\,dx').replace('dt', r'\,dt')
    t = t.replace('int', r'\int ')
    t = t.replace('vec', r'\vec ')
    t = t.replace('sqrt', r'\sqrt ')
    t = t.replace('times', r'\times ')
    t = t.replace('dots', r'\dots ')
    t = t.replace('infty', r'\infty ')
    t = t.replace('circ', r'^{\circ}')

    # --- B. 構造の微調整（最小限の正規表現） ---
    # 指数（肩）
    t = re.sub(r'\^([0-9a-zA-Z]+)', r'^{\1}', t)
    # 積分定数周りの整形
    t = t.replace('+C', ' + C').replace('-C', ' - C')

    # 分数（独立表示時のみ）
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 虚数単位
    t = t.replace(' i ', r' i ').replace('i ', r' i ')

    # --- C. 「？」抹殺フィルタ ---
    # ASCII文字と基本構造記号のみを許可
    t = "".join(char for char in t if 32 <= ord(char) <= 126 or char in '^{}_\\')
    
    return t.strip()

def elegant_render(text):
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\u3000', ' ').replace('\xa0', ' ').replace('\\n', '\n').replace('📝', '').strip()
    
    parts = re.split(r'(\(.*?\))', raw)
    final_output = []
    
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            inner = p[1:-1].strip()
            final_output.append(f" ${total_math_cleaner(inner)}$ ")
        else:
            # 地文：バックスラッシュを消し、記号を日本語フォントに
            cp = p.replace('\\', '')
            rep_map = {'theta': 'θ', 'pi': 'π', 'int': '∫', 'vec': '→', 'sqrt': '√', 'times': '×', 'circ': '°'}
            for k, v in rep_map.items():
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
    st.info("左のメニューから開始してください。")
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
