const endpoints = {
  register: "/api/register",
  checkUsername: "/api/check-username",
  login: "/api/login",
  profile: "/api/profile",
  chatLogs: "/api/chat-logs",
  sendChat: "/api/send-chat",
};

function createClient() {
  function request(method, endpoint, data, options = {}) {
    return new Promise((resolve, reject) => {
      $.ajax({
        url: endpoint,
        method,
        contentType: "application/json",
        data:
          method === "GET" || method === "DELETE" ? data : JSON.stringify(data),
        success(response) {
          resolve(response);
        },
        error(_, status, error) {
          reject(new Error(`API Error [${status}] ${error}`));
        },
      });
    });
  }

  return {
    get(endpoint, params = {}, options = {}) {
      return request("GET", endpoint, params, options);
    },
    post(endpoint, body = {}, options = {}) {
      return request("POST", endpoint, body, options);
    },
  };
}

function isFocusedTextInput() {
  return $(".text-input").is(":focus");
}

// 팝업 열기
function openPopup(popupName) {
  $(".popup-backdrop").hide();
  $(`.popup-backdrop[data-popup="${popupName}"]`).show();
}

// 팝업 닫기
function closePopup() {
  $(".popup-backdrop").hide();
}

$(document).ready(function () {
  // 사용자의 타이핑을 유도하는 타이핑 효과
  const typed = new Typed(".text-input", {
    strings: [
      "생각나는 대로, 거침없이.",
      "머리에 떠오르는 걸 바로 써요.",
      "주저하지 말고, 툭.",
      "생각 많을수록, 그냥 쓰는 게 답.",
      "생각을 포장하지 말고 그대로.",
      "지금 떠오른 그거, 바로 써요.",
      "하고 싶은 말, 그대로 던져요.",
    ],
    typeSpeed: 50,
    backSpeed: 50,
    attr: "placeholder",
    bindInputFocusEvents: true,
    fadeOut: false,
    loop: true,
  });

  $(".text-input").on("focus", function () {
    typed.reset();
  });

  $(".close-button").on("click", function () {
    closePopup();
  });

  $(".popup-backdrop").on("click", function (e) {
    if (e.target === this) {
      closePopup();
    }
  });
});

var swiper = new Swiper(".swiper", {
  direction: "vertical",
  slidesPerView: "auto",
  spaceBetween: 0,
  loop: false,
  allowTouchMove: false,
  autoHeight: true,
});

$(".text-input").on("keyup", function (e) {
  if (e.key === "Enter") {
    const inputText = $(this).val().trim();
    if (inputText.length === 0) return;

    const newSlide = `<div class="text-slot-item swiper-slide">${inputText}</div>`;
    swiper.appendSlide(newSlide);
    swiper.slideNext();

    $(this).val("");

    const maxSlides = 10;
    // 슬라이드 넘버 유지: removeSlide는 slideNext 애니메이션 끝나고 호출
    swiper.once("transitionEnd", function () {
      if (swiper.slides.length > maxSlides) {
        swiper.removeSlide(0);
      }
    });
  }
});
