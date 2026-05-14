/* Mermaid を常に default theme で描画（ダークモードでも明るいパステル維持）
 *
 * Material for MkDocs は色スキーム切り替え時に Mermaid を自動で
 * 暗い theme に書き換えてしまうため、明示的に default で固定する。
 */
(function () {
  'use strict';

  var MERMAID_CONFIG = {
    startOnLoad: false,
    theme: 'default',
    flowchart: {
      htmlLabels: true,
      curve: 'basis'
    },
    themeVariables: {
      background: '#ffffff',
      primaryColor: '#E3F2FD',
      primaryBorderColor: '#1976d2',
      primaryTextColor: '#111111',
      secondaryColor: '#FFF9C4',
      secondaryBorderColor: '#f9a825',
      secondaryTextColor: '#111111',
      tertiaryColor: '#C8E6C9',
      tertiaryBorderColor: '#388e3c',
      tertiaryTextColor: '#111111',
      mainBkg: '#E3F2FD',
      textColor: '#111111',
      nodeTextColor: '#111111',
      edgeLabelBackground: '#ffffff',
      lineColor: '#546e7a',
      clusterBkg: '#F5F5F5',
      clusterBorder: '#9E9E9E'
    }
  };

  function renderAll() {
    if (typeof window.mermaid === 'undefined') return;
    try {
      window.mermaid.initialize(MERMAID_CONFIG);
    } catch (e) { /* 初期化失敗は無視 */ }

    var nodes = document.querySelectorAll('.mermaid');
    nodes.forEach(function (el) {
      // 既にレンダリング済みなら元テキストに戻して再描画
      if (el.dataset.mermaidSource) {
        el.innerHTML = el.dataset.mermaidSource;
      } else {
        el.dataset.mermaidSource = el.innerHTML;
      }
      el.removeAttribute('data-processed');
    });
    try {
      window.mermaid.run({ nodes: nodes });
    } catch (e) {
      try { window.mermaid.init(undefined, nodes); } catch (e2) {}
    }
  }

  // Material が emit する document$ を購読して毎回再描画
  if (window.document$ && typeof window.document$.subscribe === 'function') {
    window.document$.subscribe(function () {
      setTimeout(renderAll, 50);
    });
  } else {
    window.addEventListener('load', renderAll);
  }

  // 色スキーム切り替えの watch（ダーク/ライト切り替え時にも描き直す）
  var observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (m) {
      if (m.attributeName === 'data-md-color-scheme') {
        setTimeout(renderAll, 50);
      }
    });
  });
  observer.observe(document.body, { attributes: true });
})();
