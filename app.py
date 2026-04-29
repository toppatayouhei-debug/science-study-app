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
# 2. 究極安定・単一行レンダリングエンジン
# ==========================================
def total_math_cleaner(text):
    """数式パーツ（カッコの中身）をLaTeX命令へ安全に変換"""
    if not text: return ""
    # 不要な記号を物理削除
    t = str(text).replace('\\', '').replace('displaystyle', '').replace('$', '')
    
    # 記号置換（replaceだけで安全に）
    t = t.replace('theta', r'\theta ').replace('pi', r'\pi ')
    t = t.replace('sin', r'\sin ').replace('cos', r'\cos ').replace('tan', r'\tan ')
    t = t.replace('int', r'\int ').replace('vec', r'\vec ').replace('sqrt', r'\sqrt ')
    t = t.replace('times', r'\times ').replace('dots', r'\dots ').replace('infty', r'\infty ')
    t = t.replace('circ', r'^{\circ}').replace('dx', r'\,dx').replace('dt', r'\,dt')
    
    # 指数（肩）
    t = re.sub(r'\^([0-9a-zA-Z]+)', r'^{ \1 }', t)
    
    # ASCII以外のノイズ（？）を徹底除去
    t = "".join(char for char in t if 32 <= ord(char) <= 126 or char in '^{}_\\')
    return t.strip()

def unified_render(text, is_main=False):
    """日本語と数式を分離せず、一つの文字列としてStreamlitに渡す"""
    if not text or pd.isna(text): return ""
    
    raw = str(text).replace('\u3000', ' ').replace('\xa0', ' ').replace('\\n', '\n').strip()
    
    # カッコ ( ) で分割して中身だけを LaTeX 化
    def replace_with_math(match):
        inner = match.group(1).strip()
        cleaned = total_math_cleaner(inner)
        # メインの問題/解答なら少し大きく表示（displaystyle）
        style = r"\displaystyle " if is_main else ""
        return f"$ {style}{cleaned} $"

    # ( ) の中身を数式に置換
    processed_text = re.sub(r'\((.*?)\)', replace_with_math, raw)
    
    # 文中の独立した数字も数式フォントに（オプション）
    processed_text = re.sub(r'(?<![0-9$])\b(\d+)\b(?![0-9$])', r'$ \1 $', processed_text)
    
    # 先頭にバックスラッシュが残る問題を物理的に防ぐ
    if processed_text.startswith('\\'):
        processed_parts = processed_text.split('\\', 1)
        processed_text = processed_parts[1] if len(processed_parts) > 1 else processed_parts[0]

    return processed_text

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
    st.info("サイドバーから開始してください。")
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
    
    # 問題：markdown で一行として表示
    st.markdown(f"#### {unified_render(row['question'], is_main=True)}")

    if not st.session_state.answered:
        if st.button("解法・定石を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        st.info(f"💡 **攻略の定石**\n\n{unified_render(row['strategy'])}")
        
        st.markdown("##### 【解答】")
        st.markdown(unified_render(row['answer'], is_main=True))
        
        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{unified_render(row['explanation'])}")
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
