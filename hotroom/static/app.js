(function () {
  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.left = "-9999px";
    document.body.appendChild(area);
    area.select();
    document.execCommand("copy");
    document.body.removeChild(area);
  }

  var forms = document.querySelectorAll("form[data-confirm]");
  for (var i = 0; i < forms.length; i++) {
    forms[i].addEventListener("submit", function (event) {
      var message = event.currentTarget.getAttribute("data-confirm");
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  }

  var copyButton = document.getElementById("copy-letter");
  if (copyButton) {
    var copyLabel = copyButton.textContent;
    copyButton.addEventListener("click", function () {
      var letter = document.getElementById("letter");
      var text = letter ? letter.value : "";
      var showCopied = function () {
        copyButton.textContent = "Copied";
        window.setTimeout(function () {
          copyButton.textContent = copyLabel;
        }, 2000);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(showCopied, function () {
          fallbackCopy(text);
          showCopied();
        });
      } else {
        fallbackCopy(text);
        showCopied();
      }
    });
  }

  function syncLetterForPrint() {
    var letter = document.getElementById("letter");
    var printed = document.getElementById("letter-print");
    if (letter && printed) {
      printed.textContent = letter.value;
    }
  }

  var letterField = document.getElementById("letter");
  if (letterField) {
    letterField.addEventListener("input", syncLetterForPrint);
  }

  // Print CSS hides the textarea and shows #letter-print, including Ctrl+P.
  window.addEventListener("beforeprint", syncLetterForPrint);

  var printButton = document.getElementById("print-sheet");
  if (printButton) {
    printButton.addEventListener("click", function () {
      syncLetterForPrint();
      window.print();
    });
  }
})();
