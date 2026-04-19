/* 動画制御: 堅牢な autoplay + ループ + クリック一時停止
 *
 * - ページ表示時に確実に play を試みる
 * - タブに戻った時に再生再開
 * - ended イベントで loop の保険
 * - クリックは dblclick（誤クリック防止）
 */
(function () {
  'use strict';

  function setupVideo(video) {
    if (video.dataset.controlInit === '1') return;
    video.dataset.controlInit = '1';

    // 属性を確実にセット
    video.muted = true;
    video.loop = true;
    video.playsInline = true;

    // 初回再生を強化
    var tryPlay = function () {
      var promise = video.play();
      if (promise !== undefined) {
        promise.catch(function () {
          // autoplay 失敗時は無視（ユーザー操作後に再生される）
        });
      }
    };

    // loop の保険: ended で明示的に巻き戻し
    video.addEventListener('ended', function () {
      video.currentTime = 0;
      tryPlay();
    });

    // タブに戻った時に再生再開
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden && video.paused) {
        tryPlay();
      }
    });

    // クリックは pause/play トグル（シンプル）
    video.addEventListener('click', function () {
      if (video.paused) {
        tryPlay();
      } else {
        video.pause();
      }
    });

    // 初期再生
    tryPlay();

    // 1秒後に paused だったら再試行（autoplay policy 対策）
    setTimeout(function () {
      if (video.paused) tryPlay();
    }, 1000);
  }

  function initAll() {
    var videos = document.querySelectorAll('video.cub3d-video, video[autoplay]');
    for (var i = 0; i < videos.length; i++) {
      setupVideo(videos[i]);
    }
  }

  // Material の instant navigation に対応
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(initAll);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
