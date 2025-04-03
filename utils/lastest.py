import os

def get_latest_photo_folder(base_dir="static/photos"):
    folders = [
        os.path.join(base_dir, f)
        for f in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, f))
    ]
    if not folders:
        return None
    latest = max(folders, key=os.path.getmtime)
    return latest