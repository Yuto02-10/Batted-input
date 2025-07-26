import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw
import os
import glob
from streamlit_image_coordinates import streamlit_image_coordinates
import csv
import io

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

def save_data(team_roster_file, player, balls, strikes, pitch_type, hit_type, x, y):
    """### 変更 ###: チームの名簿ファイル名からデータファイル名を生成して保存"""
    # 例: "Aチーム.csv" -> "Aチーム_data.csv"
    output_filename = team_roster_file.replace('.csv', '_data.csv')
    
    file_exists = os.path.isfile(output_filename)
    # ### 変更 ###: team_name列は不要になったため削除
    header = ['player_name', 'balls', 'strikes', 'pitch_type', 'hit_type', 'x_coord', 'y_coord']
    data_row = [player, balls, strikes, pitch_type, hit_type, x, y]
    
    with open(output_filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(header)
        writer.writerow(data_row)
    print(f"{output_filename} にデータを保存しました: {data_row}")

# --- Streamlit アプリケーション ---
st.set_page_config(layout="wide")
st.title("⚾ 打球分析アプリ - データ入力")

base_img = Image.open(BASEBALL_FIELD_IMG).resize(IMAGE_SIZE)

col1, col2 = st.columns([1, 2])

with col1:
    st.header("操作パネル")
    
    # hitting_data.csv や *_data.csv を除外した、名簿ファイルのみを検索
    all_csv_files = glob.glob('*.csv')
    team_files = sorted([f for f in all_csv_files if not f.endswith('_data.csv')])
    
    selected_team_file = st.selectbox("チームを選択", team_files)

    if selected_team_file:
        try:
            roster_df = pd.read_csv(selected_team_file, encoding='cp932', header=None)
            player_list = roster_df.iloc[:, 0].tolist()
            selected_player = st.selectbox("選手を選択", player_list)
        except Exception as e:
            st.error(f"{selected_team_file}の読み込みに失敗しました: {e}")
            selected_player = None
    
    balls = st.selectbox("ボール", [0, 1, 2, 3])
    strikes = st.selectbox("ストライク", [0, 1, 2])
    pitch_type = st.selectbox("球種", ['ストレート', 'カーブ', 'スライダー', 'フォーク', 'チェンジアップ', 'その他'])
    hit_type = st.selectbox("打球性質/結果", ['ゴロ', 'フライ', 'ライナー', '三振', '四死球'])
    
    save_button = st.button("この内容でデータを保存")

with col2:
    st.header("打球位置")
    st.write("打球位置をクリックしてください")
    
    value = streamlit_image_coordinates(base_img, key="input_image")

    if value:
        coords = value["x"], value["y"]
        st.write(f"クリック座標: {coords}")
        
        img_with_plot = base_img.copy()
        draw = ImageDraw.Draw(img_with_plot)
        color = HIT_TYPE_COLORS.get(hit_type, 'gray')
        shape = PITCH_TYPE_SHAPES.get(pitch_type, 'ellipse')
        draw_shape(draw, shape, coords[0], coords[1], 15, color)
        
        st.image(img_with_plot)
        
        if save_button:
            if selected_team_file and selected_player:
                save_data(selected_team_file, selected_player, balls, strikes, pitch_type, hit_type, coords[0], coords[1])
                st.success(f"データを保存しました: {selected_player}, {hit_type} at ({coords[0]}, {coords[1]})")
                st.balloons()
            else:
                st.warning("チームと選手を選択してください。")
