from flask import Flask, Response
import cv2
import threading

app = Flask(__name__)

cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)  # USB3.0 캡처 카드 사용
lock = threading.Lock()

@app.route('/preview')
def preview():
    def generate_frames():
        while True:
            with lock:
                success, frame = cap.read()
            if not success:
                continue
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051, debug=False)