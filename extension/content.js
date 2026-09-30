const ENGAGE_API = "http://127.0.0.1:8787";

function deepAll(selector) {
  const found = [];
  const walk = (root) => {
    if (!root || !root.querySelectorAll) return;
    for (const el of root.querySelectorAll(selector)) found.push(el);
    for (const el of root.querySelectorAll("*")) {
      if (el.shadowRoot) walk(el.shadowRoot);
    }
  };
  walk(document);
  return found;
}

function looksLikePost(text) {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (cleaned.length < 40 || cleaned.length > 1800) return false;
  const lowered = cleaned.toLowerCase();
  const junk = [
    "function ",
    "addeventlistener",
    "skip to ",
    "seeing this ad",
    "voice memory",
    "engage does not",
    "report this ad",
    "contact info",
    "explore premium",
    "all activity",
    "message more",
  ];
  if (junk.some((item) => lowered.includes(item))) return false;
  if ((cleaned.match(/\{/g) || []).length >= 2) return false;
  return true;
}

function personName() {
  const heading = document.querySelector("h1");
  if (heading) {
    const line = (heading.innerText || "")
      .split("\n")
      .map((part) => part.trim())
      .find((part) => part && part.length < 60 && !/linkedin/i.test(part));
    if (line) return line;
  }
  const parts = document.title.split("|").map((part) => part.trim());
  return parts.find((part) => part && !/^(activity|linkedin)$/i.test(part)) || "";
}

function profileBio() {
  for (const node of deepAll(".text-body-medium")) {
    if (node.closest && node.closest("#engage-panel")) continue;
    const text = (node.innerText || "").replace(/\s+/g, " ").trim();
    if (text.length > 20 && text.length < 280 && !/followers|contact info/i.test(text)) return text;
  }
  return "";
}

function readLinkedInPage() {
  const selectors = [
    ".update-components-text",
    ".feed-shared-update-v2__commentary",
    ".feed-shared-inline-show-more-text",
    "[data-testid='expandable-text-box']",
    "[componentkey*='commentary']",
  ];
  const texts = [];
  for (const selector of selectors) {
    for (const el of deepAll(selector)) {
      if (el.closest && el.closest("#engage-panel")) continue;
      const text = (el.innerText || "").replace(/\s+/g, " ").trim().replace(/\s*(…|\.\.\.)\s*more\s*$/i, "");
      if (looksLikePost(text)) texts.push(text.slice(0, 1500));
    }
    if (texts.length) break;
  }
  if (!texts.length) {
    for (const card of deepAll(".feed-shared-update-v2, .profile-creator-shared-feed-update__container")) {
      let best = "";
      for (const node of card.querySelectorAll("span, p, div")) {
        const text = (node.innerText || "").replace(/\s+/g, " ").trim();
        if (text.length > best.length && looksLikePost(text)) best = text;
      }
      if (best) texts.push(best.slice(0, 1500));
    }
  }
  const unique = [];
  for (const text of texts.sort((a, b) => b.length - a.length)) {
    const key = text.toLowerCase();
    if (unique.some((kept) => kept.toLowerCase() === key || kept.toLowerCase().includes(key))) continue;
    unique.push(text);
  }
  return {
    name: personName(),
    bio: profileBio(),
    profile_url: location.href,
    texts: unique.slice(0, 20),
    kind: pageKind(location.href),
  };
}

function pageKind(href) {
  const value = String(href || "");
  if (/\/feed\/update\/|linkedin\.com\/posts\//.test(value)) return "post";
  try {
    const path = new URL(value).pathname;
    if (/^\/in\/[^/]+\/?$/.test(path) || /^\/in\/[^/]+\/recent-activity(\/|$)/.test(path)) return "profile";
  } catch (err) {
    return "other";
  }
  return "other";
}

function fillCommentBox(text) {
  const selectors = [
    ".comments-comment-box .ql-editor",
    ".comments-comment-texteditor .ql-editor",
    "[class*='comments-comment'] [contenteditable='true']",
    "[aria-label*='comment' i][contenteditable='true']",
    ".ql-editor",
  ];
  let editor = null;
  for (const selector of selectors) {
    const hits = deepAll(selector);
    if (hits.length) {
      editor = hits[hits.length - 1];
      break;
    }
  }
  if (!editor) return { filled: false };
  editor.focus();
  const container = editor.closest(".ql-container");
  const quill = container && (container.__quill || container.quill);
  if (quill && typeof quill.setText === "function") {
    quill.setText(text, "user");
    return { filled: true };
  }
  const selection = window.getSelection();
  if (selection) {
    const range = document.createRange();
    range.selectNodeContents(editor);
    selection.removeAllRanges();
    selection.addRange(range);
  }
  if (!document.execCommand("insertText", false, text)) editor.textContent = text;
  editor.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: text }));
  return { filled: true };
}

