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
# 2. 徹底書き換え：数学シンボル・ハンター
# ==========================================
def total_math_cleaner(text, is_block=False):
    if not text or pd.isna(text): return ""
    t = str(text).replace('\\', '').replace('displaystyle', '').replace('$', '')

    # --- 強制変換フェーズ（単語の境界を無視して一掃） ---
    # 1. ベクトル (vecOA -> \vec{OA})
    t = re.sub(r'vec\s*([a-zA-Z]{1,2})', r'\\vec{\1}', t)
    
    # 2. 平方根 (sqrt3 -> \sqrt{3}, sqrt(3) -> \sqrt{3})
    t = re.sub(r'sqrt\s*\(?(.*?)\)?(?=[^0-9a-zA-Z()]|$)', r'\\sqrt{\1}', t)
    # カッコなしの単純なケースもカバー
    t = re.sub(r'sqrt\s*([0-9a-zA-Z]+)', r'\\sqrt{\1}', t)
    
    # 3. 掛け算・点・三点リーダー
    t = t.replace('times', r' \times ')
    t = t.replace('cdot', r' \cdot ')
    t = t.replace('dots', r' \dots ')
    t = t.replace('circ', r'^{\circ}')
    
    # --- 構造整理フェーズ ---
    # 4. 指数 (肩)
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', lambda m: f"^{{{m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()}}}{m.group(1)[len(m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()):]}", t)

    # 5. 組合せ (nCr)
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 6. 分数
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 7. 数学関数・ギリシャ文字（これらは単語単位で置換）
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'alpha', 'beta', 'gamma']
    for f in funcs:
        t = re.sub(rf'(?<!\\)\b{f}\b', rf'\\{f}', t)
    
    # 8. 虚数単位・変数 i
    t = re.sub(r'(\d+|\b)i\b', r'\1 i ', t)

    return t.strip()

def elegant_render(text):
    if not text or pd.isna(text): return ""
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # 数字を数式フォントにする
    def digit_replacer(match):
        return f" ${match.group(0)}$ "
    
    # カッコ分割パース
    parts = re.split(r'(\(.*?\))', raw)
    final_output = []
    
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            inner = p[1:-1].strip()
            final_output.append(f" ${total_math_cleaner(inner)}$ ")
        else:
            # 地文：キーワードを記号に置換
            cp = p.replace('\\', '').replace('vec', '→').replace('times', '×').replace('sqrt', '√').replace('dots', '…').replace('circ', '°')
            # 数字の数式化
            cp = re.sub(r'\b\d+(\.\d+)?\b', digit_replacer, cp)
            final_output.append(cp)
            
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
    st.info("サイドバーから科目を選択してください。")
    st.stop()

df_raw = load_data(subject)

# 分野選択
choice = st.sidebar.radio("分野・レベル選択", ["すべて"] + list(df_raw["category"].unique() if "category" in df_raw.columns else df_raw["level"].unique()))
df_filtered = df_raw if choice == "すべて" else df_raw[(df_raw.get("category") == choice) | (df_raw.get("level") == choice)]

# セッション管理
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
    # 英語モード
    st.markdown(f"### {row['sentence'].replace(row['question'], f'**{row[u'question']}**')}")
    if not st.session_state.answered:
        if st.button("答えを見る"):
            st.session_state.answered = True; st.rerun()
    else:
        st.success(f"正解: {row['all_answers']}")
        if st.button("次へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
