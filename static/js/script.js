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

// 한글의 특성상 focus 이후에 조합되는 문자를 유추할 수 없다. 현재로써는
$(".container").on("click keydown", function (e) {
  const $input = $(".text-input").first();

  if (!$input.is(":focus")) {
    $input.focus();
  }
});
