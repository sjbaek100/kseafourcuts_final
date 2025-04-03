from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response, send_file
import cv2
import subprocess
import numpy as np
import subprocess
import os
import utils.camera_control as camera
from utils.collage_generator import create_collage_with_qr
from utils.lastest import get_latest_photo_folder
from utils.printer import print_image
from utils.prepare_image import prepare_image_for_print
import time
from utils.upload_all import upload_all_final_images


app = Flask(__name__)
app.secret_key = 'stephaniejiwonbaek_pleasethisbemyfinalonoe'
cap = None


# 1. 시작화면
@app.route('/')
def start():
    return render_template('start.html')

# 2. 안내 화면
@app.route('/guide')
def guide():
    return render_template('guide.html')

# 3. 카메라 화면
@app.route('/cam')
def cam():
    session['photo_folder'] = camera.create_session_folder()
    return render_template('cam.html')



#이거는 라이브 스트리밍
def generate_preview():
    global cap
    if cap is None or not cap.isOpened():
        print("📷 스트리밍 초기화 필요")
        cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)

    while True:
        if cap is None:
            print("⚠️ cap is None → 스트리밍 종료")
            break
        
        success, frame = cap.read()
        if not success:
            print("❌ 프레임 캡처 실패")
            continue

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            continue

        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/preview')
def preview():
    # preview route 종료 전
    camera.release()
    time.sleep(1)
    return Response(generate_preview(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
    
#여기까지 -- 계속확인하기
# 사진 캡쳐
@app.route('/capture', methods=['POST'])
def capture():
    global cap
    try:
        print(f"📸 [Server] 요청 수신 - 캡처 시작")

        if cap is not None:
            cap.release()
            cap = None
            cv2.destroyAllWindows()
            time.sleep(1.5)
            print("🔌 OpenCV 스트리밍 종료")

        subprocess.run(["killall", "-9", "PTPCamera"])
        print("🔫 PTPCamera 종료")

        session_folder = session.get('photo_folder')
        index = request.json.get('index', 1)

        photo_path = camera.capture_single_photo(index, folder=session_folder)

        print("✅ 사진 촬영 성공:", photo_path)

        cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)
        print("🎥 스트리밍 재시작")

        return jsonify(success=True)

    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify(success=False, error=str(e)), 500

# 사진 찍기
@app.route('/shoot', methods=['POST'])
def shoot():
    return redirect(url_for('select_frame'))

# 4. 프레임 고르는 화면
@app.route("/select_frame")
def select_frame():
    # static/frames 폴더 안의 프레임 파일 리스트 가져오기
    frame_dir = os.path.join("static", "frames")
    frame_list = os.listdir(frame_dir)
    return render_template("select_frame.html", frames=frame_list)

#프레임 적용
@app.route('/apply_frame', methods=['POST'])
def apply_frame():
    photo_folder = session.get("photo_folder") or get_latest_photo_folder()
    selected_frame = request.form.get("frame")

    if not photo_folder:
        return "❌ 사진 폴더를 찾을 수 없습니다.", 400

    frame_img_path = os.path.join("static", "frames", selected_frame)
    if not frame_img_path:
        return "❌ 프레임이 선택되지 않았습니다.", 400

    final_image_path = create_collage_with_qr(photo_folder, frame_img_path)

    if not final_image_path:
        return "❌ 이미지 생성 실패", 500

    # 🔁 자동 업로드 정리
    upload_all_final_images()

    # 🧩 1. 프린트용으로 변환
    print_ready_path = final_image_path.replace(".jpg", "_flat.jpg")
    print_ready_full_path = os.path.join("static", print_ready_path)
    prepare_image_for_print(os.path.join("static", final_image_path), print_ready_full_path)

    # 🖨️ 2. 출력
    print_image(print_ready_full_path)

    # 🔁 3. 결과 페이지로 이동
    return redirect(url_for('result', final_image=print_ready_path))

#파일 저장
@app.route('/download/<session>/<filename>')
def download_file(session, filename):
    file_path = os.path.join("static", "photos", session, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "파일을 찾을 수 없습니다.", 404
    
    
# 프린트
@app.route('/print', methods=['POST'])
def print_result_image():
    from utils.printer import print_image  # 위치에 맞게 import
    data = request.get_json()
    image_path = data.get("path")

    if not image_path:
        return jsonify(success=False, error="No image path provided."), 400

    full_path = os.path.join("static", image_path)

    success = print_image(full_path)
    return jsonify(success=success)


#결과 보여주고 나가라는 화면
@app.route('/result')
def result():
    return render_template('result.html')  

if __name__ == '__main__':
    cap = cv2.VideoCapture(1, cv2.CAP_AVFOUNDATION)  # 앱 실행 전 스트리밍 시작
    app.run(host='0.0.0.0', port=5050, debug=True)
