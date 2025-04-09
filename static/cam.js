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

    startPhotoSequence();
  });

  function startPhotoSequence() {
    function takeNextPhoto() {
      if (photoCount >= 4) {
        form.submit();
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
                // fetch('/preview');
                setTimeout(takeNextPhoto, 2000);
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
