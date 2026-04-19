/* GIF クリックで一時停止/再生 (Gifffer 版)
 * Gifffer がロードされてから画像の src を data-gifffer に変換する。
 * Gifffer がロードされなければ普通の GIF として表示を継続（フォールバック）。
 */
(function () {
  'use strict';

  var MAX_WAIT = 50; // 最大 5 秒待機（100ms × 50 回）

  function wrapGifsForGifffer(attempt) {
    attempt = attempt || 0;

    // Gifffer が読み込まれているか確認
    if (typeof window.Gifffer !== 'function') {
      if (attempt < MAX_WAIT) {
        setTimeout(function () {
          wrapGifsForGifffer(attempt + 1);
        }, 100);
      }
      // 読み込まれなければ何もしない（GIF は通常通りアニメ表示される）
      return;
    }

    // .gif の img を data-gifffer 形式に変換
    var images = document.querySelectorAll('img');
    var modified = false;
    for (var i = 0; i < images.length; i++) {
      var img = images[i];
      var src = img.getAttribute('src') || '';
      if (src.toLowerCase().indexOf('.gif') > -1
          && !img.hasAttribute('data-gifffer')
          && !img.hasAttribute('data-gif-processed')) {
        img.setAttribute('data-gifffer', src);
        img.setAttribute('data-gif-processed', '1');
        img.removeAttribute('src');
        modified = true;
      }
    }
    if (modified) {
      try {
        window.Gifffer();
      } catch (e) {
        // 失敗したら src を復元
        var processed = document.querySelectorAll('img[data-gif-processed]');
        for (var j = 0; j < processed.length; j++) {
          var p = processed[j];
          var s = p.getAttribute('data-gifffer');
          if (s) {
            p.setAttribute('src', s);
            p.removeAttribute('data-gifffer');
            p.removeAttribute('data-gif-processed');
          }
        }
      }
    }
  }

  function init() {
    wrapGifsForGifffer(0);
  }

  // Material の instant navigation に対応
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(init);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
