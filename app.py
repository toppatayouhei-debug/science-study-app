import streamlit as st
import pandas as pd
import random
import re
import os
import urllib.parse
import base64
import requests

# ==================================================
# 1. 基本設定
# ==================================================
st.set_page_config(
    page_title="「理系」スターターパック",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================================================
# 2. CSS
# ==================================================
st.markdown("""
<style>
.stApp { background:#f7f8fc; }
.block-container { max-width:720px; padding-top: 3rem !important; } 
.main-title { text-align:center; font-size:1.8rem; font-weight:900; margin-bottom:0.2rem; color:#1e3a8a; }

/* 問題カード */
.card { background:white; padding:22px; border-radius:18px; box-shadow:0 8px 20px rgba(0,0,0,0.06); margin-bottom:1rem; line-height:1.7; font-size:1.05rem; color:#111; }
.orange-card { border-left: 8px solid #ff9800; } 
.green-card  { border-left: 8px solid #4caf50; }
.highlight { color: #ff9800 !important; font-weight: bold !important; }

/* 説明ボックス */
.description-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 25px; line-height: 1.6; }

/* タイトルタグ */
.mini-tag {
    display: inline-block;
    padding: 2px 12px;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 800;
    margin-bottom: 8px;
    margin-top: 10px;
}
.ans-tag { background-color: #4caf50; color: white; }
.exp-tag { background-color: #f1f8e9; color: #2e7d32; border: 1px solid #4caf50; }
.english-ans-tag { background-color: #fff9db; color: #fab005; border: 1px solid #fab005; }

/* ボタン */
.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; min-height: 55px; transition: 0.2s; }
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }

/* 音声再生 */
.audio-container { background-color: #f8f9fa; border-radius: 15px; padding: 10px; margin-top: 10px; display: flex; align-items: center; border: 1px solid #ddd; }
.audio-text { font-size: 0.85rem; color: #ff9800; font-weight: bold; margin-right: auto; padding-left: 5px; }

/* 本文エリア */
.content-area { margin-bottom: 15px; padding-left: 5px; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. ユーティリティ関数
# ==================================================

def render_text(text):
    """シンプルな化学式置換（崩れにくい初期版に近いロジック）"""
    if pd.isna(text): return ""
    t = str(text)
    # 化学式の下付き数字を置換 (例: H2O -> H₂O)
    t = re.sub(r'([A-Z][a-z]?)(\d+)', r'\1_{\2}', t)
    # イオンの上付きを置換 (例: ^2- -> ^{2-})
    t = re.sub(r'\^(\d*[\+\-])', r'^{\1}', t)
    
    # 文章の中に数式が含まれる可能性を考慮し、全体を$で囲むのではなく、
    # 置換が発生した箇所があればその文字列をLaTeXとして表示
    if "_{" in t or "^{" in t:
        return f"${t}$"
    return t

def play_voice(text, label="音声を聴く"):
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q}&tl=en&client=tw-ob"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            b64 = base64.b64encode(res.content).decode()
            md = f'<div class="audio-container"><span class="audio-text">🎧 {label}</span><audio src="data:audio/mp3;base64,{b64}" controls style="height: 35px;"></audio></div>'
            st.markdown(md, unsafe_allow_html=True)
    except: pass

def reset_engine():
    for k in ["df", "idx", "answered", "choices", "correct", "quiz_filter", "quiz_subject"]:
        if k in st.session_state: del st.session_state[k]

# ==================================================
# 4. データ読み込み
# ==================================================
@st.cache_data
def load_csv(subject):
    files = {
        "システム英単語": "final_tango_list.csv",
        "暗唱例文集": "english_sent.csv",
        "化学（一問一答）": "chemistry.csv"
    }
    try:
        df = pd.read_csv(files[subject], encoding="utf-8-sig").dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# ==================================================
# 5. メイン画面
# ==================================================
st.markdown('<div class="main-title">🧪 🔢 🧬 「理系」スターターパック</div>', unsafe_allow_html=True)
st.sidebar.title("🧬 学習メニュー")

subject = st.sidebar.selectbox("科目を選択", ["選択してください", "システム英単語", "暗唱例文集", "化学（一問一答）"])

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

raw_df = load_csv(subject)
if raw_df.empty:
    st.sidebar.error(f"⚠️ {subject} のファイルが見つかりません。")
    st.stop()

# フィルタリング
current_filter = "All"
if subject == "システム英単語":
    lv_map = {"すべて":"All", "Fundamental(1-600)":"Fundamental", "Essential(601-1200)":"Essential", "Advanced(1201-1700)":"Advanced", "Final(1701-2027)":"Final"}
    sel_lv = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter = lv_map[sel_lv]
    df = raw_df if current_filter == "All" else raw_df[raw_df["level"].astype(str).str.contains(current_filter, na=False)]
elif "chapter" in raw_df.columns:
    chaps = raw_df["chapter"].dropna().unique().tolist()
    def extract_num(t):
        m = re.search(r'\d+', str(t))
        return int(m.group()) if m else 999
    sorted_chaps = sorted(chaps, key=extract_num)
    sel_chap = st.sidebar.radio("範囲を選択", ["すべて表示"] + sorted_chaps)
    current_filter = sel_chap
    df = raw_df if sel_chap == "すべて表示" else raw_df[raw_df["chapter"].astype(str).str.strip() == sel_chap]
else:
    df = raw_df

if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_engine()
    st.session_state.quiz_subject, st.session_state.quiz_filter = subject, current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx, st.session_state.answered = 0, False

active_df = st.session_state.get("df", pd.DataFrame())
if active_df.empty: st.error("データがありません。"); st.stop()

idx = st.session_state.idx
if idx >= len(active_df):
    st.balloons(); st.success("全問終了！"); st.button("もう一度最初から", on_click=reset_engine); st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 6. 表示UI
# ==================================================

if subject == "暗唱例文集":
    st.markdown('<div class="description-box"><b>【学習モード】</b><br>・全文暗唱でわからないときは<b>「ヒント」ボタン</b>を押しましょう。</div>', unsafe_allow_html=True)
    if "study_mode" not in st.session_state: st.session_state.study_mode = "全文暗唱"
    c_m1, c_m2 = st.columns(2)
    if c_m1.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    if c_m2.button("🔵 ヒントはこちら"): st.session_state.study_mode = "空欄補充"; st.rerun()

    if st.session_state.study_mode == "空欄補充":
        st.info("💡 空欄に入る英語は１語とは限りません")

    disp = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", str(row["English"])) if st.session_state.study_mode == "空欄補充" else "（英文を思い出してください）"
    st.markdown(f'<div class="card orange-card">【日本語】<br><b>{row["japanese"]}</b><hr>【英文】<br>{disp}</div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        st.markdown('<div class="mini-tag english-ans-tag">正解</div>', unsafe_allow_html=True)
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span class="highlight">\1</span>', str(row["English"]))
        st.markdown(f'<div class="content-area">{ans_highlight}</div>', unsafe_allow_html=True)
        play_voice(str(row["English"]).replace("**", ""))
        if st.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

elif subject == "システム英単語":
    word = str(row["question"])
    sent = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sent}</div>', unsafe_allow_html=True)
    
    if "choices" not in st.session_state:
        correct = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"]))][0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() != correct]
        st.session_state.choices = random.sample([correct] + random.sample(dummies, 3), 4)
        random.shuffle(st.session_state.choices)
        st.session_state.correct = correct

    st.markdown('<div class="tango-btn">', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        if cols[i%2].button(val, key=f"t_{i}", disabled=st.session_state.answered):
            st.session_state.selected, st.session_state.answered = val, True; st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        play_voice(word)
        if st.button("✅ 次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

elif subject == "化学（一問一答）":
    st.markdown(f'<div class="card green-card">【{row["chapter"]}】</div>', unsafe_allow_html=True)
    
    # 修正ポイント：render_textを通さず、直接 st.markdown で描画する
    # これにより、CSV内の $...$ が正しく認識されます
    st.markdown(str(row["question"]))
    
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        st.markdown('<div class="mini-tag ans-tag">正解</div>', unsafe_allow_html=True)
        st.markdown(str(row["answer"]))
        
        st.markdown('<div class="mini-tag exp-tag">解説</div>', unsafe_allow_html=True)
        st.markdown(str(row["explanation"]))
        
        if st.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