function ensureStyle() {
  if (document.getElementById("engage-style")) return;
  const style = document.createElement("style");
  style.id = "engage-style";
  style.textContent = `
    #engage-panel { position: fixed; top: 12px; right: 12px; z-index: 2147483646; width: 280px; padding: 12px; background: #1c1915; color: #f4f0e8; font: 13px/1.4 "Avenir Next", "Segoe UI", sans-serif; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,.25); }
    #engage-panel .step { margin: 0 0 4px; letter-spacing: .08em; text-transform: uppercase; font-size: 10px; color: #c9bba6; }
    #engage-panel h2 { margin: 0 0 6px; font-size: 16px; font-weight: 600; }
    #engage-panel p { margin: 0 0 8px; }
    #engage-panel .bar { height: 4px; background: #3a342c; border-radius: 4px; overflow: hidden; margin: 8px 0; }
    #engage-panel .bar > div { height: 100%; width: 0; background: #e6d3b3; }
    #engage-panel.busy .bar > div { width: 40%; animation: engage-slide 1s ease-in-out infinite; }
    @keyframes engage-slide { from { transform: translateX(-120%); } to { transform: translateX(320%); } }
    #engage-panel button, #engage-panel select { width: 100%; margin-top: 6px; font: inherit; }
    #engage-panel button { padding: 8px; border: 0; background: #f4f0e8; color: #1c1915; cursor: pointer; }
    #engage-panel select { padding: 6px; }
    #engage-panel .tone { font-size: 14px; }
  `;
  document.documentElement.appendChild(style);
}

function mountPanel() {
  ensureStyle();
  let panel = document.getElementById("engage-panel");
  if (!panel) {
    panel = document.createElement("div");
    panel.id = "engage-panel";
    document.documentElement.appendChild(panel);
  }
  return panel;
}

function showMemoryPanel(state) {
  const panel = mountPanel();
  panel.classList.toggle("busy", Boolean(state.busy));
  const width = state.busy ? 40 : Math.min(100, (state.posts || 0) * 25);
  const card = state.card
    ? `<p class="tone">${escapeHtml(state.card.line)}</p><p>${escapeHtml(state.card.meta)}</p>`
    : "";
  panel.innerHTML = `
    <p class="step">${escapeHtml(state.step || "")}</p>
    <h2>${escapeHtml(state.title || "")}</h2>
    <div class="bar"><div style="width:${width}%"></div></div>
    <p>${escapeHtml(state.body || "")}</p>
    ${card}
  `;
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

async function saveVisiblePosts() {
  if (pageKind(location.href) !== "profile") return;
  if (saveVisiblePosts.running) {
    saveVisiblePosts.again = true;
    return;
  }
  saveVisiblePosts.running = true;
  const page = readLinkedInPage();
  const name = page.name || "This person";
  const onPosts = /recent-activity/.test(location.pathname);
  try {
    if (!onPosts) {
      showMemoryPanel({
        step: "Step 1 of 3",
        title: name,
        body: page.bio || "Profile link saved. Open Activity, then scroll. Each post you bring on screen is saved. Engage does not open the next post.",
        posts: 0,
      });
      return;
    }
    if (!page.texts.length) {
      showMemoryPanel({
        step: "Step 2 of 3",
        title: name,
        body: "Scroll until a post is fully on screen. Then scroll to the next one. Engage does not open posts for you.",
        posts: 0,
      });
      return;
    }
    showMemoryPanel({
      step: "Step 2 of 3",
      title: "Creating memory",
      body: "Reading " + page.texts.length + " post" + (page.texts.length === 1 ? "" : "s") + " on screen for " + name + ".",
      busy: true,
    });
    let result = null;
    try {
      const response = await fetch(ENGAGE_API + "/harness", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(page),
      });
      result = await response.json();
    } catch (err) {
      showMemoryPanel({
        step: "Step 2 of 3",
        title: name,
        body: "Engage is not running. In the project folder, run: engage serve",
      });
      return;
    }
    if (!result || result.error) {
      showMemoryPanel({
        step: "Step 2 of 3",
        title: name,
        body: result && result.error ? result.error : "Could not update the memory.",
      });
      return;
    }
    showMemoryPanel({
      step: "Step 3 of 3",
      title: result.name,
      body: "Scroll to load older posts. " + (result.added || 0) + " new just now.",
      posts: result.posts,
      card: {
        line: result.one_liner || result.how || "",
        meta: result.posts + " posts in memory. Nothing is posted.",
      },
    });
  } finally {
    saveVisiblePosts.running = false;
    if (saveVisiblePosts.again) {
      saveVisiblePosts.again = false;
      scheduleSave();
    }
  }
}

