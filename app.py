import streamlit as st
import pandas as pd

# ページの設定
st.set_page_config(page_title="入試数学の定石マスター", layout="wide")

@st.cache_data
def load_data(subject):
    file_map = {
        "システム英単語": "final_tango_list.csv",
        "入試数学の定石（数Ⅲ）": "math3.csv",
        "入試数学の定石（ⅠAⅡB C）": "math_std.csv"
    }
    
    try:
        # quotechar='"' を指定して、ダブルクォーテーション内のカンマを保護
        df = pd.read_csv(file_map[subject], encoding="utf-8-sig", quotechar='"')
        
        # 文字列のクリーニング（余計な改行や重複したバックスラッシュを修正）
        for col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'\\+', r'\\', regex=True)
        return df
    except Exception as e:
        st.error(f"CSVの読み込みに失敗しました。ファイル名や形式を確認してください。\nエラー内容: {e}")
        return pd.DataFrame()

# メインタイトル
st.title("🎓 入試数学の定石・解法の型")

# サイドバーの設定
st.sidebar.header("メニュー設定")
subject = st.sidebar.selectbox("教材を選択", ["入試数学の定石（ⅠAⅡB C）", "入試数学の定石（数Ⅲ）", "システム英単語"])

df = load_data(subject)

if not df.empty:
    # サイドバーでカテゴリーを選択
    categories = ["すべて"] + list(df["category"].unique())
    selected_category = st.sidebar.selectbox("カテゴリー選択", categories)

    # フィルタリング
    if selected_category != "すべて":
        filtered_df = df[df["category"] == selected_category]
    else:
        filtered_df = df

    # 問題の選択
    st.sidebar.divider()
    question_idx = st.sidebar.number_input("問題番号 (1～)", min_value=1, max_value=len(filtered_df), step=1) - 1
    
    # --- 表示エリア ---
    row = filtered_df.iloc[question_idx]

    st.subheader(f"📌 {row['category']}")
    
    # 問題文の表示
    st.info("### 【問題】")
    st.markdown(row["question"])

    # 解法の定石（アコーディオン）
    with st.expander("💡 この問題の定石（解法の型）を確認する", expanded=False):
        # バックスラッシュが消えないように raw 文字列として LaTeX 表示
        strategy_text = row["strategy"].replace('$', '')
        st.latex(rf"\text{{定石：}} {strategy_text}")
        st.write(row["strategy"]) # 文字としても表示（太字などが反映される）

    # 解答の表示
    if st.button("解答を表示する"):
        st.success("### 【解答】")
        ans_text = row["answer"].replace('$', '')
        st.latex(rf"\displaystyle {ans_text}")
        
        st.divider()
        st.write("#### 📝 ポイント解説")
        st.write(row["explanation"])

else:
    st.warning("表示するデータがありません。CSVファイルが正しい場所に配置されているか確認してください。")

# フッター
st.sidebar.caption("© 2026 入試数学の定石マスター")