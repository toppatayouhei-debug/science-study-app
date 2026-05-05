import streamlit as st
import pandas as pd
import random
import re
import base64
import requests
import urllib.parse

# ==================================================
# 1. 基本設定
# ==================================================
st.set_page_config(
    page_title="理系の暗記モノ 完全攻略",
    page_icon="🧬",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ==================================================
# 2. CSS（色の追加と修正）
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
.blue-card   { border-left: 8px solid #2196f3; } /* 数学用（水色） */
.purple-card { border-left: 8px solid #9c27b0; } /* 地理用（紫） */
.pink-card   { border-left: 8px solid #e91e63; }
.highlight { color: #ff9800 !important; font-weight: bold !important; }

/* 注意書き用スタイル */
.warning-box { background-color: #fff4f4; border: 1px solid #ffcdd2; color: #b71c1c; padding: 12px; border-radius: 10px; font-size: 0.9rem; margin-bottom: 15px; font-weight: bold; }

/* タイトルタグ */
.mini-tag { display: inline-block; padding: 2px 12px; border-radius: 8px; font-size: 0.8rem; font-weight: 800; margin-bottom: 8px; margin-top: 10px; }

/* 数学（水色） */
.tag-blue-ans { background-color: #2196f3; color: white; }
.tag-blue-exp { background-color: #e3f2fd; color: #1565c0; border: 1px solid #2196f3; }

/* 地理（紫） */
.tag-purple-ans { background-color: #9c27b0; color: white; }
.tag-purple-exp { background-color: #f3e5f5; color: #7b1fa2; border: 1px solid #9c27b0; }

/* 生物・化学 */
.tag-green-ans { background-color: #4caf50; color: white; }
.tag-green-exp { background-color: #f1f8e9; color: #2e7d32; border: 1px solid #4caf50; }
.tag-pink-ans { background-color: #e91e63; color: white; }
.tag-pink-exp { background-color: #fce4ec; color: #880e4f; border: 1px solid #e91e63; }

.description-box { background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e5e7eb; margin-bottom: 25px; line-height: 1.6; }
.stButton button { width: 100%; border-radius: 16px; font-size: 1.1rem; font-weight: 800; min-height: 55px; }
</style>
""", unsafe_allow_html=True)

# ==================================================
# 3. ユーティリティ関数
# ==================================================
def play_voice(text, label="音声を聴く"):
    try:
        q = urllib.parse.quote(text)
        url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={q}&tl=en&client=tw-ob"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            b64 = base64.b64encode(res.content).decode()
            md = f'<div style="background:#f8f9fa; border-radius:15px; padding:10px; margin-top:10px; display:flex; align-items:center; border:1px solid #ddd;"><span style="font-size:0.85rem; color:#ff9800; font-weight:bold; margin-right:auto;">🎧 {label}</span><audio src="data:audio/mp3;base64,{b64}" controls style="height: 35px;"></audio></div>'
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
        "数学Ⅲ（定石定着）": "math3.csv",
        "システム英単語": "final_tango_list.csv",
        "暗唱例文集": "english_sent.csv",
        "化学（一問一答）": "chemistry.csv",
        "地理（一問一答）": "geography.csv",
        "生物（一問一答）": "biology.csv"
    }
    try:
        df = pd.read_csv(files[subject], encoding="utf-8-sig").dropna(how='all')
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except: return pd.DataFrame()

# ==================================================
# 5. メインロジック
# ==================================================
st.markdown('<div class="main-title">🧪 🔢 🧬 理系の暗記モノ 完全攻略</div>', unsafe_allow_html=True)
st.sidebar.title("🧬 学習メニュー")

subject = st.sidebar.selectbox("科目を選択", ["選択してください", "数学Ⅲ（定石定着）", "システム英単語", "暗唱例文集", "化学（一問一答）", "地理（一問一答）", "生物（一問一答）"])

if subject == "選択してください":
    st.markdown('<div class="description-box"><b>【学習の進め方】</b><br>1. サイドバーから科目を選択。<br>2. 範囲を絞り込んで学習開始。</div>', unsafe_allow_html=True)
    st.stop()

raw_df = load_csv(subject)
if raw_df.empty:
    st.sidebar.error(f"⚠️ {subject} のファイルが見つかりません。")
    st.stop()

# フィルタリング処理
if "chapter" in raw_df.columns or "Chapter" in raw_df.columns:
    c_col = "chapter" if "chapter" in raw_df.columns else "Chapter"
    chaps = raw_df[c_col].dropna().unique().tolist()
    sel_chap = st.sidebar.radio("範囲を選択", ["すべて表示"] + chaps)
    df = raw_df if sel_chap == "すべて表示" else raw_df[raw_df[c_col].astype(str).str.strip() == sel_chap]
    current_filter = sel_chap
elif subject == "システム英単語":
    lv_map = {"すべて":"All", "Fundamental(1-600)":"Fundamental", "Essential(601-1200)":"Essential", "Advanced(1201-1700)":"Advanced", "Final(1701-2027)":"Final"}
    sel_lv = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    df = raw_df if lv_map[sel_lv] == "All" else raw_df[raw_df["level"].astype(str).str.contains(lv_map[sel_lv], na=False)]
    current_filter = sel_lv
else:
    df = raw_df
    current_filter = "All"

if st.session_state.get("quiz_subject") != subject or st.session_state.get("quiz_filter") != current_filter:
    reset_engine()
    st.session_state.quiz_subject, st.session_state.quiz_filter = subject, current_filter
    st.session_state.df = df.sample(frac=1).reset_index(drop=True)
    st.session_state.idx, st.session_state.answered = 0, False

active_df = st.session_state.get("df", pd.DataFrame())
idx = st.session_state.get("idx", 0)

if idx >= len(active_df):
    st.balloons(); st.success("全問終了！"); st.button("もう一度最初から", on_click=reset_engine); st.stop()

row = active_df.iloc[idx]
st.progress((idx + 1) / len(active_df))

# ==================================================
# 6. 各科目の表示UI
# ==================================================

# --- 数学Ⅲ（定石定着） ---
if subject == "数学Ⅲ（定石定着）":
    st.markdown(f'<div class="card blue-card">【{row.get("chapter", "設定なし")}】</div>', unsafe_allow_html=True)
    st.write(row.get("question", "")) # 数式対応
    
    # 【追加】問題表示時点で注意書きを表示
    st.markdown('<div class="warning-box">⚠️見た瞬間に解答の方針が浮かんでほしい問題を並べました。ここで解法を身につけて、必ず演習で手を動かして計算すること。計算力は大事です。</div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答え・方針を確認する"):
            st.session_state.answered = True
            st.rerun()
    else:
        st.markdown('<div class="mini-tag tag-blue-ans">方針・正解</div>', unsafe_allow_html=True)
        st.write(row.get("answer", "")) # 数式対応
        st.markdown('<div class="mini-tag tag-blue-exp">解説</div>', unsafe_allow_html=True)
        st.write(row.get("explanation", "")) # 数式対応
        if st.button("✅ 次へ"):
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- 地理（一問一答） ---
elif subject == "地理（一問一答）":
    st.markdown(f'<div class="card purple-card">【{row.get("chapter", row.get("Chapter", ""))}】</div>', unsafe_allow_html=True)
    st.markdown(str(row.get("question", row.get("Question", ""))))
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        st.markdown('<div class="mini-tag tag-purple-ans">正解</div>', unsafe_allow_html=True)
        st.markdown(str(row.get("answer", row.get("Answer", ""))))
        st.markdown('<div class="mini-tag tag-purple-exp">解説</div>', unsafe_allow_html=True)
        st.markdown(str(row.get("explanation", row.get("Explanation", ""))))
        if st.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- システム英単語 ---
elif subject == "システム英単語":
    word = str(row["question"])
    sent = re.sub(re.escape(word), f"<span class='highlight'>{word}</span>", str(row["sentence"]), flags=re.IGNORECASE)
    st.markdown(f'<div class="card orange-card">{sent}</div>', unsafe_allow_html=True)
    
    # 【追加】問題表示時点で注意書きを表示
    st.markdown('<div class="warning-box">⚠️シス単本体をメインにしましょう。情報量が全然違います。</div>', unsafe_allow_html=True)

    if "choices" not in st.session_state:
        correct = [x.strip() for x in re.split(r'[,、;]', str(row["all_answers"]))][0]
        dummies = [x.strip() for x in re.split(r'[,、;]', str(row["dummy_pool"])) if x.strip() != correct]
        st.session_state.choices = random.sample([correct] + random.sample(dummies, 3), 4)
        random.shuffle(st.session_state.choices)
        st.session_state.correct = correct

    cols = st.columns(2)
    for i, val in enumerate(st.session_state.choices):
        if cols[i%2].button(val, key=f"t_{i}", disabled=st.session_state.answered):
            st.session_state.selected, st.session_state.answered = val, True; st.rerun()

    if st.session_state.answered:
        if st.session_state.selected == st.session_state.correct: st.success("正解！")
        else: st.error(f"不正解... 正解：{st.session_state.correct}")
        st.info(f"意味：{row['all_answers']}\n訳：{row['translation']}")
        play_voice(word)
        if st.button("✅ 次の問題へ"):
            del st.session_state.choices
            st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- 暗唱例文集 ---
elif subject == "暗唱例文集":
    if "study_mode" not in st.session_state: st.session_state.study_mode = "全文暗唱"
    c_m1, c_m2 = st.columns(2)
    if c_m1.button("🔴 全文暗唱"): st.session_state.study_mode = "全文暗唱"; st.rerun()
    if c_m2.button("🔵 ヒントはこちら"): st.session_state.study_mode = "空欄補充"; st.rerun()
    
    disp = re.sub(r'\*\*(.*?)\*\*', "[ ____ ]", str(row["English"])) if st.session_state.study_mode == "空欄補充" else "（英文を思い出してください）"
    st.markdown(f'<div class="card orange-card">【日本語】<br><b>{row["japanese"]}</b><hr>【英文】<br>{disp}</div>', unsafe_allow_html=True)

    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        st.markdown('<div class="mini-tag english-ans-tag" style="background:#fff9db; color:#fab005; border:1px solid #fab005;">正解</div>', unsafe_allow_html=True)
        ans_highlight = re.sub(r'\*\*(.*?)\*\*', r'<span class="highlight">\1</span>', str(row["English"]))
        st.markdown(f'<div style="margin-bottom:15px; padding-left:5px;">{ans_highlight}</div>', unsafe_allow_html=True)
        play_voice(str(row["English"]).replace("**", ""))
        if st.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()

# --- その他（化学・生物） ---
elif subject in ["化学（一問一答）", "生物（一問一答）"]:
    card_c = "green-card" if subject == "化学（一問一答）" else "pink-card"
    t_ans = "tag-green-ans" if subject == "化学（一問一答）" else "tag-pink-ans"
    t_exp = "tag-green-exp" if subject == "化学（一問一答）" else "tag-pink-exp"
    
    st.markdown(f'<div class="card {card_c}">【{row.get("chapter", row.get("Chapter", ""))}】</div>', unsafe_allow_html=True)
    st.markdown(str(row.get("question", row.get("Question", ""))))
    if not st.session_state.answered:
        if st.button("答えを確認する"): st.session_state.answered = True; st.rerun()
    else:
        st.markdown(f'<div class="mini-tag {t_ans}">正解</div>', unsafe_allow_html=True)
        st.markdown(str(row.get("answer", row.get("Answer", ""))))
        st.markdown(f'<div class="mini-tag {t_exp}">解説</div>', unsafe_allow_html=True)
        st.markdown(str(row.get("explanation", row.get("Explanation", ""))))
        if st.button("✅ 次へ"): st.session_state.idx += 1; st.session_state.answered = False; st.rerun()
