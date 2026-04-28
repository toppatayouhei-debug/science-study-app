import streamlit as st
import pandas as pd

# ページ基本設定
st.set_page_config(page_title="学習マスター Pro", layout="wide")

@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    
    try:
        # sep=None, engine='python' でカンマ/タブを自動判別して読み込み
        df = pd.read_csv(file_map[subject], encoding="utf-8-sig", sep=None, engine='python', quotechar='"')
        # 列名の余計な空白や引用符を掃除
        df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")
        return df
    except Exception as e:
        st.error(f"読み込みエラーが発生しました: {e}")
        return pd.DataFrame()

# タイトル
st.title("🎓 学習マスター Pro")

# サイドバー：教材選択
subject = st.sidebar.selectbox("📖 教材を選択", ["入試数学の定石（ⅠAⅡB C）", "入試数学の定石（数Ⅲ）", "システム英単語"])
df = load_data(subject)

if not df.empty:
    # --- A. 数学（定石・解法の型）の表示レイアウト ---
    if "category" in df.columns and "strategy" in df.columns:
        # カテゴリー絞り込み
        categories = ["すべて"] + list(df["category"].unique())
        selected_cat = st.sidebar.selectbox("カテゴリー選択", categories)
        
        filtered_df = df if selected_cat == "すべて" else df[df["category"] == selected_cat]
        
        # 問題選択
        q_num = st.sidebar.number_input("問題番号", min_value=1, max_value=len(filtered_df), step=1)
        row = filtered_df.iloc[q_num - 1]
        
        st.subheader(f"📌 {row['category']}")
        
        # 問題エリア
        st.info("### 【問題】")
        st.markdown(row["question"])
        
        # 定石エリア（アコーディオン）
        with st.expander("💡 定石を確認する", expanded=False):
            # 数式が化けないよう、バックスラッシュを適切に処理して表示
            strategy_text = row["strategy"].replace(r'\\', r'\\')
            st.markdown(strategy_text)
            
        if st.button("答えを表示"):
            st.success("### 【解答・解説】")
            st.markdown(row["answer"])
            st.divider()
            st.write("#### 📝 ポイント解説")
            st.write(row["explanation"])

    # --- B. システム英単語（お送りいただいたデータ構造）の表示レイアウト ---
    elif "all_answers" in df.columns and "sentence" in df.columns:
        # レベル絞り込み
        levels = ["すべて"] + list(df["level"].unique())
        selected_level = st.sidebar.selectbox("レベル選択", levels)
        
        filtered_df = df if selected_level == "すべて" else df[df["level"] == selected_level]
        
        # 単語選択
        w_num = st.sidebar.number_input("単語番号", min_value=1, max_value=len(filtered_df), step=1)
        row = filtered_df.iloc[w_num - 1]
        
        st.subheader(f"🔤 英単語学習 [{row['level']}]")
        
        # 単語カード風表示
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b;">
            <h1 style="margin: 0; color: #31333f;">{row['question']}</h1>
            <p style="color: #555;">試験情報: {row['exam_info']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        # 例文セクション
        st.markdown("#### 📖 例文")
        st.markdown(f"> **{row['sentence']}**")
        st.caption(f"訳: {row['translation']}")

        # 解答表示ボタン
        if st.button("意味を表示"):
            st.success(f"### 正解: {row['all_answers']}")
            with st.expander("紛らわしい選択肢（ダミー）"):
                st.write(row["dummy_pool"])

    else:
        st.error("CSVの列名がアプリの想定と異なります。列名を確認してください。")

else:
    st.warning("データが見つかりません。CSVファイルがプログラムと同じフォルダにあるか確認してください。")

# サイドバー下部
st.sidebar.divider()
st.sidebar.caption("© 2026 AI Study Assistant")