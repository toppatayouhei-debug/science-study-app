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
# 2. 強化版数式処理エンジン
# ==========================================
def fix_math_format(text, is_block=False):
    if not text or pd.isna(text): return ""
    t = str(text).replace('\\', '').replace('displaystyle', '')
    
    # 1. 平方根 (sqrt3 -> \sqrt{3}, sqrt(3) -> \sqrt{3}) の徹底変換
    # カッコがない sqrt3 などのケースを先に処理
    t = re.sub(r'sqrt\s*\(?([0-9a-zA-Z]+)\)?', r'\\sqrt{\1}', t)
    
    # 2. 指数（肩）の修正: x^2+x -> x^{2}+x
    t = re.sub(r'\^([0-9a-zA-Z\+ \-]+)', lambda m: f"^{{{m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()}}}{m.group(1)[len(m.group(1).split('+')[0].split('-')[0].split('=')[0].strip()):]}", t)
    
    # 3. 組合せ・度数
    t = t.replace('circ', r'^{\circ}')
    t = re.sub(r'([nN\d]+)?C([rR\d]+)', r'{}_{\1}C_{\2}', t)

    # 4. 分数の変換 (ブロック表示なら \frac, インラインならそのまま)
    if is_block:
        t = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', t)

    # 5. 数学関数・変数へのバックスラッシュ付与
    # i(虚数単位) や theta もここで保護
    funcs = ['sin', 'cos', 'tan', 'log', 'ln', 'exp', 'theta', 'pi', 'alpha', 'beta']
    for f in funcs:
        t = re.sub(rf'\b{f}\b', rf'\\{f}', t)
    
    # 変数としての i (虚数単位) が単独で存在する場合に数式フォント化
    t = re.sub(r'\b(i)\b', r'\mathit{\1}', t)

    return t.strip()

def render_mixed(text):
    if not text or pd.isna(text): return ""
    # 改行と絵文字の整理
    raw = str(text).replace('\\n', '\n').replace('📝', '').strip()
    
    # ( ... ) で囲まれた部分を数式として抽出
    parts = re.split(r'(\(.*?\))', raw)
    res = ""
    for p in parts:
        if p.startswith('(') and p.endswith(')'):
            # 数式パート
            res += f" ${fix_math_format(p[1:-1])}$ "
        else:
            # 地文パート (バックスラッシュを除去してプレーンに)
            clean_p = p.replace('\\', '').replace('circ', '°').replace('sqrt', '√')
            res += clean_p
    return res

# ==========================================
# 3. データ読み込み & サイドバー制御
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
    st.info("左のサイドバーから科目と分野を選択してスタートしてください。")
    st.stop()

df_raw = load_data(subject)

# 分野フィルタリング
if subject == "システム英単語":
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    choice = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["level"] == lv_map[choice]]
else:
    cats = ["すべて"] + list(df_raw["category"].unique())
    choice = st.sidebar.radio("分野選択", cats)
    df_filtered = df_raw if choice == "すべて" else df_raw[df_raw["category"] == choice]

# 状態のリセット（サイドバー連動）
filter_key = f"{subject}_{choice}"
if "filter_key" not in st.session_state or st.session_state.filter_key != filter_key:
    st.session_state.filter_key = filter_key
    st.session_state.df = df_filtered.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty:
    st.warning("該当するデータがありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. メイン表示
# ==========================================
if subject != "システム英単語":
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    
    # 問題文
    st.latex(rf"\displaystyle {fix_math_format(row['question'], is_block=True)}")

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown("---")
        # 攻略の定石
        st.info(f"💡 **攻略の定石**\n\n{render_mixed(row['strategy'])}")
        
        # 解答 (分数を \frac 化)
        st.markdown("##### 【解答】")
        st.latex(rf"\displaystyle {fix_math_format(row['answer'], is_block=True)}")
        
        # ポイント解説
        if "explanation" in row and pd.notna(row["explanation"]):
            st.success(f"📝 **ポイント解説**\n\n{render_mixed(row['explanation'])}")

        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
else:
    # 英語モード (シンプル表示)
    st.markdown(f'<div class="card orange-card">**{row["level"]}**</div>', unsafe_allow_html=True)
    q_word = str(row["question"])
    st.markdown(f"### {str(row['sentence']).replace(q_word, f' __({q_word})__ ')}")
    
    if not st.session_state.answered:
        if st.button("答えを見る"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.success(f"正解: {row['all_answers']}")
        if st.button("次の単語へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()