function scheduleSave() {
  if (pageKind(location.href) !== "profile") return;
  clearTimeout(scheduleSave.timer);
  scheduleSave.timer = setTimeout(saveVisiblePosts, 900);
}

async function showDraftBar() {
  const panel = mountPanel();
  panel.classList.remove("busy");
  let voices = [];
  try {
    const response = await fetch(ENGAGE_API + "/memories");
    const payload = await response.json();
    voices = payload.memories || [];
  } catch (err) {
    voices = [];
  }
  const options = voices
    .map((voice) => `<option value="${escapeHtml(voice.id)}">${escapeHtml(voice.name)}</option>`)
    .join("");
  panel.innerHTML = `
    <p class="step">Open post</p>
    <h2>Write draft</h2>
    <p>Choose the voice, then the sentence goes in the comment box. You press Post.</p>
    <select id="engage-role">${options || '<option value="">No voice yet</option>'}</select>
    <button id="engage-draft" type="button">Write draft</button>
    <p id="engage-draft-status"></p>
  `;
  const button = panel.querySelector("#engage-draft");
  button.addEventListener("click", writeDraft);
}

async function writeDraft() {
  const status = document.getElementById("engage-draft-status");
  const role = document.getElementById("engage-role");
  const authorId = role ? role.value : "";
  if (!authorId) {
    status.textContent = "Build a voice on their profile first.";
    return;
  }
  const page = readLinkedInPage();
  const text = page.texts[0] || "";
  if (!text) {
    status.textContent = "Open the post so its writing is on screen, then try again.";
    return;
  }
  const panel = document.getElementById("engage-panel");
  if (panel) panel.classList.add("busy");
  status.textContent = "Writing the draft.";
  try {
    const response = await fetch(ENGAGE_API + "/draft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ author_id: authorId, text, live: true }),
    });
    const proposal = await response.json();
    if (!proposal || proposal.error) {
      status.textContent = proposal && proposal.error ? proposal.error : "Could not draft.";
      return;
    }
    if (proposal.status !== "draft" || !proposal.comment) {
      status.textContent = proposal.status === "skipped" ? "Say nothing on this post." : "This draft was refused.";
      return;
    }
    const placed = fillCommentBox(proposal.comment);
    status.textContent = placed.filled
      ? "In the comment box. You press Post. Enter was not pressed."
      : "Click Comment to open the box, then Write draft again. Enter was not pressed.";
  } catch (err) {
    status.textContent = "Engage is not running. Run: engage serve";
  } finally {
    if (panel) panel.classList.remove("busy");
  }
}

function boot() {
  const old = document.getElementById("engage-harness-banner");
  if (old) old.remove();
  const kind = pageKind(location.href);
  if (kind === "post") {
    showDraftBar();
    return;
  }
  if (kind === "profile") {
    saveVisiblePosts();
    return;
  }
  const panel = document.getElementById("engage-panel");
  if (panel) panel.remove();
}

if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.onMessage) {
  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (!message || message.type === "read") sendResponse(readLinkedInPage());
    if (message && message.type === "fill") sendResponse(fillCommentBox(message.text || ""));
    return true;
  });
}

if (typeof location !== "undefined" && /(^|\.)linkedin\.com$/.test(location.hostname)) {
  let lastUrl = "";
  const tick = () => {
    if (location.href === lastUrl) return;
    lastUrl = location.href;
    boot();
    setTimeout(boot, 1500);
  };
  tick();
  setInterval(tick, 1000);
  document.addEventListener("scroll", () => {
    if (pageKind(location.href) === "profile" && /recent-activity/.test(location.pathname)) scheduleSave();
  }, true);
}
