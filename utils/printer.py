import subprocess

def print_image(filepath):
    printer_name = "Canon_SELPHY_CP1500_2"
    try:
        subprocess.run([
            "lpr",
            "-P", printer_name,
            "-o", "fit-to-page",
            "-o", "media=Postcard",  # 또는 "media=4x6"
            filepath
        ], check=True)
        print("✅ 프린트 성공:", filepath)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ 프린트 실패:", e)
        return False
