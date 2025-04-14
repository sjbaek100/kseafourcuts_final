import cv2
import numpy as np
import qrcode
import os

def create_collage_with_qr(photo_folder, frame_img_path, output_folder="static/final"):
    # 📁 session 폴더명 추출
    session_folder_name = os.path.basename(photo_folder)

    # 1. 사진 4개 불러오기
    photos = []
    for i in range(1, 5):
        photo_path = os.path.join(photo_folder, f"photo_{i}.jpg")
        photo = cv2.imread(photo_path)
        if photo is not None:
            photos.append(photo)

    if len(photos) != 4:
        raise ValueError("사진 4장이 필요합니다.")

    # 2. 사진 크기 조정
    resized_photos = [cv2.resize(photo, (300, 400)) for photo in photos]

    # 3. 대칭 구조 배치
    row1 = np.hstack((resized_photos[0], resized_photos[0]))
    row2 = np.hstack((resized_photos[1], resized_photos[1]))
    row3 = np.hstack((resized_photos[2], resized_photos[2]))
    row4 = np.hstack((resized_photos[3], resized_photos[3]))
    collage = np.vstack((row1, row2, row3, row4))

    # 4. 프레임 이미지 처리
    frame = cv2.imread(frame_img_path, cv2.IMREAD_UNCHANGED)
    frame_resized = cv2.resize(frame, (collage.shape[1], collage.shape[0]))
    b, g, r, a = cv2.split(frame_resized)
    alpha = a / 255.0
    alpha = cv2.merge([alpha, alpha, alpha])
    frame_rgb = cv2.merge([b, g, r])
    blended = (frame_rgb * alpha + collage * (1 - alpha)).astype(np.uint8)

    # 5. 고정 도메인 기반 QR 주소 생성
    qr_url = f"https://ksea4cuts.kro.kr/photos/{session_folder_name}/final.jpg"
    qr_img = qrcode.make(qr_url)
    qr_img = np.array(qr_img.convert("RGB"))
    qr_resized = cv2.resize(qr_img, (100, 100))

    # 6. QR 삽입 (오른쪽 아래)
    h, w = blended.shape[:2]
    qr_h, qr_w = qr_resized.shape[:2]
    blended[h-qr_h:h, w-qr_w:w] = qr_resized

    # 7. 저장
    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, "final_image_with_qr.jpg")
    cv2.imwrite(output_path, blended)

    print(f"✅ 최종 이미지 (QR 포함) 저장 완료: {output_path}")
    print(f"📎 QR 링크: {qr_url}")
    return output_path
