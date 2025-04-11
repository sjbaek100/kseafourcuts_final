import os
from datetime import datetime
import subprocess
import cv2
import threading
import time

# 기본 설정
BASE_DIR = "static/photos"

# 스트리밍 관련 전역 변수
cap = None
stop_streaming_event = threading.Event()
cap_lock = threading.Lock()

# Sony Alpha (사진 촬영용) 포트 전역 변수
camera_port = None

# ✅ PTPCamera 프로세스 종료 (초기화 시 1번만)
def kill_ptpcamera():
    try:
        subprocess.run(["killall", "-9", "PTPCamera"], check=True)
        print("✅ PTPCamera 종료됨")
    except subprocess.CalledProcessError:
        print("❎ PTPCamera 프로세스 없음 (이미 종료된 상태)")

# ✅ 세션 폴더 생성
def create_session_folder():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = os.path.join(BASE_DIR, timestamp)
    os.makedirs(session_path, exist_ok=True)
    print(f"📂 세션 폴더 생성됨: {session_path}")
    return session_path

# ✅ 스트리밍 시작 (OpenCV → iPhone HDMI 캡처 카드)
def start_streaming():
    global cap, stop_streaming_event
    with cap_lock:
        stop_streaming_event.clear()
        if cap is not None and cap.isOpened():
            print("ℹ️ 이미 스트리밍 중입니다.")
            return
        if cap is not None:
            cap.release()

        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)  # ✅ iPhone HDMI 캡처 카드 장치 index 1
        if cap.isOpened():
            print("✅ 스트리밍 시작")
        else:
            print("⚠️ 스트리밍 실패: 비디오 장치 열기 실패")

# ✅ 스트리밍 프레임 생성
def generate_preview():
    global cap
    with cap_lock:
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if not cap.isOpened():
            print("⚠️ 스트리밍 실패: 비디오 장치 열기 실패")
            return

    while not stop_streaming_event.is_set():
        with cap_lock:
            if cap is None or not cap.isOpened():
                break
            success, frame = cap.read()

        if not success:
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    with cap_lock:
        if cap is not None:
            cap.release()
            cap = None

    print("🛑 generate_preview 완전히 종료")

# ✅ gphoto2 카메라 포트 탐지 (초기화 시 1번만)
def detect_camera_port():
    try:
        result = subprocess.run(["sudo", "/opt/homebrew/bin/gphoto2", "--auto-detect"],
                                capture_output=True, text=True)
        print("🕵️ gphoto2 카메라 인식 결과:", result.stdout)
        for line in result.stdout.splitlines():
            if 'usb:' in line:
                port = line.split()[-1]
                print(f"🎯 사용 포트: {port}")
                return port
    except Exception as e:
        print(f"❌ gphoto2 카메라 포트 탐지 실패: {e}")
    print("⚠️ 카메라 포트를 찾을 수 없습니다.")
    return None

# ✅ Sony Alpha 촬영 (빠르게 반복해서 사용 가능하도록)
# 전역 변수 (파일 맨 위에)
camera_port = None

def system_initialize():
    global camera_port
    print("🚀 시스템 초기화 시작")
    kill_ptpcamera()
    time.sleep(1.0)  # 안정화
    camera_port = detect_camera_port()
    if not camera_port:
        raise RuntimeError("❌ 초기화 실패: 카메라 포트를 찾을 수 없습니다!")
    print(f"🚀 시스템 초기화 완료: {camera_port}")

def capture_single_photo(index, folder):
    global camera_port

    if not folder:
        raise ValueError("📂 저장할 session 폴더 경로가 필요합니다.")

    # 🎯 PTPCamera 항상 kill
    kill_ptpcamera()
    time.sleep(2.0)

    # 🎯 포트 재탐지 항상 수행
    camera_port = detect_camera_port()
    if not camera_port:
        raise RuntimeError("❌ 카메라 포트를 찾을 수 없습니다!")

    photo_path = os.path.join(folder, f"photo_{index}.jpg")
    print(f"📁 저장 시도 경로: {photo_path}")

    capture_command = [
        "/opt/homebrew/bin/gphoto2",
        "--port", camera_port,
        "--capture-image-and-download",
        "--debug", "--debug-logfile=my-gphoto-log.txt",
        "--filename", photo_path
    ]

    result = subprocess.run(capture_command, capture_output=True, text=True)

    print("📸 gphoto2 stdout:", result.stdout)
    print("📸 gphoto2 stderr:", result.stderr)

    if result.returncode != 0 or not os.path.exists(photo_path):
        raise RuntimeError("❌ 사진 파일이 저장되지 않았습니다!")

    print(f"✅ {index}번째 사진 저장됨: {photo_path}")

    return photo_path
