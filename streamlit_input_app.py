import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw
import os
import glob
from streamlit_image_coordinates import streamlit_image_coordinates
import csv
import io # ### 追加 ### メモリ上でCSVデータを扱うためにインポート

# --- 定数と定義 ---
BASEBALL_FIELD_IMG = 'baseballfield.jpg'
IMAGE_SIZE = (750, 750)

# 色と形の定義
HIT_TYPE_COLORS = {
    'ゴロ': 'green', 'フライ': 'blue', 'ライナー': 'red', '三振': 'black', '四死球': 'purple'
}
PITCH_TYPE_SHAPES = {
    'ストレート': 'ellipse', 'カーブ': 'rectangle', 'スライダー': 'triangle', 'フォーク': 'diamond', 'チェンジアップ': 'star', 'その他': 'ellipse'
}

# --- ヘルパー関数 ---
def draw_shape(draw_obj, shape, x, y, size, color):
    # (この関数は変更なし)
    h_size = size / 2
    if shape == 'ellipse':
        draw_obj.ellipse((x - h_size, y - h_size, x + h_size, y + h_size), fill=color, outline=color)
    elif shape == 'rectangle':
        draw_obj.rectangle((x - h_size, y - h_size, x + h_size, y + h_size), fill=color, outline=color)
    elif shape == 'triangle':
        points = [(x, y - h_size), (x - h_size, y + h_size), (x + h_size, y + h_size)]
        draw_obj.polygon(points, fill=color, outline=color)
    elif shape == 'diamond':
        points = [(x, y - h_size), (x + h_size, y), (x, y + h_size), (x - h_size, y)]
        draw_obj.polygon(points, fill=color, outline=color)
    else:
        draw_obj.ellipse((x - h_size, y - h_size, x + h_size, y + h_size), fill=color, outline=color)

# ### 削除 ### save_data関数は不要になるため削除します

# --- Streamlit アプリケーション ---
st.set_page_config(layout="wide")
st.title("⚾ 打球分析アプリ - データ入力")

# ベースとなる画像を読み込み
try:
    base_img = Image.open(BASEBALL_FIELD_IMG).resize(IMAGE_SIZE)
except FileNotFoundError:
    st.error(f"{BASEBALL_FIELD_IMG}が見つかりません。アプリと同じフォルダに配置してください。")
    st.stop() # 画像がなければアプリを停止

# 2カラムレイアウト
col1, col2 = st.columns([1, 2])

# col1: 操作パネル
with col1:
    st.header("操作パネル")
    
    # team_roster_data.csvを除いた名簿ファイルのみを検索
    all_csv_files = glob.glob('*.csv')
    team_files = sorted([f for f in all_csv_files if not f.endswith('_data.csv')])
    
    selected_team_file = st.selectbox("チームを選択", team_files)

    selected_player = None
    if selected_team_file:
        try:
            roster_df = pd.read_csv(selected_team_file, encoding='cp932', header=None)
            player_list = roster_df.iloc[:, 0].tolist() # 1列目を選手名として取得
            selected_player = st.selectbox("選手を選択", player_list)
        except Exception as e:
            st.error(f"{selected_team_file}の読み込みに失敗しました: {e}")
    
    balls = st.selectbox("ボール", [0, 1, 2, 3])
    strikes = st.selectbox("ストライク", [0, 1, 2])
    pitch_type = st.selectbox("球種", ['ストレート', 'カーブ', 'スライダー', 'フォーク', 'チェンジアップ', 'その他'])
    hit_type = st.selectbox("打球性質/結果", ['ゴロ', 'フライ', 'ライナー', '三振', '四死球'])
    
    # ### 変更 ### 保存ボタンは、後で表示されるダウンロードボタンの準備をする役割に変更
    prepare_button = st.button("データダウンロードの準備")

# col2: 画像表示とインタラクション
with col2:
    st.header("打球位置")
    st.write("打球位置をクリックしてください")
    
    # 画像クリックで座標を取得
    value = streamlit_image_coordinates(base_img, key="input_image")

    # クリックされたら、その点を描画したプレビューを表示
    if value:
        coords = value["x"], value["y"]
        st.write(f"クリック座標: {coords}")
        
        img_with_plot = base_img.copy()
        draw = ImageDraw.Draw(img_with_plot)
        color = HIT_TYPE_COLORS.get(hit_type, 'gray')
        shape = PITCH_TYPE_SHAPES.get(pitch_type, 'ellipse')
        draw_shape(draw, shape, coords[0], coords[1], 15, color)
        
        st.image(img_with_plot)
        
        # 準備ボタンが押されたら、ダウンロードボタンを表示
        if prepare_button:
            if selected_team_file and selected_player:
                # データをCSV形式の文字列に変換
                header = ['team_name', 'player_name', 'balls', 'strikes', 'pitch_type', 'hit_type', 'x_coord', 'y_coord']
                # team_name列には、どの名簿ファイルから入力したかを記録
                data_row = [selected_team_file, selected_player, balls, strikes, pitch_type, hit_type, coords[0], coords[1]]
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(header)
                writer.writerow(data_row)
                csv_data = output.getvalue()

                st.success(f"データが準備できました！")
                
                # ダウンロードボタンを設置
                st.download_button(
                    label="CSVデータをダウンロード",
                    data=csv_data,
                    file_name=f"{selected_player}_{hit_type}_data.csv", # ファイル名を動的に生成
                    mime="text/csv"
                )
            else:
                st.warning("チームと選手を選択してください。")
    else:
        # 何もクリックされていないときは元の画像を表示
        st.image(base_img)
