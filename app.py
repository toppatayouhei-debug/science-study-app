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
# 2. デザイン (既存スタイルを継承しつつ暗唱用を追加)
# ==========================================
st.markdown("""
<style>
.stApp { background-color: #f0f2f5 !important; }
.header-container { text-align: center; margin-bottom: 25px; }
.main-title { color: #1e3a8a; font-size: 2.2rem; font-weight: 800; }
.description-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 25px; line-height: 1.6; }
.card { background-color: white !important; padding: 20px !important; border-radius: 12px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.08) !important; margin-bottom: 18px; }
.orange-card { border-left: 8px solid #ff9800 !important; }
.blue-card { border-left: 8px solid #2196f3 !important; }
.highlight { color: #ff9800 !important; font-weight: bold !important; }
.stButton button { width: 100%; border-radius: 10px; font-weight: bold; min-height: 45px; }
/* 音声再生用 */
.audio-container { background-color: #f8f9fa; border-radius: 10px; padding: 10px; display: flex; align-items: center; border: 1px solid #ddd; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ユーティリティ関数 (数式・音声)
# ==========================================
def clean_math(text):
    if pd.isna(text): return ""
    t = str(text).strip()
    t = t.replace("$", "").replace(r"\(", "").replace(r"\)", "").replace(r"\[", "").replace(r"\]", "")
    t = re.sub(r'([a-zA-Z0-9\)\}])\^([0-9a-zA-Z]+)', r'\1^{\2}', t)
    return t

def render_inline_math(text):
    if pd.isna(text): return ""
    s = str(text)
    pattern = r'([a-zA-Z0-9\\+\-*/=^{}()]+(?:\s*[=+\-*/]\s*[a-zA-Z0-9\\+\-*/=^{}()]+)+|[a-zA-Z]+\^[0-9]+)'
    def repl(m):
        return f"${clean_math(m.group(1))}$"
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
    except:
        pass

# ==========================================
# 4. データ読み込み
# ==========================================
@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "暗唱例文集": "english_sent.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    file_name = file_map.get(subject)
    if not file_name: return pd.DataFrame()
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base, file_name)
        df = pd.read_csv(path, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return pd.DataFrame()

# ==========================================
# 5. ヘッダー
# ==========================================
st.markdown('<div class="header-container"><div class="main-title">🧪 🔢 🧬 「理系」スターターパック</div></div>', unsafe_allow_html=True)

# ==========================================
# 6. サイドバー
# ==========================================
st.sidebar.title("🧬 学習メニュー")

subject = st.sidebar.selectbox(
    "科目を選択",
    ["選択してください", "システム英単語", "暗唱例文集", "入試数学の定石（数Ⅲ）", "入試数学の定石（ⅠAⅡB C）"]
)

if subject == "選択してください":
    st.markdown("""
    <div class="description-box">
        <p><strong>①英単語</strong>はリーディングで意味を増やすためのツールです。</p>
        <p><strong>②暗唱例文集</strong>は文法・構文を「使える」ようにするためのツールです。音読を重視しましょう。</p>
        <p><strong>③数学</strong>は入試の「定石」を整理しました。解法が即座に浮かぶまで繰り返しましょう。</p>
        <hr style="border:0; border-top:1px solid #eee; margin:15px 0;">
        <p style="color:#666; font-size:0.9rem;">👈 左のサイドバーから学習したい科目を選択してください。</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# 7. データ取得 & フィルタリング
# ==========================================
df_raw = load_data(subject)
if df_raw.empty:
    st.warning("データファイルが見つかりません。")
    st.stop()

# フィルタ処理
filter_label = "すべて"
if subject == "システム英単語":
    lv_map = {"すべて": "All", "Fundamental (1-600)": "Fundamental", "Essential (601-1200)": "Essential", "Advanced (1201-1700)": "Advanced", "Final (1701-2027)": "Final"}
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter = lv_map[filter_label]
    filter_col = "level"
elif "category" in df_raw.columns:
    cats = df_raw["category"].unique().tolist()
    filter_label = st.sidebar.radio("分野・単元選択", ["すべて"] + cats)
    current_filter = filter_label
    filter_col = "category"

# ==========================================
# 8. セッション管理
# ==========================================
changed = ("current_sub" not in st.session_state or st.session_state.current_sub != subject or st.session_state.get("last_filter") != filter_label)

if changed:
    st.session_state.current_sub = subject
    st.session_state.last_filter = filter_label
    df = df_raw.copy() if filter_label == "すべて" else df_raw[df_raw[filter_col].astype(str).str.contains(current_filter, case=False, na=False)]
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx = 0
    st.session_state.answered = False
    st.session_state.study_mode = "全文暗唱" # 例文用初期値
    if "choices" in st.session_state: del st.session_state["choices"]

row = st.session_state.df.iloc[st.session_state.idx % len(st.session_state.df)]

# ==========================================
# 9. 学習モード別のUI
# ==========================================

# --- システム英単語 (4択) ---
if subject == "システム英単語":
    word = str(row["question"])
    sentence = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sentence}</div>', unsafe_allow_html=True)

    if "choices" not in st.session_state:
        ans_list = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"])) if x.strip()]
        correct = ans_list[0]
        dummy_pool = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() and x.strip() != correct]
        choices = [correct] + random.sample(dummy_pool, min(len(dummy_pool), 3))
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
        play_voice(word, "発音を確認")
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False
            del st.session_state["choices"]; st.rerun()

# --- 暗唱例文集 (空欄/全文) ---
elif subject == "暗唱例文集":
    c1, c2 = st.columns(2)
    if c1.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    if c2.button("🔵 空欄補充"): st.session_state.study_mode = "空欄補充"; st.rerun()

    disp_text = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", str(row["English"])) if st.session_state.study_mode == "空欄補充" else "（英文を思い出してください）"
    st.markdown(f'<div class="card orange-card">【日本語】<br><b>{row["japanese"]}</b><hr>【英文】<br>{disp_text}</div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#e91e63; font-weight:800; border-bottom:2px solid;">\1</span>', str(row["English"]))
        st.markdown(f'<div class="card" style="background:#fff9db !important;">【正解】<br><span style="font-size:1.1rem; font-family:serif;">{ans_highlight}</span></div>', unsafe_allow_html=True)
        play_voice(str(row["English"]).replace("**", ""), "音声を聴く")
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- 数学モード (定石表示) ---
else:
    st.markdown(f'<div class="card blue-card">【{row["category"]}】</div>', unsafe_allow_html=True)
    st.latex(clean_math(row["question"]))

    if not st.session_state.answered:
        if st.button("定石と解答を確認する"):
            st.session_state.answered = True; st.rerun()
    else:
        st.markdown("---")
        st.markdown("##### 💡 攻略の定石")
        st.info(str(row["strategy"]))
        st.markdown("##### 【解答】")
        st.latex(clean_math(row["answer"]))
        if "explanation" in row and pd.notna(row["explanation"]):
            st.markdown("##### 📝 ポイント解説")
            st.markdown(render_inline_math(row["explanation"]))
        if st.button("次の問題へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
