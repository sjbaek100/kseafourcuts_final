import os

def get_latest_photo_folder():
    try:
        with open('static/last_folder.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise RuntimeError("❌ 최신 폴더 정보를 찾을 수 없습니다.")