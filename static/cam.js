document.addEventListener("DOMContentLoaded", function () {
  const startBtn = document.getElementById("start");
  const popup = document.getElementById("popup");
  const timerDisplay = document.getElementById("timer");
  const countDisplay = document.getElementById("count");
  const infoBox = document.getElementById("info");
  const shutterSound = document.getElementById("shutter");
  const form = document.getElementById("shoot-form");

  let photoCount = 0;

  startBtn.addEventListener("click", function (event) {
    event.preventDefault();
    popup.style.display = "none";
    infoBox.style.display = "block";
    document.getElementById("live-view").src = "http://127.0.0.1:5051/preview";

    startPhotoSequence();
  });

  function startPhotoSequence() {
    function takeNextPhoto() {
      if (photoCount >= 4) {
        console.log("✅ 4장 촬영 완료. 프리뷰 종료 요청");
        fetch('http://127.0.0.1:5051/stop_preview')
          .then(() => {
            console.log("🛑 프리뷰 정상 종료");
            form.submit();
          })
          .catch(err => {
            console.error("❌ 프리뷰 종료 실패:", err);
            form.submit();
          });
        return;
      }

      photoCount++;
      countDisplay.textContent = `${photoCount}/4`;

      let countdown = 10;
      timerDisplay.textContent = countdown;

      const countdownInterval = setInterval(() => {
        countdown--;
        timerDisplay.textContent = countdown;

        if (countdown <= 0) {
          clearInterval(countdownInterval);
          timerDisplay.textContent = "DO NOT MOVE! 절대 움직이지 마세요!";
          timerDisplay.style.color = "red";
          shutterSound.play();

          fetch('/capture', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index: photoCount })
          })
          .then(res => res.json())
          .then(data => {
            if (data.success) {
              console.log(`${photoCount}번째 사진 촬영 성공`);
              setTimeout(takeNextPhoto, 1000);
            } else {
              console.error(`${photoCount}번째 사진 실패:`, data.error);
              alert(`❌ ${photoCount}번째 사진 실패: ${data.error}`);
            }
          })
          .catch(err => {
            console.error("📸 fetch 오류 발생:", err);
            alert(`❌ ${photoCount}번째 사진 실패: 네트워크 오류`);
          });
        }
      }, 1000);
    }

    takeNextPhoto();
  }
});