const API = "http://127.0.0.1:8787";

const SKIP = {
  sensitive: "This post is sensitive. Say nothing.",
  injection: "This post tries to instruct the tool. Say nothing.",
  off_goal: "This topic is outside their goal. Say nothing.",
  prohibited_claim: "This post pushes a claim they do not make. Say nothing.",
  repeats_point: "This repeats a point they already made. Say nothing.",
};

let pendingProposal = null;
let pageKindNow = "other";

document.addEventListener("DOMContentLoaded", init);
document.getElementById("nav-start").addEventListener("click", () => showStart());
document.getElementById("nav-settings").addEventListener("click", () => showSettings());
document.getElementById("go-comment").addEventListener("click", () => showComment());
document.getElementById("read").addEventListener("click", onRead);
document.getElementById("draft").addEventListener("click", onDraft);
document.getElementById("keep").addEventListener("click", () => review("accept"));
document.getElementById("change").addEventListener("click", showEdit);
document.getElementById("drop").addEventListener("click", () => review("reject"));
document.getElementById("save-edit").addEventListener("click", () => review("edit"));

async function init() {
  const health = await getJson("/health");
  if (!health || !health.ok) {
    setStatus("Start the local server, then open this again: engage serve");
    return;
  }
  const tab = await currentTab();
  const url = await pageHref(tab);
  if (!url.includes("linkedin.com")) {
    setStatus("Open a LinkedIn profile or a post, then click Engage again.");
    return;
  }
  pageKindNow = pageKind(url);
  document.getElementById("go-comment").hidden = pageKindNow !== "post";
  showStart(pageKindNow);
}

function showStart(kind) {
  const current = kind || pageKindNow;
  document.getElementById("title").textContent = "Start";
  document.getElementById("start").hidden = false;
  document.getElementById("settings").hidden = true;
  document.getElementById("actions").hidden = true;
  document.getElementById("capture").hidden = true;
  document.getElementById("result").hidden = true;
  document.getElementById("nav-start").setAttribute("aria-current", "page");
  document.getElementById("nav-settings").removeAttribute("aria-current");
  if (current === "profile") {
    setStatus("You are on a profile. Open Activity and scroll. The panel on the page saves each post.");
  } else if (current === "post") {
    setStatus("A post is open. Build a voice first, or write a comment if one is already saved.");
  } else {
    setStatus("Open a LinkedIn profile to begin.");
  }
}

async function showSettings() {
  document.getElementById("title").textContent = "Settings";
  document.getElementById("start").hidden = true;
  document.getElementById("settings").hidden = false;
  document.getElementById("actions").hidden = true;
  document.getElementById("capture").hidden = true;
  document.getElementById("result").hidden = true;
  document.getElementById("nav-settings").setAttribute("aria-current", "page");
  document.getElementById("nav-start").removeAttribute("aria-current");
  setStatus("Voices recorded on this machine.");
  const list = document.getElementById("memory-list");
  const payload = await getJson("/memories");
  const memories = payload && payload.memories ? payload.memories : [];
  list.replaceChildren();
  if (!memories.length) {
    const empty = document.createElement("p");
    empty.textContent = "No voices recorded yet. Start on a profile.";
    list.appendChild(empty);
    return;
  }
  for (const memory of memories) {
    const article = document.createElement("article");
    const name = document.createElement("h2");
    name.textContent = memory.name;
    const line = document.createElement("p");
    line.textContent = memory.one_liner || memory.posts + " posts";
    const meta = document.createElement("p");
    meta.className = "hint";
    meta.textContent = memory.posts + " posts";
    article.append(name, line, meta);
    list.appendChild(article);
  }
}

async function showComment() {
  document.getElementById("title").textContent = "Comment in their voice";
  document.getElementById("start").hidden = true;
  document.getElementById("settings").hidden = true;
  document.getElementById("actions").hidden = false;
  document.getElementById("nav-start").removeAttribute("aria-current");
  document.getElementById("nav-settings").removeAttribute("aria-current");
  setStatus("Pick a voice. The draft goes in the comment box. You press Post.");
  const tab = await currentTab();
  const url = await pageHref(tab);
  await loadVoices(pageKind(url));
}

async function onRead() {
  setBusy(true);
  try {
    const page = await readTab();
    if (!page || !page.texts || page.texts.length === 0) {
      setStatus("No post text was on screen. Scroll until the writing is visible, then try again.");
      return;
    }
    const result = await postJson("/harness", page);
    if (!result || result.error) {
      setStatus(result && result.error ? result.error : "The server refused this page.");
      return;
    }
    renderMemory(result);
    setStatus(result.unchanged ? "Voice for " + result.name + " is already up to date." : "Voice memory updated for " + result.name + ".");
    await loadVoices(pageKind((await currentTab()).url || ""));
  } catch (err) {
    setStatus("Could not read this tab. Stay on LinkedIn and try again.");
  } finally {
    setBusy(false);
  }
}

