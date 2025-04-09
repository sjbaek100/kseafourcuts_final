from flask import Flask, render_template, jsonify, request, redirect, url_for, session, Response, send_file
import os
import time
from utils import camera_control as camera
from datetime import datetime
import cv2
from utils.collage_generator import create_collage_with_qr
from utils.lastest import get_latest_photo_folder
from utils.printer import print_image
from utils.prepare_image import prepare_image_for_print
from utils.upload_all import upload_all_final_images


app = Flask(__name__)
app.secret_key = 'stephaniejiwonbaek_pleasethisbemyfinalonoe'

# 세션 폴더 생성
def create_session_folder():
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_folder = os.path.join('static/photos', now)
    os.makedirs(session_folder, exist_ok=True)
    print(f"📂 세션 폴더 생성됨: {session_folder}")
    return session_folder

# 실시간 스트리밍
def generate_frames():
    if camera.cap is None:
        print("⚠️ cap is None → 스트리밍 종료")
        return

    while True:
        success, frame = camera.cap.read()
        if not success:
            print("❌ 프레임 캡처 실패")
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            





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
    print(f"📂 현재 세션 폴더: {session['photo_folder']}")
    return render_template('cam.html')


@app.route('/preview')
def preview():
    camera.stop_streaming_event.clear()
    camera.start_streaming()
    return Response(camera.generate_preview(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_preview')
def stop_preview():
    camera.stop_streaming_event.set()
    camera.stop_streaming()
    return 'Stream stopped', 200



# # 🎥 실시간 프리뷰 (HDMI 미러링)
# @app.route("/preview")
# def preview():
#     # ✅ 스트리밍 먼저 켜기
#     camera.start_streaming()
#     time.sleep(1)  # 안정화 타임

#     return Response(camera.generate_preview(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame')

# 📸 사진 캡처 (USB 촬영)
@app.route("/capture", methods=["POST"])
def capture():
    data = request.get_json()
    index = data.get("index", 1)

    session_folder = session.get('photo_folder')
    if not session_folder:
        return jsonify({"success": False, "error": "세션 폴더가 설정되지 않았습니다."}), 500

    try:
        # 🔥 포트 재검출
        camera_port = camera.detect_camera_port()

        photo_path = camera.capture_single_photo(index=index, folder=session_folder, camera_port=camera_port)
        return jsonify({"success": True, "path": photo_path})
    except Exception as e:
        print(f"❌ 서버 오류 발생: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
            
# 사진 찍기 (버튼 클릭 → select_frame 으로 이동)
@app.route("/shoot", methods=["POST"])
def shoot():
    return redirect(url_for("select_frame"))

# 4. 프레임 고르는 화면
@app.route("/select_frame")
def select_frame():
    frame_dir = os.path.join("static", "frames")
    frame_list = os.listdir(frame_dir)
    return render_template("select_frame.html", frames=frame_list)

# 프레임 적용 후 최종 이미지 생성
@app.route('/apply_frame', methods=['POST'])
def apply_frame():
    if request.method == 'GET':
        return redirect(url_for('select_frame'))  # GET 접근은 select_frame 으로 redirect

    photo_folder = session.get("photo_folder") or get_latest_photo_folder()
    if not photo_folder or not os.path.exists(photo_folder):
        return "❌ 사진 촬영 후 프레임을 적용하세요.", 400

    selected_frame = request.form.get("frame")
    if not selected_frame:
        return "❌ 프레임을 선택하세요.", 400

    frame_img_path = os.path.join("static", "frames", selected_frame)
    if not os.path.exists(frame_img_path):
        return "❌ 프레임이 존재하지 않습니다.", 400

    final_image_path = create_collage_with_qr(photo_folder, frame_img_path)

    if not final_image_path:
        return "❌ 이미지 생성 실패", 500

    # 🔁 자동 업로드
    upload_all_final_images()


    # 🖨️ 프린트용으로 변환
    print_ready_full_path = final_image_path.replace('.jpg', '_flat.jpg')

    prepare_image_for_print(final_image_path, print_ready_full_path)

    # 🖨️ 출력
    # print_image(print_ready_full_path)

    # 결과 화면으로 이동
    # URL에서 static/ 부분은 제거해야 하니까!
    print_ready_web_path = print_ready_full_path.replace(os.path.join('static/'), '')
    return redirect(url_for('result', final_image=print_ready_web_path))




# 파일 다운로드
@app.route('/download/<session>/<filename>')
def download_file(session, filename):
    file_path = os.path.join("static", "photos", session, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return "파일을 찾을 수 없습니다.", 404

# 프린트 요청 (AJAX 용)
@app.route('/print', methods=['POST'])
def print_result_image():
    data = request.get_json()
    image_path = data.get("path")

    if not image_path:
        return jsonify(success=False, error="No image path provided."), 400

    # ✅ 여기서 static 제거
    if image_path.startswith('static/'):
        image_path = image_path.replace('static/', '', 1)

    # ✅ 절대 경로로 맞추기
    full_path = os.path.join(os.getcwd(), 'static', image_path)
    print(f"🖨️ 프린트할 파일 경로: {full_path}")

    if not os.path.exists(full_path):
        return jsonify(success=False, error=f"File not found: {full_path}"), 404

    success = print_image(full_path)
    return jsonify(success=success)

# 결과 화면
@app.route('/result')
def result():
    return render_template('result.html')

# 마지막 사진 조회
@app.route('/lastest')
def lastest_image():
    path = get_latest_photo_folder()
    return jsonify({"path": path})

@app.route('/<session_folder>/final.jpg')
def log_and_serve(session_folder):
    with open('access_log.txt', 'a') as log_file:
        log_file.write(f"{datetime.now()}: {session_folder} 접속\n")
    return send_file(f'deploy/{session_folder}/final.jpg')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5050)
    

