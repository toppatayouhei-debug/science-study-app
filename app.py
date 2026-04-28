import streamlit as st
import pandas as pd

# --- 1. ページ設定（元のタイトル） ---
st.set_page_config(page_title="入試数学の定石マスター", layout="wide")

@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    try:
        # CSV読み込み：sep=Noneでカンマ/タブを自動判別し、quotecharでカンマ混じりの列を保護
        df = pd.read_csv(file_map[subject], encoding="utf-8-sig", sep=None, engine='python', quotechar='"')
        # 列名の余計な空白やクォーテーションを掃除
        df.columns = df.columns.str.strip().str.replace('"', '').str.replace("'", "")
        return df
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return pd.DataFrame()

# --- 2. メインタイトル ---
st.title("🎓 入試数学の定石・解法の型")

# --- 3. サイドバー設定 ---
st.sidebar.header("メニュー設定")
subject = st.sidebar.selectbox("教材を選択", ["入試数学の定石（ⅠAⅡB C）", "入試数学の定石（数Ⅲ）", "システム英単語"])

df = load_data(subject)

if not df.empty:
    # --- 判定：数学 or 英語 ---
    # category列があれば数学、なければ英単語として処理
    if "category" in df.columns:
        # --- 数学用レイアウト ---
        categories = ["すべて"] + list(df["category"].unique())
        selected_category = st.sidebar.selectbox("カテゴリー選択", categories)

        if selected_category != "すべて":
            filtered_df = df[df["category"] == selected_category]
        else:
            filtered_df = df

        st.sidebar.divider()
        question_idx = st.sidebar.number_input("問題番号 (1～)", min_value=1, max_value=len(filtered_df), step=1) - 1
        
        row = filtered_df.iloc[question_idx]

        st.subheader(f"📌 {row['category']}")
        st.info("### 【問題】")
        st.markdown(row["question"])

        with st.expander("💡 この問題の定石（解法の型）を確認する", expanded=False):
            st.write(row["strategy"])

        if st.button("解答を表示する"):
            st.success("### 【解答】")
            st.write(row["answer"])
            st.divider()
            st.write("#### 📝 ポイント解説")
            st.write(row["explanation"])

    else:
        # --- 英単語用レイアウト（提示されたデータ構造に対応） ---
        levels = ["すべて"] + list(df["level"].unique())
        selected_level = st.sidebar.selectbox("レベル選択", levels)

        if selected_level != "すべて":
            filtered_df = df[df["level"] == selected_level]
        else:
            filtered_df = df

        st.sidebar.divider()
        word_idx = st.sidebar.number_input("単語番号 (1～)", min_value=1, max_value=len(filtered_df), step=1) - 1
        
        row = filtered_df.iloc[word_idx]

        st.subheader(f"🔤 {row['level']}")
        st.info(f"### 【単語】\n{row['question']}")
        
        if "exam_info" in row:
            st.write(f"出題情報: {row['exam_info']}")

        with st.expander("📖 例文を確認する", expanded=False):
            st.write(f"**{row['sentence']}**")
            st.write(f"訳: {row['translation']}")

        if st.button("意味を表示する"):
            st.success(f"### 【意味】\n{row['all_answers']}")
            if "dummy_pool" in row:
                st.write(f"その他候補: {row['dummy_pool']}")

else:
    st.warning("表示できるデータがありません。CSVファイルを確認してください。")

# --- 4. フッター ---
st.sidebar.caption("© 2026 入試数学の定石マスター")