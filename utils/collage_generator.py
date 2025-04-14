import cv2
import numpy as np
import os
import qrcode
import shutil

def create_collage_with_qr(photo_folder, frame_img_path):
    print(f"📂 [시작] 콜라주 생성 시작! Photo folder: {photo_folder}, Frame: {frame_img_path}")

    # 1. 프레임 로드
    frame = cv2.imread(frame_img_path, cv2.IMREAD_UNCHANGED)
    if frame is None or frame.shape[2] != 4:
        raise ValueError("❌ 프레임 이미지가 유효하지 않거나 알파 채널이 없습니다.")
    print("✅ 프레임 이미지 로드 성공")

    h_frame, w_frame = frame.shape[:2]

    # 2. 투명 영역 감지
    alpha = frame[:, :, 3]
    transparent_mask = (alpha < 128).astype(np.uint8) * 255
    contours, _ = cv2.findContours(transparent_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) < 8:
        raise ValueError("❌ 투명한 영역이 최소 8개 필요합니다.")
    print(f"✅ 투명 영역 {len(contours)}개 감지")

    bounding_boxes = sorted([cv2.boundingRect(c) for c in contours], key=lambda b: (b[1], b[0]))

    # 3. 사진 불러오기
    photos = []
    for i in range(1, 5):
        path = os.path.join(photo_folder, f"photo_{i}.jpg")
        photo = cv2.imread(path)
        if photo is None:
            raise ValueError(f"❌ {i}번째 사진이 없습니다: {path}")
        photos.append(photo)
    print("✅ 모든 사진 로드 성공")
    
    frame_rgb = frame[:, :, :3].copy()

    # 4. RGB 프레임 복사
    canvas = np.ones_like(frame_rgb) * 255  # 흰색 배경 (or 다른 배경)
    
    # Step 1: 오른쪽 (원본 flip)
    for i in range(4):
        right_idx = i * 2 + 1
        x_right, y_right, w_right, h_right = bounding_boxes[right_idx]
        resized = cv2.resize(photos[i], (w_right, h_right))
        flipped = cv2.flip(resized, 1)  # 👉 거울 모드 (좌우 반전)
        canvas[y_right:y_right+h_right, x_right:x_right+w_right] = flipped

    # Step 2: 왼쪽 (오른쪽 복사)
    for i in range(4):
        left_idx = i * 2
        right_idx = i * 2 + 1
        x_left, y_left, w_left, h_left = bounding_boxes[left_idx]
        x_right, y_right, w_right, h_right = bounding_boxes[right_idx]
        right_crop = canvas[y_right:y_right+h_right, x_right:x_right+w_right].copy()
        right_resized = cv2.resize(right_crop, (w_left, h_left))
        canvas[y_left:y_left+h_left, x_left:x_left+w_left] = right_resized

    print("✅ 오른쪽 (거울 모드) → 왼쪽 복사 완료")

    # 5. 각 영역에 사진 삽입
    for i in range(4):
        for j in range(2):
            x, y, w, h = bounding_boxes[i * 2 + j]
            resized = cv2.resize(photos[i], (w, h))
            canvas[y:y+h, x:x+w] = resized
    print("✅ 사진 삽입 완료")
    
    alpha = frame[:, :, 3] / 255.0
    for c in range(3):  # RGB
        canvas[:, :, c] = (alpha * frame[:, :, c] + (1 - alpha) * canvas[:, :, c]).astype(np.uint8)

    # 6. final.jpg 저장
    final_path = os.path.join(photo_folder, "final.jpg")
    cv2.imwrite(final_path, canvas)
    os.makedirs(photo_folder, exist_ok=True)  # 폴더 없으면 생성
    if not cv2.imwrite(final_path, canvas):
        raise IOError(f"❌ final.jpg 저장 실패: {final_path}")
    print(f"✅ final.jpg 저장 완료: {final_path}")

    # 7. QR 코드 생성
    session_folder_name = os.path.basename(photo_folder)
    qr_url = f"https://ksea4cuts.kro.kr/{session_folder_name}/final.jpg"
    qr_instance = qrcode.QRCode(
    version=1,  # QR 코드 버전 (1: 가장 작음 ~ 40: 가장 큼)
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=20,  # ✔️ 박스 사이즈 (기본이 10, 더 키우면 원본 크기 커짐)
    border=4,  # 테두리 두께
    )

    qr_instance.add_data(qr_url)
    qr_instance.make(fit=True)

    qr_img = qr_instance.make_image(fill_color="black", back_color="white")
    qr = np.array(qr_img.convert('RGB'))

    # 이제 resize 하면 확실히 줄어듭니다
    qr = cv2.resize(qr, (120, 120))
    

    qr_h, qr_w = qr.shape[:2]
    margin = 30
    y_offset = h_frame - qr_h - margin
    x_right = w_frame - qr_w - margin
    x_left = w_frame // 2 - qr_w - margin

    if x_left >= 0:
        canvas[y_offset:y_offset+qr_h, x_left:x_left+qr_w] = qr
        canvas[y_offset:y_offset+qr_h, x_right:x_right+qr_w] = qr

    # 8. final_with_qr 저장
    final_with_qr = os.path.join(photo_folder, "final_with_qr.jpg")
    if not cv2.imwrite(final_with_qr, canvas):
        raise IOError(f"❌ final_with_qr.jpg 저장 실패: {final_with_qr}")
    print(f"✅ final_with_qr.jpg 저장 완료: {final_with_qr}")

    # 9. deploy 폴더 저장
    deploy_folder = os.path.join("deploy", session_folder_name)
    os.makedirs(deploy_folder, exist_ok=True)
    try:
        shutil.copy2(final_path, os.path.join(deploy_folder, "final.jpg"))
        print(f"✅ deploy 폴더로 복사 완료: {deploy_folder}/final.jpg")
    except Exception as e:
        raise IOError(f"❌ deploy 폴더 복사 실패: {e}")

    print(f"📎 QR에 삽입된 URL: {qr_url}")
    print("🎉 콜라주 생성 및 배포 완료!")

    return final_with_qr