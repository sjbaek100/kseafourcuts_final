import os

# 🚨 사진 폴더 경로
deploy_path = "deploy"

# 🌟 타겟 파일 이름
target_filename = "final.jpg"

# 📄 생성할 index.html 내용 (자동 다운로드)
def generate_html(file_name):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Download</title>
    <meta http-equiv="refresh" content="0; url={file_name}" />
</head>
<body>
    <p>If the download doesn't start automatically, <a href="{file_name}" download>click here</a>.</p>
</body>
</html>
"""

# 🔄 모든 세션 폴더에 대해 index.html 생성
def create_index_files(base_path):
    for folder in os.listdir(base_path):
        session_folder = os.path.join(base_path, folder)
        target_file = os.path.join(session_folder, target_filename)

        if os.path.isdir(session_folder) and os.path.isfile(target_file):
            index_path = os.path.join(session_folder, "index.html")
            with open(index_path, "w") as f:
                f.write(generate_html(target_filename))
            print(f"✅ index.html created in: {session_folder}")

if __name__ == "__main__":
    create_index_files(deploy_path)
    print("🎉 All index.html files created successfully!")
