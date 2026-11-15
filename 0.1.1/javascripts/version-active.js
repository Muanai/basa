(function () {
  function markActiveVersion() {
    var container = document.querySelector(".md-version");
    if (!container) return;

    var currentBtn = container.querySelector(".md-version__current");
    if (!currentBtn || !currentBtn.firstChild) return;

    var currentTitle = currentBtn.firstChild.textContent.trim();
    var links = container.querySelectorAll(".md-version__link");

    links.forEach(function (link) {
      var title = link.firstChild ? link.firstChild.textContent.trim() : "";
      if (title === currentTitle) {
        link.classList.add("md-version__link--active");
        link.setAttribute("aria-current", "page");
      } else {
        link.classList.remove("md-version__link--active");
        link.removeAttribute("aria-current");
      }
    });
  }

  var observer = new MutationObserver(markActiveVersion);
  var header = document.querySelector(".md-header") || document.body;
  observer.observe(header, { childList: true, subtree: true });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", markActiveVersion);
  } else {
    markActiveVersion();
  }
})();
