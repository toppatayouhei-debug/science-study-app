import streamlit as st
import pandas as pd
import random
import re

# ==========================================
# 1. デザイン設定
# ==========================================
st.set_page_config(page_title="理系学習アプリ", page_icon="🧬")

st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }
.card { 
    background-color: white !important; 
    padding: 15px 20px !important; 
    border-radius: 12px !important; 
    box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important; 
    margin-bottom: 10px !important;
    color: #111111 !important;
}
.highlight { color: #ff9800 !important; font-weight: bold !important; }
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
.explanation-box {
    background-color: #fff9db !important;
    padding: 15px !important;
    border-radius: 10px !important;
    border: 1px solid #fab005 !important;
    margin-top: 10px !important;
    color: #444 !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 補助関数 (数式判定を大幅強化)
# ==========================================
def format_math_text(text):
    """x\sinx のようなスペースなしの数式も検知して $ で囲む"""
    if pd.isna(text): return ""
    text = str(text).strip()
    
    # 全角・ゴミの除去
    text = text.replace("−", "-").replace("　", " ").replace("‘", "").replace("’", "")
    
    # すでに $ で囲まれている場合はそのまま
    if text.startswith("$") and text.endswith("$"):
        return text
    
    clean_text = text.replace("$", "").strip()
    
    # 判定基準：バックスラッシュがある、または sin, cos, tan, log 等のキーワードが含まれる
    # または + や - や / が含まれる「式っぽい」もの
    keywords = ["\\", "^", "_", "{", "}", "/", "sin", "cos", "tan", "log", "int", "theta", "pi", "exp"]
    is_math = any(k in clean_text.lower() for k in keywords) or any(c in clean_text for c in ["+", "=", "(", ")"])
    
    if is_math:
        # \sin のあとにスペースがない場合に備え、表示用に調整して $ で囲む
        return f"${clean_text}$"
    return clean_text

def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "数Ⅲ積分 定石": "math3_integration.csv"
    }
    try:
        df = pd.read_csv(file_map[subject], encoding="utf-8-sig").dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# ==========================================
# 3. メイン処理
# ==========================================
st.sidebar.title("🧬 学習メニュー")
sub = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "数Ⅲ積分 定石"])

if sub == "選択してください":
    st.info("← サイドバーから科目を選択してください。")
    st.stop()

df_raw = load_data(sub)
if df_raw.empty:
    st.warning(f"{sub} のCSVファイルが見つかりません。")
    st.stop()

# --- フィルター ---
selected_filter = "すべて"
if sub == "システム英単語":
    lv_map = {"すべて":"All", "Fundamental (1-600)":"Fundamental", "Essential (601-1200)":"Essential", "Advanced (1201-1700)":"Advanced", "Final (1701-2027)":"Final"}
    selected_filter = st.sidebar.radio("レベルを選択", list(lv_map.keys()))
    filter_keyword = lv_map[selected_filter]
    filter_col = "level"
else:
    if "category" in df_raw.columns:
        cats = ["すべて"] + sorted(df_raw["category"].unique().tolist())
    else:
        df_raw["category"] = "未分類"
        cats = ["すべて", "未分類"]
    selected_filter = st.sidebar.radio("分野を選択", cats)
    filter_keyword = selected_filter
    filter_col = "category"

# --- セッション初期化 ---
if ("current_sub" not in st.session_state or st.session_state.current_sub != sub or 
    st.session_state.get("last_filter") != selected_filter):
    
    st.session_state.current_sub = sub
    st.session_state.last_filter = selected_filter
    
    df_f = df_raw.copy()
    if selected_filter != "すべて":
        df_f = df_raw[df_raw[filter_col].astype(str).str.contains(filter_keyword, case=False, na=False)]
    
    st.session_state.df = df_f.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False

if st.session_state.df.empty:
    st.warning("該当する問題がありません。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 4. 表示
# ==========================================

if sub == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)
    
    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        st.session_state.choices = random.sample([correct] + random.sample(dummies, min(3, len(dummies))), 4)
        st.session_state.correct = correct
    
    c1, c2 = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        with (c1 if i % 2 == 0 else c2):
            if st.button(val, key=f"t_{st.session_state.idx}_{i}", disabled=st.session_state.answered):
                st.session_state.selected, st.session_state.answered = val, True
                st.rerun()
    
    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"正解：{st.session_state.correct}")
        st.write(f"意味：{row['all_answers']}")
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown(f'<div class="explanation-box"><b>解説:</b><br>{format_math_text(row["explanation"])}</div>', unsafe_allow_html=True)
        if st.button("次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()

elif sub == "数Ⅲ積分 定石":
    st.markdown(f'<div class="card blue-card">【{row["category"]}】次の不定積分を求めよ：</div>', unsafe_allow_html=True)
    # 問題文は常に latex モード
    st.latex(r"\int " + str(row["question"]) + r" \, dx")
    
    if not st.session_state.answered:
        if st.button("解答を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.write("**💡 定石：**")
        st.markdown(format_math_text(row['strategy']))
        
        st.write("**【解答】**")
        ans_raw = str(row["answer"])
        # 日本語を含むかどうかで出し方を変える
        if re.search(r'[ぁ-んァ-ヶ亜-熙]', ans_raw):
            st.markdown(format_math_text(ans_raw))
        else:
            # 数式のみの場合は latex モード（ゴミ掃除付き）
            st.latex(ans_raw.replace("$", "").strip())
        
        if "explanation" in row and pd.notna(row["explanation"]):
            st.write("---")
            st.markdown(f"**📝 詳しい解説:**")
            st.markdown(format_math_text(row["explanation"]))
        
        if st.button("次の問題へ"):
            st.session_state.idx += 1
            st.session_state.answered = False
            st.rerun()