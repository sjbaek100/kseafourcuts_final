import subprocess
import os

def prepare_image_for_print(input_path, output_path):
    try:
        # 절대경로로 변환
        input_path = os.path.abspath(input_path)
        output_path = os.path.abspath(output_path)

        command = [
            "magick", input_path,
            "-resize", "1000x",
            "-gravity", "center",
            "-background", "white",
            "-extent", "1000x1480",
            output_path
        ]
        subprocess.run(command, check=True)
        print("✅ 이미지 프린트용으로 변환 완료:", output_path)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 이미지 변환 실패:", e)
        return False
