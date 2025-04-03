document.addEventListener("DOMContentLoaded", function () {
  const startBtn = document.getElementById("start");
  const popup = document.getElementById("popup");
  const camVideo = document.getElementById("cam");
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

    // 여기서 getUserMedia는 사용하지 않음. 대신 서버에서 gPhoto2로 사진을 찍어야 함
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
    
      let countdown = 3;
      timerDisplay.textContent = countdown;
    
      const countdownInterval = setInterval(() => {
        countdown--;
        timerDisplay.textContent = countdown;
    
        if (countdown <= 0) {
          clearInterval(countdownInterval);
          shutterSound.play();
    
          // 촬영 요청 보내기
          fetch('/capture', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ index: photoCount })
          })
            .then(res => res.json())
            .then(data => {
              if (data.success) {
                console.log(`${photoCount}번째 사진 촬영 성공`);
                // 다음 사진은 "5초 후" 진행
                setTimeout(takeNextPhoto, 8000);
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
  
  function startCapture(index) {
    document.getElementById('shooting-overlay').style.display = 'flex';
  
    fetch('/capture', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ index: index })
    })
      .then(res => res.json())
      .then(data => {
        // 잠시 후 오버레이 끄기
        setTimeout(() => {
          document.getElementById('shooting-overlay').style.display = 'none';
        }, 2000);
      });
      fetch('/capture', { method: 'POST' })
  .then(response => {
    if (!response.ok) throw new Error('캡처 요청 실패');
    return response.text();
  })
  .catch(error => {
    console.error("📸 fetch 오류 발생:", error);
    alert("사진 촬영 중 문제가 발생했습니다. 다시 시도해주세요.");
  });
  }  
});
