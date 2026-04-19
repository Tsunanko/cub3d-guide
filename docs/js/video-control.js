/* 動画制御: 堅牢な autoplay + ループ + クリック一時停止 (v2)
 *
 * 追加対策:
 * - IntersectionObserver で画面内に入った時に play
 * - pause イベントで（ユーザー意図以外なら）再開
 * - 定期的に paused を監視して自動復旧
 * - ユーザー操作フラグ（クリックによる明示的 pause かを判定）
 */
(function () {
  'use strict';

  function setupVideo(video) {
    if (video.dataset.controlInit === '1') return;
    video.dataset.controlInit = '1';

    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.preload = 'auto';

    // ユーザーが明示的に一時停止したか
    var userPaused = false;

    var tryPlay = function () {
      if (userPaused) return;
      try {
        var p = video.play();
        if (p !== undefined) {
          p.catch(function () { /* 無視 */ });
        }
      } catch (e) { /* 無視 */ }
    };

    // クリックで明示的に pause/play トグル
    video.addEventListener('click', function () {
      if (video.paused) {
        userPaused = false;
        tryPlay();
      } else {
        userPaused = true;
        video.pause();
      }
    });

    // pause が勝手に起きたら復帰（ユーザー意図でなければ）
    video.addEventListener('pause', function () {
      if (!userPaused && !document.hidden) {
        setTimeout(tryPlay, 50);
      }
    });

    // ended で明示的に巻き戻し（loop の保険）
    video.addEventListener('ended', function () {
      video.currentTime = 0;
      tryPlay();
    });

    // タブ復帰時に再生
    document.addEventListener('visibilitychange', function () {
      if (!document.hidden && !userPaused && video.paused) {
        tryPlay();
      }
    });

    // ページ内に入ったら再生（IntersectionObserver）
    if (typeof IntersectionObserver !== 'undefined') {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (ent) {
          if (ent.isIntersecting && !userPaused && video.paused) {
            tryPlay();
          }
        });
      }, { threshold: 0.1 });
      io.observe(video);
    }

    // 定期的な監視（3秒おき）
    setInterval(function () {
      if (!userPaused && video.paused && !document.hidden) {
        tryPlay();
      }
    }, 3000);

    // 初回再生試行
    tryPlay();
    setTimeout(tryPlay, 500);
    setTimeout(tryPlay, 1500);
  }

  function initAll() {
    var videos = document.querySelectorAll('video.cub3d-video, video[autoplay]');
    for (var i = 0; i < videos.length; i++) {
      setupVideo(videos[i]);
    }
  }

  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(initAll);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }
})();