async function onDraft() {
  const authorId = document.getElementById("voice").value;
  if (!authorId) {
    setStatus("Save a voice first.");
    return;
  }
  setBusy(true);
  try {
    const page = await readTab();
    const text = page && page.texts ? page.texts[0] : "";
    if (!text) {
      setStatus("No post was visible. Open the post so its text is on screen.");
      return;
    }
    const proposal = await postJson("/draft", {
      author_id: authorId,
      text,
      live: document.getElementById("live").checked,
    });
    if (!proposal || proposal.error) {
      setStatus(proposal && proposal.error ? proposal.error : "Could not draft.");
      return;
    }
    pendingProposal = proposal;
    renderProposal(proposal);
    if (proposal.status === "draft" && proposal.comment) {
      const placed = await placeInBox(proposal.comment);
      if (placed && placed.filled) {
        setStatus("In the comment box. You press Post. Enter was not pressed.");
      } else {
        setStatus("Click Comment to open the box, then draft again. Enter was not pressed.");
      }
    }
  } catch (err) {
    setStatus("Could not read this tab. Stay on LinkedIn and try again.");
  } finally {
    setBusy(false);
  }
}

async function review(action) {
  if (!pendingProposal) return;
  const body = { proposal_id: pendingProposal.id, action };
  if (action === "edit") {
    body.text = document.getElementById("edit-text").value;
    body.rule = document.getElementById("edit-rule").value;
  }
  if (action === "reject") {
    body.rule = document.getElementById("edit-rule").value;
  }
  setBusy(true);
  try {
    const result = await postJson("/review", body);
    if (!result || result.error) {
      setStatus(result && result.error ? result.error : "Could not record that.");
      return;
    }
    document.getElementById("review").hidden = true;
    if (result.handoff) {
      setStatus("Ready to paste. Nothing was posted.");
      document.getElementById("result-body").textContent = result.handoff.text;
    } else if (action === "reject") {
      setStatus("Draft dropped. Nothing to paste.");
    } else {
      setStatus("Recorded.");
    }
  } finally {
    setBusy(false);
  }
}

function showEdit() {
  document.getElementById("edit-box").hidden = false;
  if (pendingProposal && pendingProposal.comment) {
    document.getElementById("edit-text").value = pendingProposal.comment;
  }
}

function renderMemory(result) {
  document.getElementById("capture").hidden = false;
  document.getElementById("capture-name").textContent = result.name;
  const list = document.getElementById("observations");
  list.replaceChildren();
  for (const item of [result.posts + " posts in memory", result.added + " new this time"]) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
  const examples = document.getElementById("examples");
  examples.replaceChildren();
  if (result.how) {
    const p = document.createElement("p");
    p.textContent = result.how;
    examples.appendChild(p);
  }
  document.getElementById("memory-note").textContent = result.claims
    ? "Allowed claims stay as they already are. The memory is style only."
    : "This voice has no allowed claims yet. A model draft will be refused until you add one.";
}

function renderProposal(proposal) {
  const section = document.getElementById("result");
  section.hidden = false;
  const title = document.getElementById("result-title");
  const body = document.getElementById("result-body");
  const reviewBox = document.getElementById("review");
  document.getElementById("edit-box").hidden = true;
  if (proposal.status === "skipped") {
    title.textContent = "Say nothing";
    body.textContent = SKIP[proposal.reason] || proposal.reason;
    reviewBox.hidden = true;
    setStatus("No draft was written.");
    return;
  }
  if (proposal.status === "blocked") {
    title.textContent = "Draft refused";
    body.textContent = proposal.comment || proposal.reason;
    reviewBox.hidden = false;
    setStatus("Write your own sentence, or drop it.");
    return;
  }
  title.textContent = "Draft";
  body.textContent = proposal.comment || "";
  reviewBox.hidden = false;
  setStatus("Keep it, change it, or drop it. Nothing is posted.");
}

async function loadVoices(kind) {
  const payload = await getJson("/memories");
  const voices = payload && payload.memories ? payload.memories : [];
  const select = document.getElementById("voice");
  select.replaceChildren();
  for (const voice of voices) {
    const option = document.createElement("option");
    option.value = voice.id;
    option.textContent = voice.name;
    select.appendChild(option);
  }
  const ready = voices.length > 0 && kind === "post";
  document.getElementById("voice-field").hidden = !ready;
  document.getElementById("live-field").hidden = !ready;
  document.getElementById("draft").hidden = !ready;
}

async function placeInBox(text) {
  const tab = await currentTab();
  if (!tab || !tab.id) return { filled: false };
  return chrome.tabs.sendMessage(tab.id, { type: "fill", text });
}

async function pageHref(tab) {
  if (!tab || !tab.id) return "";
  try {
    const [injected] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => location.href,
    });
    if (injected && typeof injected.result === "string" && injected.result) return injected.result;
  } catch (err) {
    return tab.url || "";
  }
  return tab.url || "";
}

async function readTab() {
  const tab = await currentTab();
  if (!tab || !tab.id) throw new Error("no tab");
  return chrome.tabs.sendMessage(tab.id, { type: "read" });
}

async function currentTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function getJson(path) {
  try {
    const response = await fetch(API + path);
    return await response.json();
  } catch (err) {
    return null;
  }
}

async function postJson(path, body) {
  const response = await fetch(API + path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return response.json();
}

function setStatus(text) {
  document.getElementById("status").textContent = text;
}

function setBusy(busy) {
  for (const button of document.querySelectorAll("button")) {
    button.disabled = busy;
  }
}
