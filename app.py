import streamlit as st
import pandas as pd
import random
import re
import os
import urllib.parse
import base64
import requests

# ==========================================
# 1. ページ設定
# ==========================================
st.set_page_config(
    page_title="「理系」スターターパック",
    page_icon="🧬",
    layout="centered"
)

# ==========================================
# 2. デザイン (CSS)
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }
.header-container { text-align: center; margin-bottom: 25px; }
.main-title { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; }
.description-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 25px; line-height: 1.6; }
.card { background-color: white !important; padding: 20px !important; border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important; margin-bottom: 18px; }
.orange-card { border-left: 8px solid #ff9800 !important; }
.green-card { border-left: 8px solid #4caf50 !important; }
.highlight { color: #ff9800 !important; font-weight: bold !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
.audio-container { background-color: #f8f9fa; border-radius: 10px; padding: 10px; display: flex; align-items: center; border: 1px solid #ddd; margin-top: 10px; }
/* 化学の問題文用フォントサイズ調整 */
.chem-question { font-size: 1.1rem !important; font-weight: 700; color: #1f2937; line-height: 1.5; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ユーティリティ関数
# ==========================================
def clean_math(text):
    if pd.isna(text): return ""
    t = str(text).strip()
    if not t.startswith("$"):
        t = re.sub(r'([A-Z][a-z]?)(\d+)', r'\1_{\2}', t)
        t = re.sub(r'\^(\d+[\+\-])', r'^{\1}', t)
    t = t.replace("$", "").replace(r"\(", "").replace(r"\)", "").replace(r"\[", "").replace(r"\]", "")
    return t

def render_inline_math(text):
    if pd.isna(text): return ""
    s = str(text)
    pattern = r'([A-Za-z0-9\\+\-*/=^{}()]+(?:\s*[=+\-*/]\s*[A-Za-z0-9\\+\-*/=^{}()]+)+|[A-Z][a-z]?\d+|[A-Z][a-z]?\^{\d+[\+\-]})'
    def repl(m): return f"${clean_math(m.group(1))}$$
    return re.sub(pattern, repl, s)

def play_voice(text, label="音声を聴く"):
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q}&tl=en&client=tw-ob"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            b64 = base64.b64encode(res.content).decode()
            md = f'<div class="audio-container"><span style="color:#ff9800; font-weight:bold; margin-right:auto;">🎧 {label}</span><audio src="data:audio/mp3;base64,{b64}" controls style="height: 30px;"></audio></div>'
            st.markdown(md, unsafe_allow_html=True)
    except: pass

# ==========================================
# 4. データ読み込み
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "暗唱例文集": "english_sent.csv",
        "化学（一問一答）": "chemistry.csv"
    }
    file_name = file_map.get(subject)
    if not file_name: return pd.DataFrame()
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, file_name)
        df = pd.read_csv(path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# ==========================================
# 5. メインロジック
# ==========================================
st.markdown('<div class="header-container"><div class="main-title">🧪 🔢 🧬 「理系」スターターパック</div></div>', unsafe_allow_html=True)
st.sidebar.title("🧬 学習メニュー")

subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "暗唱例文集", "化学（一問一答）"])

# --- 【復元】科目選択時の注意事項 ---
if subject == "選択してください":
    st.markdown("""
    <div class="description-box">
    <b>【学習の進め方】</b><br>
    1. 左のサイドバーから<b>科目</b>を選択してください。<br>
    2. レベルや章を選択すると、問題がランダムに出題されます。<br>
    3. 自分のペースで暗唱や演習を繰り返しましょう。
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df_raw = load_data(subject)
if df_raw.empty:
    st.sidebar.error(f"⚠️ {subject} のファイルが見つかりません。")
    st.stop()

# --- フィルタ設定 ---
filter_label = "すべて"
filter_col = None

if subject == "システム英単語":
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter, filter_col = lv_map[filter_label], "level"

elif subject in ["暗唱例文集", "化学（一問一答）"]:
    chapter_col = "chapter" if "chapter" in df_raw.columns else None
    if chapter_col:
        unique_chapters = df_raw[chapter_col].dropna().unique().tolist()
        def extract_number(text):
            match = re.search(r'\d+', str(text))
            return int(match.group()) if match else 999
        try:
            sorted_chapters = sorted(unique_chapters, key=extract_number)
        except:
            sorted_chapters = sorted(unique_chapters)
        filter_label = st.sidebar.radio("章・セクションを選択", ["すべて"] + sorted_chapters)
        current_filter, filter_col = filter_label, chapter_col

# --- セッション管理 ---
if "current_sub" not in st.session_state or st.session_state.current_sub != subject or st.session_state.get("last_filter") != filter_label:
    st.session_state.current_sub, st.session_state.last_filter = subject, filter_label
    
    if filter_label == "すべて" or filter_col is None:
        df = df_raw.copy()
    else:
        df = df_raw[df_raw[filter_col].astype(str).str.strip() == str(current_filter).strip()]
    
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx, st.session_state.answered = 0, False
    if "choices" in st.session_state: del st.session_state["choices"]

if st.session_state.df.empty:
    st.error(f"該当データがありません。CSV内の表記を確認してください。")
    st.stop()

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# --- 表示ロジック ---
if subject == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)

    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummies, min(len(dummies), 3))
        random.shuffle(choices)
        st.session_state.choices, st.session_state.correct = choices, correct

    cols = st.columns(2)
    for i, choice in enumerate(st.session_state.choices):
        if cols[i % 2].button(choice, key=f"t_{i}", disabled=st.session_state.answered):
            st.session_state.selected, st.session_state.answered = choice, True
            st.rerun()

    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("Correct!")
        else: st.error(f"Incorrect... 正解：{st.session_state.correct}")
        st.write(f"**意味:** {row['all_answers']}")
        play_voice(word, "発音")
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False
            del st.session_state["choices"]; st.rerun()

elif subject == "暗唱例文集":
    # --- 【復元】暗唱例文集の注意事項 ---
    st.markdown("""
    <div class="description-box">
    <b>【学習モード】</b><br>
    ・<b>全文暗唱</b>：日本語を見て英文を完全に思い出します。<br>
    ・<b>空欄補充</b>：重要箇所が伏せられた状態で思い出します。
    </div>
    """, unsafe_allow_html=True)

    if "study_mode" not in st.session_state: st.session_state.study_mode = "全文暗唱"
    c1, c2 = st.columns(2)
    if c1.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    if c2.button("🔵 空欄補充"): st.session_state.study_mode = "空欄補充"; st.rerun()

    is_hint_mode = st.session_state.study_mode == "空欄補充"
    disp_text = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", str(row["English"])) if is_hint_mode else "（英文を思い出してください）"
    st.markdown(f'<div class="card orange-card">【日本語】<br><b>{row["japanese"]}</b><hr>【英文】<br>{disp_text}</div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#e91e63; font-weight:800; border-bottom:2px solid;">\1</span>', str(row["English"]))
        st.markdown(f'<div class="card" style="background:#fff9db !important;">【正解】<br><span style="font-size:1.1rem; font-family:serif;">{ans_highlight}</span></div>', unsafe_allow_html=True)
        play_voice(str(row["English"]).replace("**", ""), "音声")
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

elif subject == "化学（一問一答）":
    st.markdown(f'<div class="card green-card">【{row["chapter"]}】</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chem-question">{render_inline_math(row["question"])}</div>', unsafe_allow_html=True)
    
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        st.markdown(f'<div class="card" style="background:#e8f5e9 !important;">【正解】<br><span style="font-size:1.3rem; font-weight:bold; color:#2e7d32;">{render_inline_math(row["answer"])}</span></div>', unsafe_allow_html=True)
        st.info(f"💡 解説\n\n{render_inline_math(row['explanation'])}")
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
