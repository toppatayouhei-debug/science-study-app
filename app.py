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
.sub-title { text-align:center; color:#666; font-size:0.85rem; margin-bottom:1.5rem; }

.card { background:white; padding:22px; border-radius:18px; box-shadow:0 8px 20px rgba(0,0,0,0.06); margin-bottom:1rem; line-height:1.7; font-size:1.05rem; color:#111; }
.orange-card { border-left: 8px solid #ff9800; } 
.green-card  { border-left: 8px solid #4caf50; }
.highlight { color: #ff9800 !important; font-weight: bold !important; }

.description-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 25px; line-height: 1.6; }
.exp-card { background: #fff9db; padding: 18px; border-radius: 14px; border: 1px dashed #fab005; margin-top: 10px; font-size: 0.95rem; color: #333; }
.chem-exp-card { background: #e8f5e9; padding: 18px; border-radius: 14px; border: 1px dashed #4caf50; margin-top: 10px; font-size: 0.95rem; }

.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; min-height: 55px; transition: 0.2s; }
.tango-btn button { background-color: #fff4e6 !important; color: #ff9800 !important; border: 2px solid #ff9800 !important; }

.audio-container { background-color: #f8f9fa; border-radius: 15px; padding: 10px; margin-top: 10px; display: flex; align-items: center; border: 1px solid #ddd; }
.audio-text { font-size: 0.85rem; color: #ff9800; font-weight: bold; margin-right: auto; padding-left: 5px; }

.chem-text { font-size: 1.1rem; font-weight: 500; color: #1f2937; line-height: 1.8; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. 化学式ピンポイント変換関数
# ==================================================

def smart_chem_render(text):
    """文章内の化学式と思われる箇所だけを抽出してLaTeX化する"""
    if pd.isna(text): return ""
    t = str(text)

    # 1. すでに $ で囲まれている部分は保護
    if "$" in t:
        return t

    # 2. 化学式パターン（元素記号、数字、上付き・下付きの塊）を抽出
    # 例: H2O, OH-, SO4^2-, Fe3+, CH3COOH など
    pattern = r'([A-Z][a-z]?\d*|\^[\d\+\-]+|\([\w\d\+\-]+\)\d*|[\+\-])+'

    def replacer(match):
        s = match.group(0)
        # 短すぎる単独アルファベットなどは無視（「Aは〜」のAなどを誤爆させないため）
        if len(s) == 1 and s.isalpha():
            return s
        
        # 下付き数字の処理 (H2O -> H_{2}O)
        res = re.sub(r'([A-Z][a-z]?|[\]\)])(\d+)', r'\1_{\2}', s)
        # 上付きイオンの処理 (^2- -> ^{2-}, ^+ -> ^{+})
        res = re.sub(r'\^([\d\+\-]+)', r'^{\1}', res)
        # 上付きが明示されていないイオンの処理 (Fe3+ -> Fe^{3+}, OH- -> OH^{-})
        res = re.sub(r'(\d+[\+\-])', r'^{\1}', res)
        res = re.sub(r'(?<!\^)([\+\-])(?!\w)', r'^{\1}', res)
        
        return f"${res}$"

    # 化学式っぽい塊を見つけて置換
    processed_text = re.sub(r'[A-Za-z0-9\^ \(\)\+\-]+', lambda m: re.sub(r'([A-Z][a-z]?\d+|[A-Z][a-z]?\^[\d\+\-]+|[A-Z][a-z]?[\+\-])', replacer, m.group(0)), t)
    
    # 矢印などの記号を補完
    processed_text = processed_text.replace("->", r" $\rightarrow$ ").replace("→", r" $\rightarrow$ ")
    
    return processed_text

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
# 5. メイン画面・サイドバー
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

# --- フィルタリング ---
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
    with c_m1:
        if st.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    with c_m2:
        if st.button("🔵 ヒントはこちら"): st.session_state.study_mode = "空欄補充"; st.rerun()

    if st.session_state.study_mode == "空欄補充":
        st.info("💡 空欄に入る英語は１語とは限りません")

    disp = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", str(row["English"])) if st.session_state.study_mode == "空欄補充" else "（英文を思い出してください）"
    st.markdown(f'<div class="card orange-card">【日本語】<br><b>{row["japanese"]}</b><hr>【英文】<br>{disp}</div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span class="highlight">\1</span>', str(row["English"]))
        st.markdown(f'<div class="exp-card">【正解】<br>{ans_highlight}</div>', unsafe_allow_html=True)
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
    # スマートレンダリングを適用
    st.markdown(f'<div class="card green-card">【{row["chapter"]}】</div>', unsafe_allow_html=True)
    st.write(smart_chem_render(row["question"]))
    
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        st.markdown('<div class="exp-card" style="border-color:#4caf50;">【正解】</div>', unsafe_allow_html=True)
        st.write(smart_chem_render(row["answer"]))
        st.markdown('<div class="chem-exp-card">💡 解説</div>', unsafe_allow_html=True)
        st.write(smart_chem_render(row["explanation"]))
        if st.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
