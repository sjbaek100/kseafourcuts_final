import cv2
import numpy as np
import os
import qrcode
import shutil

def create_collage_with_qr(photo_folder, frame_img_path):
    # 1. 프레임 로드
    frame = cv2.imread(frame_img_path, cv2.IMREAD_UNCHANGED)
    if frame is None or frame.shape[2] != 4:
        raise ValueError("프레임 이미지가 유효하지 않거나 알파 채널이 없습니다.")

    h_frame, w_frame = frame.shape[:2]

    # 2. 투명 영역 감지
    alpha = frame[:, :, 3]
    transparent_mask = (alpha < 128).astype(np.uint8) * 255
    contours, _ = cv2.findContours(transparent_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) < 8:
        raise ValueError("투명한 영역이 최소 8개 필요합니다.")

    bounding_boxes = sorted([cv2.boundingRect(c) for c in contours], key=lambda b: (b[1], b[0]))

    # 3. 사진 불러오기
    photos = []
    for i in range(1, 5):
        path = os.path.join(photo_folder, f"photo_{i}.jpg")
        photo = cv2.imread(path)
        if photo is None:
            raise ValueError(f"{i}번째 사진이 없습니다.")
        photos.append(photo)

    # 4. RGB 프레임 복사
    frame_rgb = frame[:, :, :3].copy()

    # 5. 각 영역에 사진 삽입
    for i in range(4):
        for j in range(2):
            x, y, w, h = bounding_boxes[i * 2 + j]
            resized = cv2.resize(photos[i], (w, h))
            frame_rgb[y:y+h, x:x+w] = resized

    # 💾 6. final.jpg 저장 (QR 없는 버전)
    final_path = os.path.join(photo_folder, "final.jpg")
    cv2.imwrite(final_path, frame_rgb)

    # 7. QR 코드 생성 (ksea4cuts.kro.kr 주소 사용)
    session_folder_name = os.path.basename(photo_folder)
    qr_url = f"https://ksea4cuts.kro.kr/photos/{session_folder_name}/final.jpg"
    qr = qrcode.make(qr_url)
    qr = np.array(qr.convert('RGB'))
    qr = cv2.resize(qr, (300, 300))  # qr 크기

    qr_h, qr_w = qr.shape[:2]
    margin = 30
    y_offset = h_frame - qr_h - margin
    x_right = w_frame - qr_w - margin
    x_left = w_frame // 2 - qr_w - margin

    # QR 2개 삽입
    if x_left >= 0:
        frame_rgb[y_offset:y_offset+qr_h, x_left:x_left+qr_w] = qr
    frame_rgb[y_offset:y_offset+qr_h, x_right:x_right+qr_w] = qr

    # 💾 8. final_with_qr 저장
    final_with_qr = os.path.join(photo_folder, "final_with_qr.jpg")
    cv2.imwrite(final_with_qr, frame_rgb)
    shutil.copy2(final_path, f"deploy/photos/{session_folder_name}/final.jpg")

    print(f"✅ final.jpg 저장 완료: {final_path}")
    print(f"✅ final_with_qr.jpg 저장 완료: {final_with_qr}")
    print(f"📎 QR에 삽입된 URL: {qr_url}")

    return final_with_qr
