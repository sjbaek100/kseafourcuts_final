from flask import Flask, request, jsonify
import os
from datetime import datetime
import subprocess
import threading
import time
from flask_cors import CORS

app = Flask(__name__)
BASE_DIR = "static/photos"
CORS(app) 

camera_port = None  # 시작할 때 None 으로 두고, 감지 후 사용
SESSION_FOLDER = None 


# ✅ PTPCamera 프로세스 종료
def kill_ptpcamera():
    try:
        subprocess.run(["killall", "-9", "PTPCamera"], check=True)
        print("✅ PTPCamera 종료됨")
    except subprocess.CalledProcessError:
        print("❎ PTPCamera 프로세스 없음 (이미 종료됨)")

# ✅ 카메라 포트 자동 감지
def detect_camera_port():
    result = subprocess.run(["sudo", "/opt/homebrew/bin/gphoto2", "--auto-detect"],
                            capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    ports = [line.split()[-1] for line in lines if 'usb:' in line]
    if ports:
        latest_port = ports[-1]
        print(f"🎯 자동 인식된 포트: {latest_port}")
        return latest_port
    raise RuntimeError("❌ 카메라 포트를 찾을 수 없습니다.")

def update_last_folder(session_path):
    with open('static/last_folder.txt', 'w') as f:
        f.write(session_path)

def create_session_folder():
    global SESSION_FOLDER
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = os.path.join(BASE_DIR, timestamp)
    os.makedirs(session_path, exist_ok=True)
    os.chmod(session_path, 0o777)
    SESSION_FOLDER = session_path
    print(f"📂 세션 폴더 생성됨: {SESSION_FOLDER}")
    update_last_folder(SESSION_FOLDER)

# ✅ USB keep-alive 기능 (3초마다 USB 상태 확인)
def usb_keep_alive():
    while True:
        try:
            output = subprocess.check_output(["system_profiler", "SPUSBDataType"]).decode()
            if "ILCE-7RM2" in output:
                print("✅ USB 장치 정상 연결 유지 중")
            else:
                print("⚠️ USB 장치가 인식되지 않습니다!")
        except subprocess.CalledProcessError as e:
            print(f"❌ USB 상태 확인 중 오류 발생: {e}")
        time.sleep(3)

# ✅ 촬영 함수
def capture_image(camera_port, photo_path):
    capture_command = [
        "sudo", "/opt/homebrew/bin/gphoto2",
        "--port", camera_port,
        "--capture-image-and-download",
        "--filename", photo_path
    ]


    result = subprocess.run(capture_command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❗️촬영 실패, 포트 재검사 후 재시도")
        new_port = detect_camera_port()
        capture_command[4] = new_port
        result = subprocess.run(capture_command, capture_output=True, text=True)

    return result

# ✅ Flask route
@app.route('/capture', methods=['POST'])
def capture():
    try:
        global camera_port

        kill_ptpcamera()

        # 🚫 기존 : 촬영할 때마다 폴더 새로 만듦
        # session_folder = create_session_folder()

        # ✅ 수정 : 서버 시작 시 만들어둔 폴더 사용
        session_folder = SESSION_FOLDER

        index = request.json.get('index', 1)
        photo_path = os.path.join(session_folder, f"photo_{index}.jpg")

        print(f"📸 {index}번째 사진 저장 시도 → {photo_path}")

        # 촬영 시도
        result = capture_image(camera_port, photo_path)
        

        print("📸 gphoto2 stdout:", result.stdout)
        print("📸 gphoto2 stderr:", result.stderr)

        if result.returncode != 0 or not os.path.exists(photo_path):
            raise RuntimeError("❌ 사진 촬영 실패!")

        return jsonify(success=True, path=photo_path)

    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify(success=False, error=str(e)), 500

# ✅ 메인 실행
if __name__ == '__main__':
    # 최초 세션 폴더 생성 (서버 실행 시 1회만)
    create_session_folder()

    # 최초 포트 감지
    camera_port = detect_camera_port()

    # USB Keep-Alive 스레드 시작
    keep_alive_thread = threading.Thread(target=usb_keep_alive, daemon=True)
    keep_alive_thread.start()

    app.run(host='0.0.0.0', port=5052, debug=False)