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

const request = createClient();

function fetchRegister() {
  const name = $("#register-name").val();
  const username = $("#register-username").val();
  const password = $("#register-password").val();
  const passwordConfirm = $("#register-password-confirm").val();

  if (
    !name ||
    !username ||
    !password ||
    !passwordConfirm ||
    !validatePassword(password) ||
    !validateEmail(username) ||
    password !== passwordConfirm
  ) {
    return;
  }

  request
    .post(endpoints.register, {
      name: $("#register-name").val(),
      username: $("#register-username").val(),
      password: $("#register-password").val(),
      passwordConfirm: $("#register-password-confirm").val(),
    })
    .then(function (response) {
      closePopup();
      openPopup("login");
    });
}

/* ============== DOM 이벤트 ============== */

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

  // 팝업
  $(".close-button").on("click", function () {
    closePopup();
  });

  $(".popup-backdrop").on("click", function (e) {
    if (e.target === this) {
      closePopup();
    }
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

  let debounceTimer;
  // 회원가입 폼 유효성 검사
  $("#register-form input").on("keyup", function () {
    const id = $(this).attr("id");
    const value = $(this).val();
    checkFormValidity();

    if (id === "register-username") {
      if (value.length === 0) {
        $(".register-helper-text.email").text("이메일을 입력해 주세요.");
        $(".register-helper-text.email").removeClass("fail");
        $(".register-helper-text.email").removeClass("success");
        return;
      }

      if (!validateEmail(value)) {
        $(".register-helper-text.email").text(
          "올바른 이메일 주소를 입력해 주세요."
        );
        $(".register-helper-text.email").addClass("fail");

        return;
      }

      // 이전 타이머가 있다면 취소
      clearTimeout(debounceTimer);

      // 500ms 후에 API 요청 실행
      debounceTimer = setTimeout(() => {
        request
          .post(endpoints.checkUsername, {
            username: value,
          })
          .then(function () {
            $(".register-helper-text.email").text("좋아요, 사용할 수 있어요!");
            $(".register-helper-text.email").addClass("success");
          })
          .catch(function () {
            $(".register-helper-text.email").text(
              "이미 사용 중인 이메일이에요."
            );
            $(".register-helper-text.email").addClass("fail");
            $(".register-helper-text.email").removeClass("success");
          });
      }, 500);

      return;
    }

    if (id === "register-password") {
      if (value.length === 0) {
        $(".register-helper-text.password").text("비밀번호를 입력해 주세요.");
        $(".register-helper-text.password").removeClass("fail");
        $(".register-helper-text.password").removeClass("success");
        return;
      }

      if (!validatePassword(value)) {
        $(".register-helper-text.password").text(
          "영문, 숫자 조합으로 입력해 주세요."
        );
        $(".register-helper-text.password").addClass("fail");
        $(".register-helper-text.password").removeClass("success");

        return;
      }

      $(".register-helper-text.password").removeClass("fail");
      $(".register-helper-text.password").addClass("success");
      $(".register-helper-text.password").text("좋아요, 사용할 수 있어요!");

      return;
    }

    if (id === "register-password-confirm") {
      if (value.length === 0) {
        $(".register-helper-text.password-confirm").text(
          "비밀번호를 확인해 주세요."
        );
        $(".register-helper-text.password-confirm").removeClass("fail");
        $(".register-helper-text.password-confirm").removeClass("success");
        return;
      }

      if (value !== $("#register-password").val()) {
        $(".register-helper-text.password-confirm").text(
          "비밀번호가 일치하지 않아요."
        );
        $(".register-helper-text.password-confirm").addClass("fail");
        $(".register-helper-text.password-confirm").removeClass("success");
        return;
      }

      $(".register-helper-text.password-confirm").removeClass("fail");
      $(".register-helper-text.password-confirm").addClass("success");
      $(".register-helper-text.password-confirm").text(
        "좋아요, 비밀번호가 일치해요!"
      );

      return;
    }
  });

  // 회원가입 폼 제출
  $("#register-form").on("submit", function (e) {
    e.preventDefault();
    fetchRegister();
  });
});

/* ============== 유효성 검사 ============== */

function checkFormValidity() {
  const $name = $("#register-name");
  const $username = $("#register-username");
  const $password = $("#register-password");
  const $passwordConfirm = $("#register-password-confirm");

  if (
    $name.val().length > 0 &&
    $username.val().length > 0 &&
    $password.val().length > 0 &&
    $passwordConfirm.val().length > 0 &&
    $password.val() === $passwordConfirm.val()
  ) {
    $(".register-button").attr("disabled", false);
  } else {
    $(".register-button").attr("disabled", true);
  }
}

function validateEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

function validatePassword(password) {
  const passwordRegex = /^(?=.*[A-Za-z])(?=.*\d).+$/;
  return passwordRegex.test(password);
}
