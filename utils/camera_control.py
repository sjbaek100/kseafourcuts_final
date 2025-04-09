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

cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)  # macOS에서 AVFoundation 사용
if not cap.isOpened():
    print("⚠️ 소니 카메라 열기 실패 (AVFoundation)-1번 장치")
else:
    print("✅ 소니 카메라 열기 성공 (AVFoundation)-1번 장치")
    
# `0번` 장치가 소니 카메라로 잘 열렸다면, 이 인덱스를 명시적으로 사용해봅니다.
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
if cap.isOpened():
    print("✅ 소니 카메라 열기 성공 (AVFoundation) - 0번 장치")
else:
    print("⚠️ 소니 카메라 열기 실패 (AVFoundation) - 0번 장치")



def check_available_cameras():
    for i in range(5):  # 0, 1, 2, 3, 4번 장치 확인
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Device {i} is available")
            cap.release()
        else:
            print(f"Device {i} is not available")

check_available_cameras()

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
    stop_streaming_event.clear()
    
    # 기존에 열린 카메라 해제
    if cap is not None and cap.isOpened():
        cap.release()
    
    # USB3.0 캡처 장치(소니 카메라)로 강제 설정
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    
    if cap.isOpened():
        print("✅ 스트리밍 시작")
    else:
        print("⚠️ 스트리밍 실패: 비디오 장치 열기 실패")

def stop_streaming():
    global cap
    if cap is not None and cap.isOpened():
        cap.release()
        cap = None
        print("✅ 스트리밍 종료됨")
    else:
        print("⚠️ 스트리밍 종료 실패: 카메라가 열려 있지 않음")

def restart_streaming():
    global cap
    print("🔄 스트리밍 재시작")
    if cap is not None and cap.isOpened():
        print("♻️ 기존 cap 인스턴스 종료")
        cap.release()
        cap = None
        time.sleep(1)
    time.sleep(3.0)  # 일정 시간 대기
    for attempt in range(5):  # 재시도 횟수 늘림
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION) 
        if cap.isOpened():
            print("✅ 스트리밍 성공")
            return
        else:
            print(f"⚠️ 스트리밍 실패 (시도 {attempt + 1})")
            time.sleep(1)
    print("❌ 스트리밍 재시도 실패")



def kill_ptpcamera():
    try:
        subprocess.run(["killall", "-9", "PTPCamera"], check=True)
        print("✅ PTPCamera 종료됨")
    except subprocess.CalledProcessError:
        print("❎ PTPCamera 프로세스 없음 (이미 종료된 상태)")
    time.sleep(3.0)

def create_session_folder():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = os.path.join(BASE_DIR, timestamp)
    os.makedirs(session_path, exist_ok=True)
    print(f"📂 세션 폴더 생성됨: {session_path}")
    return session_path

def detect_camera_port():
    detect_command = ["sudo", "/opt/homebrew/bin/gphoto2", "--auto-detect"]
    result = subprocess.run(detect_command, capture_output=True, text=True)
    print("🕵️ gphoto2 카메라 인식 결과:", result.stdout)
    lines = result.stdout.strip().split('\n')
    for line in lines:
        if 'usb:' in line:
            port = line.split()[-1]
            print(f"🎯 사용 포트: {port}")
            return port
    print("⚠️ 카메라 포트를 찾을 수 없습니다.")
    return None

def capture_single_photo(index, folder=None, camera_port=None):
    if folder is None:
        raise ValueError("📂 저장할 session 폴더 경로가 필요합니다.")
    stop_remote_preview()
    time.sleep(2.0)

    if camera_port is None:
        camera_port = detect_camera_port()
        if not camera_port:
            restart_streaming()
            raise RuntimeError("❌ 카메라 포트를 찾을 수 없습니다!")

    global cap
    if cap is not None:
        print("🔌 capture_single_photo: 스트리밍 강제 종료")
        cap.release()
        cap = None

    kill_ptpcamera()
    time.sleep(3.0)

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

    if result.returncode != 0:
        restart_streaming()
        raise RuntimeError(f"❌ 카메라 촬영 실패: {result.stderr.strip()}")

    if not os.path.exists(photo_path):
        restart_streaming()
        raise RuntimeError("❌ 사진 파일이 저장되지 않았습니다!")

    print(f"✅ {index}번째 사진 저장됨: {photo_path}")
    restart_streaming()
    return photo_path

def generate_preview():
    global cap
    cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION) 

    if not cap.isOpened():
        print("⚠️ 스트리밍 실패: 비디오 장치 열기 실패")
        return

    start_time = time.time()

    while cap is not None and cap.isOpened():
        if stop_streaming_event.is_set() or (time.time() - start_time > 600):
            print("🛑 stop_streaming_event 감지 또는 타임아웃 → 스트리밍 종료")
            break

        success, frame = cap.read()

        if stop_streaming_event.is_set():
            print("🛑 stop_streaming_event 감지됨 → 바로 중단")
            break

        if not success:
            print("❌ 프레임 캡처 실패")
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("⚠️ 프레임 인코딩 실패")
            continue

        frame = buffer.tobytes()
        yield (b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    if cap is not None:
        print("🔌 generate_preview 종료 후 스트리밍 종료")
        cap.release()
        cap = None

    print("🛑 generate_preview 완전히 종료")
