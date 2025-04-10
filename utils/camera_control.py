import os
from datetime import datetime
import subprocess
import time
import cv2
import threading
import requests

BASE_DIR = "static/photos"
cap = None
stop_streaming_event = threading.Event()
cap_lock = threading.Lock()

def stop_remote_preview():
    try:
        response = requests.get("http://localhost:5050/stop_preview", timeout=2)
        if response.status_code == 200:
            print("✅ 원격 프리뷰 종료 성공")
        else:
            print(f"⚠️ 프리뷰 종료 응답 이상: {response.status_code}")
    except requests.RequestException as e:
        print(f"⚠️ 프리뷰 종료 요청 실패: {e}")

def start_streaming():
    global cap, stop_streaming_event
    with cap_lock:
        stop_streaming_event.clear()
        if cap is not None and cap.isOpened():
            print("ℹ️ 이미 스트리밍 중입니다.")
            return
        if cap is not None:
            cap.release()

        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
        if cap.isOpened():
            print("✅ 스트리밍 시작")
        else:
            print("⚠️ 스트리밍 실패: 비디오 장치 열기 실패")

def stop_streaming():
    global cap, stop_streaming_event
    stop_streaming_event.set()
    with cap_lock:
        if cap is not None:
            cap.release()
            cap = None
    print("✅ 스트리밍 완전 종료")

def get_stream_frame():
    global cap
    with cap_lock:
        if cap is None or not cap.isOpened():
            return None
        success, frame = cap.read()

    if not success:
        return None

    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        return None

    return buffer.tobytes()

def kill_ptpcamera():
    try:
        subprocess.run(["killall", "-9", "PTPCamera"], check=True)
        print("✅ PTPCamera 종료됨")
    except subprocess.CalledProcessError:
        print("❎ PTPCamera 프로세스 없음 (이미 종료된 상태)")
    time.sleep(2.0)

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

def capture_single_photo(index, folder):
    if not folder:
        raise ValueError("📂 저장할 session 폴더 경로가 필요합니다.")

    print("🛑 프리뷰 종료 시도")
    stop_remote_preview()
    time.sleep(1.0)

    global cap
    with cap_lock:
        if cap is not None:
            print("🔌 스트리밍 강제 종료")
            cap.release()
            cap = None
    time.sleep(2.0)

    kill_ptpcamera()
    time.sleep(3.0)

    print("⏳ 장치 안정화 대기 중...")
    time.sleep(3.0)

    camera_port = detect_camera_port()
    if not camera_port:
        raise RuntimeError("❌ 카메라 포트를 찾을 수 없습니다!")

    time.sleep(2.0)

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

def create_session_folder():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = os.path.join(BASE_DIR, timestamp)
    os.makedirs(session_path, exist_ok=True)
    print(f"📂 세션 폴더 생성됨: {session_path}")
    return session_path
