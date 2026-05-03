# --- フィルタ設定 ---
filter_label = "すべて"
filter_col = None

if subject == "システム英単語":
    lv_map = {
        "すべて": "All", 
        "Fundamental (1-600)": "Fundamental", 
        "Essential (601-1200)": "Essential", 
        "Advanced (1201-1700)": "Advanced", 
        "Final (1701-2027)": "Final"
    }
    filter_label = st.sidebar.radio("レベル選択", list(lv_map.keys()))
    current_filter = lv_map[filter_label]

elif subject in ["暗唱例文集", "化学（一問一答）"]:
    chapter_col = "chapter" if "chapter" in df_raw.columns else None
    if chapter_col:
        unique_chapters = df_raw[chapter_col].dropna().unique().tolist()
        
        # --- ここを修正：数字順に並び替えるロジック ---
        def extract_number(text):
            # 文字列から最初の連続する数字を抽出
            match = re.search(r'\d+', str(text))
            return int(match.group()) if match else 999  # 数字がない場合は後ろに送る

        try:
            # 数値としてソート（例：1, 2, 10...）
            sorted_chapters = sorted(unique_chapters, key=extract_number)
        except:
            # 万が一エラーが出た場合は標準のソート
            sorted_chapters = sorted(unique_chapters)
        
        filter_label = st.sidebar.radio("章・セクションを選択", ["すべて"] + sorted_chapters)
        current_filter, filter_col = filter_label, chapter_col
