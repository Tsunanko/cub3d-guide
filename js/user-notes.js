/* マイメモ + 管理者フィードバック機能
 * - localStorage にページごとのメモを保存（サーバ不要、認証不要）
 * - 右下 FAB からドロワーを開き、Markdown で自由に書ける
 * - 全メモを .md ファイルとして Export / Import
 * - このページの内容について GitHub Issue を事前入力して開く
 * Material for MkDocs の navigation.instant（SPA 遷移）に対応
 */
(function () {
  "use strict";

  const SITE_CONFIG = {
    repo: "Tsunanko/cub3d-guide",
    siteName: "cub3D ガイド",
    primaryColor: "#5e35b1",
    primaryColorDark: "#4527a0",
    storageKey: "guide-notes-v1",
  };

  let state = null;
  let saveTimer = null;

  function loadState() {
    try {
      const raw = localStorage.getItem(SITE_CONFIG.storageKey);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") {
          if (!parsed.notes) parsed.notes = {};
          return parsed;
        }
      }
    } catch (e) { /* fall through */ }
    return { version: 1, notes: {}, updatedAt: null };
  }

  function saveState() {
    state.updatedAt = new Date().toISOString();
    try {
      localStorage.setItem(SITE_CONFIG.storageKey, JSON.stringify(state));
    } catch (e) {
      console.warn("[user-notes] localStorage 書き込み失敗:", e);
    }
  }

  function currentKey() {
    return location.pathname;
  }

  function currentTitle() {
    const h1 = document.querySelector(".md-content h1");
    if (h1) return h1.textContent.trim();
    return (document.title || "").split(" - ")[0] || location.pathname;
  }

  function ensureUI() {
    if (document.getElementById("un-fab")) return;

    document.documentElement.style.setProperty("--un-primary", SITE_CONFIG.primaryColor);
    document.documentElement.style.setProperty("--un-primary-dark", SITE_CONFIG.primaryColorDark);

    const fab = document.createElement("button");
    fab.id = "un-fab";
    fab.type = "button";
    fab.setAttribute("aria-label", "マイメモを開く");
    fab.title = "マイメモ";
    fab.innerHTML =
      '<span class="un-fab-icon" aria-hidden="true">📝</span>' +
      '<span class="un-fab-dot" id="un-fab-dot" hidden aria-hidden="true"></span>';
    document.body.appendChild(fab);

    const backdrop = document.createElement("div");
    backdrop.id = "un-backdrop";
    backdrop.hidden = true;
    document.body.appendChild(backdrop);

    const drawer = document.createElement("aside");
    drawer.id = "un-drawer";
    drawer.hidden = true;
    drawer.setAttribute("aria-label", "マイメモ");
    drawer.innerHTML =
      '<header class="un-head">' +
      '  <div class="un-head-title">' +
      '    <span class="un-head-icon" aria-hidden="true">📝</span>' +
      '    <div class="un-head-text">' +
      '      <div class="un-head-label">このページのメモ</div>' +
      '      <div class="un-head-page" id="un-page-title">—</div>' +
      '    </div>' +
      '  </div>' +
      '  <button id="un-close" type="button" aria-label="閉じる">✕</button>' +
      '</header>' +
      '<div class="un-hint">' +
      '  メモは <b>あなたのブラウザ内だけ</b> に保存されます。' +
      '  別の PC では見られないので、大事なメモは <b>「📥 書き出し」</b> で .md ファイルに残してください。' +
      '</div>' +
      '<textarea id="un-text" placeholder="ここに自由に書けます。Markdown もそのまま書けます。" spellcheck="false"></textarea>' +
      '<footer class="un-foot">' +
      '  <button id="un-export" type="button">📥 全メモ書き出し</button>' +
      '  <button id="un-import" type="button">📤 インポート</button>' +
      '  <button id="un-clear" type="button">🗑️ このページ消去</button>' +
      '  <button id="un-feedback" type="button" class="un-feedback">📮 このページにフィードバック</button>' +
      '</footer>' +
      '<input type="file" id="un-import-file" accept=".md,text/markdown,text/plain" hidden>';
    document.body.appendChild(drawer);

    fab.addEventListener("click", openDrawer);
    document.getElementById("un-close").addEventListener("click", closeDrawer);
    backdrop.addEventListener("click", closeDrawer);
    document.getElementById("un-text").addEventListener("input", onInput);
    document.getElementById("un-export").addEventListener("click", exportNotes);
    document.getElementById("un-import").addEventListener("click", () =>
      document.getElementById("un-import-file").click());
    document.getElementById("un-import-file").addEventListener("change", importNotes);
    document.getElementById("un-clear").addEventListener("click", clearPage);
    document.getElementById("un-feedback").addEventListener("click", openFeedback);
    document.addEventListener("keydown", onKey);
  }

  function openDrawer() {
    const drawer = document.getElementById("un-drawer");
    const backdrop = document.getElementById("un-backdrop");
    drawer.hidden = false;
    backdrop.hidden = false;
    requestAnimationFrame(() => {
      drawer.classList.add("un-open");
      backdrop.classList.add("un-open");
    });
    setTimeout(() => document.getElementById("un-text").focus(), 260);
  }

  function closeDrawer() {
    const drawer = document.getElementById("un-drawer");
    const backdrop = document.getElementById("un-backdrop");
    drawer.classList.remove("un-open");
    backdrop.classList.remove("un-open");
    setTimeout(() => {
      drawer.hidden = true;
      backdrop.hidden = true;
    }, 240);
  }

  function onKey(e) {
    if (e.key === "Escape") {
      const drawer = document.getElementById("un-drawer");
      if (drawer && !drawer.hidden) closeDrawer();
    }
  }

  function onInput(e) {
    const key = currentKey();
    const val = e.target.value;
    if (val) state.notes[key] = val;
    else delete state.notes[key];
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {
      saveState();
      updateDot();
    }, 300);
  }

  function updateDot() {
    const dot = document.getElementById("un-fab-dot");
    if (!dot) return;
    dot.hidden = !state.notes[currentKey()];
  }

  function refreshForPage() {
    const titleEl = document.getElementById("un-page-title");
    const textarea = document.getElementById("un-text");
    if (titleEl) titleEl.textContent = currentTitle();
    if (textarea) textarea.value = state.notes[currentKey()] || "";
    updateDot();
  }

  function clearPage() {
    if (!confirm("このページのメモを消去しますか？（他のページのメモは残ります）")) return;
    delete state.notes[currentKey()];
    const textarea = document.getElementById("un-text");
    if (textarea) textarea.value = "";
    saveState();
    updateDot();
  }

  function exportNotes() {
    const keys = Object.keys(state.notes).filter((k) => state.notes[k]).sort();
    if (keys.length === 0) {
      alert("保存されているメモはまだありません。");
      return;
    }
    const today = new Date().toISOString().slice(0, 10);
    const lines = [];
    lines.push("# マイメモ (" + SITE_CONFIG.siteName + ") — " + today + " エクスポート");
    lines.push("");
    for (const key of keys) {
      const url = location.origin + key;
      lines.push("## " + key);
      lines.push(url);
      lines.push("");
      lines.push(state.notes[key]);
      lines.push("");
      lines.push("---");
      lines.push("");
    }
    const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "guide-notes-" + today + ".md";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function importNotes(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function () {
      const text = String(reader.result || "");
      const blocks = text.split(/\n---\s*\n/);
      let added = 0;
      for (const blk of blocks) {
        const lines = blk.split("\n");
        let urlLine = null;
        let bodyStart = 0;
        for (let i = 0; i < lines.length; i++) {
          const m = lines[i].match(/^https?:\/\/\S+/);
          if (m) {
            urlLine = m[0];
            bodyStart = i + 1;
            break;
          }
        }
        if (!urlLine) continue;
        let pathname;
        try {
          pathname = new URL(urlLine).pathname;
        } catch (_) { continue; }
        const body = lines.slice(bodyStart).join("\n").replace(/^\s+|\s+$/g, "");
        if (!body) continue;
        state.notes[pathname] = body;
        added++;
      }
      saveState();
      refreshForPage();
      alert(added + " 件のメモをインポートしました。");
    };
    reader.readAsText(file);
    e.target.value = "";
  }

  function openFeedback() {
    const title = "[Feedback] " + currentTitle();
    const body =
      "## 対象ページ\n" + location.href + "\n\n" +
      "## フィードバックの種類\n" +
      "- [ ] 誤字・脱字\n" +
      "- [ ] 内容が間違っている\n" +
      "- [ ] 分かりにくい\n" +
      "- [ ] こういう解説がほしい\n" +
      "- [ ] その他\n\n" +
      "## 詳細\n\n（ここに書いてください）\n\n" +
      "---\nサイト内のフィードバックフォームから送信";
    const url =
      "https://github.com/" + SITE_CONFIG.repo + "/issues/new" +
      "?title=" + encodeURIComponent(title) +
      "&body=" + encodeURIComponent(body) +
      "&labels=" + encodeURIComponent("feedback,from-site");
    window.open(url, "_blank", "noopener,noreferrer");
  }

  function init() {
    state = loadState();
    ensureUI();
    refreshForPage();
  }

  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(init);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
