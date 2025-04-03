import os
import shutil

SRC_BASE = "static/photos"
DEST_BASE = "deploy/photos"

def upload_all_final_images():
    if not os.path.exists(DEST_BASE):
        os.makedirs(DEST_BASE)

    for folder_name in os.listdir(SRC_BASE):
        src_folder = os.path.join(SRC_BASE, folder_name)
        dest_folder = os.path.join(DEST_BASE, folder_name)

        final_img_path = os.path.join(src_folder, "final.jpg")
        if os.path.exists(final_img_path):
            os.makedirs(dest_folder, exist_ok=True)
            dest_path = os.path.join(dest_folder, "final.jpg")
            shutil.copy2(final_img_path, dest_path)
            print(f"✅ 업로드 완료: {folder_name}/final.jpg")
        else:
            print(f"⚠️ final.jpg 없음: {folder_name}")

if __name__ == "__main__":
    upload_all_final_images()
