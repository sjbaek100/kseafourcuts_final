import os
from datetime import datetime
import subprocess
import time
import cv2

BASE_DIR = "static/photos"

def kill_ptpcamera():
    try:
        subprocess.run(["killall", "-9", "PTPCamera"], check=True)
        print("✅ PTPCamera 종료됨")
    except subprocess.CalledProcessError:
        print("❎ PTPCamera 프로세스 없음 (이미 종료된 상태)")
    time.sleep(1.5)  # ⚠️ 이거 반드시 있어야 함!

        
def release_opencv_stream():
    import app
    if app.cap:
        print("🔌 OpenCV 스트리밍 종료")
        app.cap.release()
        app.cap = None
        cv2.destroyAllWindows()
        time.sleep(1.5)
    else:
        print("⚠️ cap is None → 스트리밍 종료")

# ✅ 여기서 추가
release = release_opencv_stream

        
def reset_camera():
    subprocess.call("pkill PTPCamera", shell=True)
    time.sleep(1.5)  # 1초 이상 대기해서 완전히 프로세스 종료 후 진행
    
def capture_single_photo(index=1, folder=None):
    kill_ptpcamera()

    if folder is None:
        raise ValueError("📂 저장할 session 폴더 경로가 필요합니다.")

    photo_path = os.path.join(folder, f"photo_{index}.jpg")
    print(f"📁 저장 시도 경로: {photo_path}")  # 로그용

    capture_command = [
        "sudo", "/opt/homebrew/bin/gphoto2",
        "--capture-image-and-download",
        "--debug", "--debug-logfile=my-gphoto-log.txt",
        "--filename", photo_path
    ]
    print("🧪 실행 명령어:", " ".join(capture_command))


    result = subprocess.run(capture_command, capture_output=True, text=True)
    print("📸 gphoto2 stdout:", result.stdout)
    print("📸 gphoto2 stderr:", result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"카메라 촬영 실패: {result.stderr.strip()}")

    # 여기서 진짜 파일이 저장되었는지 확인
    if not os.path.exists(photo_path):
        raise RuntimeError("❌ 사진 파일이 저장되지 않았습니다!")

    print(f"✅ {index}번째 사진 저장됨: {photo_path}")
    return photo_path


def create_session_folder():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = os.path.join(BASE_DIR, timestamp)
    os.makedirs(session_path, exist_ok=True)
    return session_path
