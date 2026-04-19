/* GIF クリックで一時停止/再生
 * Gifffer を使って GIF をクリック可能にする
 */
(function () {
  'use strict';

  function wrapGifsForGifffer() {
    // すべての <img src="*.gif"> を data-gifffer 形式に書き換え
    var images = document.querySelectorAll('img');
    for (var i = 0; i < images.length; i++) {
      var img = images[i];
      var src = img.getAttribute('src') || '';
      if (src.toLowerCase().indexOf('.gif') > -1
          && !img.hasAttribute('data-gifffer')
          && !img.hasAttribute('data-gif-wrapped')) {
        img.setAttribute('data-gifffer', src);
        img.setAttribute('data-gif-wrapped', '1');
        img.removeAttribute('src');
      }
    }
    if (typeof Gifffer === 'function') {
      Gifffer();
    }
  }

  // Material の instant navigation に対応
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(function () {
      wrapGifsForGifffer();
    });
  } else {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', wrapGifsForGifffer);
    } else {
      wrapGifsForGifffer();
    }
  }
})();
