import streamlit as st
import pandas as pd

# 1. ページ設定（元のタイトル）
st.set_page_config(page_title="入試数学の定石マスター", layout="wide")

@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    try:
        # CSV読み込み：区切り文字のミスを自動判別し、カンマ混じりのデータを保護
        df = pd.read_csv(file_map[subject], encoding="utf-8-sig", sep=None, engine='python', quotechar='"')
        # 列名の余計な空白を削除
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"読み込み失敗: {e}")
        return pd.DataFrame()

# 2. メインタイトル
st.title("🎓 入試数学の定石・解法の型")

# 3. サイドバー
st.sidebar.header("メニュー設定")
subject = st.sidebar.selectbox("教材を選択", ["入試数学の定石（ⅠAⅡB C）", "入試数学の定石（数Ⅲ）", "システム英単語"])

df = load_data(subject)

if not df.empty:
    # カテゴリー列の判定（levelかcategory、存在する方を使う）
    cat_col = "level" if "level" in df.columns else "category"
    
    categories = ["すべて"] + list(df[cat_col].unique())
    selected_cat = st.sidebar.selectbox("カテゴリー選択", categories)

    filtered_df = df if selected_cat == "すべて" else df[df[cat_col] == selected_cat]

    st.sidebar.divider()
    idx = st.sidebar.number_input("番号 (1～)", min_value=1, max_value=len(filtered_df), step=1) - 1
    row = filtered_df.iloc[idx]

    # --- メイン表示エリア ---
    st.subheader(f"📌 {row[cat_col]}")

    # 問題文 / 単語の表示
    st.info(f"### 【問題 / 単語】\n{row['question']}")
    
    # 英語データのみにある「出題情報」を表示
    if "exam_info" in df.columns:
        st.write(f"出題情報: {row['exam_info']}")

    # 「定石（数学）」または「例文（英語）」の表示
    if "strategy" in df.columns:
        with st.expander("💡 この問題の定石（解法の型）を確認する", expanded=False):
            st.write(row["strategy"])
    elif "sentence" in df.columns:
        with st.expander("📖 例文を確認する", expanded=False):
            st.write(f"**{row['sentence']}**")
            st.write(f"訳: {row['translation']}")

    # ボタン：解答 / 意味を表示
    if st.button("解答を表示する"):
        # 数学ならanswer、英語ならall_answersを表示
        ans_col = "answer" if "answer" in df.columns else "all_answers"
        st.success(f"### 【解答 / 意味】\n{row[ans_col]}")
        
        # 数学の解説がある場合
        if "explanation" in df.columns:
            st.divider()
            st.write(f"#### 📝 ポイント解説\n{row['explanation']}")
        # 英語のダミー選択肢がある場合
        if "dummy_pool" in df.columns:
            st.write(f"（誤答選択肢: {row['dummy_pool']}）")

else:
    st.warning("データが見つかりません。CSVファイルを確認してください。")

# フッター
st.sidebar.caption("© 2026 入試数学の定石マスター")