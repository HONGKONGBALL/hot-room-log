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

  // SVG text and strokes use the viewBox, so a fixed size becomes tiny on a phone.
  // Scale them so labels stay about 13px and points stay easy to point at.
  function fitChartText() {
    var printing = window.matchMedia && window.matchMedia("print").matches;
    var charts = document.querySelectorAll("svg.chart");
    for (var i = 0; i < charts.length; i++) {
      var svg = charts[i];
      var width = svg.getBoundingClientRect().width;
      if (printing) {
        var capped = width && width < 500 ? width : 411;
        if (capped >= 8) {
          width = capped;
        }
      }
      if (!width || width < 8) {
        continue;
      }
      var scale = width / 640;
      var timeSize = width < 420 ? 11 : 13;
      var labels = svg.querySelectorAll("text");
      var yLabels = svg.querySelectorAll("text.axis-label");

      function yGapPx() {
        var boxes = [];
        for (var i = 0; i < yLabels.length; i++) {
          boxes.push(yLabels[i].getBoundingClientRect());
        }
        boxes.sort(function (a, b) { return a.top - b.top; });
        var min = Infinity;
        for (var g = 1; g < boxes.length; g++) {
          min = Math.min(min, boxes[g].top - boxes[g - 1].bottom);
        }
        return min;
      }

      var ySize = 13;
      for (var pass = 0; pass < 8; pass++) {
        for (var j = 0; j < labels.length; j++) {
          var target = labels[j].classList.contains("axis-label") ? ySize : timeSize;
          labels[j].style.fontSize = (target / scale).toFixed(2) + "px";
        }
        if (yLabels.length < 2 || yGapPx() >= 3 || ySize <= 8) {
          break;
        }
        ySize -= 1;
      }
      var pointRadius = (7 * 640) / width;
      var pointStroke = (2 * 640) / width;
      var circles = svg.querySelectorAll("circle.point");
      for (var k = 0; k < circles.length; k++) {
        circles[k].setAttribute("r", pointRadius.toFixed(2));
        circles[k].style.strokeWidth = pointStroke.toFixed(2) + "px";
      }
      var trend = svg.querySelector("polyline.trend");
      if (trend) {
        trend.style.strokeWidth = ((2.25 * 640) / width).toFixed(2) + "px";
      }
      var axes = svg.querySelectorAll("line.axis");
      for (var a = 0; a < axes.length; a++) {
        axes[a].style.strokeWidth = ((1.25 * 640) / width).toFixed(2) + "px";
      }
    }
  }

  function markScrollers() {
    var boxes = document.querySelectorAll(".table-scroll");
    for (var i = 0; i < boxes.length; i++) {
      var box = boxes[i];
      var overflow = box.scrollWidth > box.clientWidth + 2;
      box.classList.toggle("can-scroll", overflow);
      if (!overflow) {
        box.classList.remove("at-start", "at-end");
        continue;
      }
      var max = box.scrollWidth - box.clientWidth;
      box.classList.toggle("at-start", box.scrollLeft <= 2);
      box.classList.toggle("at-end", box.scrollLeft >= max - 2);
    }
  }

  var tip = document.createElement("p");
  tip.className = "chart-tip";
  tip.hidden = true;
  document.body.appendChild(tip);

  function hideTip() {
    tip.hidden = true;
  }

  function showTip(circle) {
    var title = circle.querySelector("title");
    if (!title) {
      return;
    }
    tip.textContent = title.textContent;
    tip.hidden = false;
    tip.style.transform = "translate(-50%, calc(-100% - 10px))";
    var rect = circle.getBoundingClientRect();
    var tipRect = tip.getBoundingClientRect();
    var left = rect.left + rect.width / 2;
    left = Math.max(tipRect.width / 2 + 8, Math.min(left, window.innerWidth - tipRect.width / 2 - 8));
    tip.style.left = left + "px";
    if (rect.top - tipRect.height - 10 < 8) {
      tip.style.transform = "translate(-50%, 10px)";
      tip.style.top = rect.bottom + "px";
    } else {
      tip.style.top = rect.top + "px";
    }
  }

  var points = document.querySelectorAll("circle.point");
  for (var p = 0; p < points.length; p++) {
    points[p].addEventListener("mouseenter", function (event) {
      showTip(event.currentTarget);
    });
    points[p].addEventListener("mouseleave", hideTip);
    points[p].addEventListener("click", function (event) {
      showTip(event.currentTarget);
      event.stopPropagation();
    });
  }
  document.addEventListener("click", hideTip);

  var scrollers = document.querySelectorAll(".table-scroll");
  for (var s = 0; s < scrollers.length; s++) {
    scrollers[s].addEventListener("scroll", markScrollers, { passive: true });
  }

  function refit() {
    fitChartText();
    markScrollers();
  }

  window.addEventListener("resize", refit);
  window.addEventListener("beforeprint", refit);
  window.addEventListener("afterprint", refit);
  refit();
})();
