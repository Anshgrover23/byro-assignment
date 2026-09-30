const API = "http://127.0.0.1:8787";

const SKIP = {
  sensitive: "This post is sensitive. Say nothing.",
  injection: "This post tries to instruct the tool. Say nothing.",
  off_goal: "This topic is outside their goal. Say nothing.",
  prohibited_claim: "This post pushes a claim they do not make. Say nothing.",
  repeats_point: "This repeats a point they already made. Say nothing.",
};

let pendingCard = null;
let pendingProposal = null;

document.addEventListener("DOMContentLoaded", init);
document.getElementById("read").addEventListener("click", onRead);
document.getElementById("save").addEventListener("click", onSave);
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
  const url = tab && tab.url ? tab.url : "";
  if (!url.includes("linkedin.com")) {
    setStatus("Open a LinkedIn profile or a post, then click Engage again.");
    return;
  }
  document.getElementById("actions").hidden = false;
  const onProfile = /linkedin\.com\/in\//i.test(url);
  document.getElementById("read").hidden = !onProfile;
  document.getElementById("read-hint").hidden = !onProfile;
  setStatus(onProfile ? "Read the posts that are visible, then save only if the card looks right." : "Pick a saved voice and draft from the longest post on screen.");
  await loadVoices();
}

async function onRead() {
  setBusy(true);
  try {
    const page = await readTab();
    if (!page || !page.texts || page.texts.length === 0) {
      setStatus("No posts were visible. Scroll until their writing is on screen, then read again.");
      return;
    }
    const result = await postJson("/capture", page);
    if (!result || result.error) {
      setStatus(result && result.error ? result.error : "The server refused this page.");
      return;
    }
    pendingCard = result.card;
    renderCapture(result);
    setStatus("Nothing is saved yet.");
  } catch (err) {
    setStatus("Could not read this tab. Stay on LinkedIn and try again.");
  } finally {
    setBusy(false);
  }
}

async function onSave() {
  if (!pendingCard) return;
  setBusy(true);
  try {
    const result = await postJson("/voices/save", { card: pendingCard });
    if (!result || result.error) {
      setStatus(result && result.error ? result.error : "Could not save this voice.");
      return;
    }
    setStatus("Saved for " + result.name + ". Open a post and draft as them.");
    document.getElementById("capture").hidden = true;
    await loadVoices();
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

function renderCapture(result) {
  const card = result.card;
  document.getElementById("capture").hidden = false;
  document.getElementById("capture-name").textContent = card.name;
  const list = document.getElementById("observations");
  list.replaceChildren();
  for (const item of result.summary.observations) {
    const li = document.createElement("li");
    li.textContent = item;
    list.appendChild(li);
  }
  const examples = document.getElementById("examples");
  examples.replaceChildren();
  for (const example of result.summary.voice_examples) {
    const p = document.createElement("p");
    p.textContent = example;
    examples.appendChild(p);
  }
  const claims = card.allowed_claims || [];
  document.getElementById("claims-note").textContent = claims.length
    ? "Allowed claims stay as they already are. This page does not add new ones."
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

async function loadVoices() {
  const payload = await getJson("/voices");
  const voices = payload && payload.voices ? payload.voices : [];
  const select = document.getElementById("voice");
  select.replaceChildren();
  for (const voice of voices) {
    const option = document.createElement("option");
    option.value = voice.id;
    option.textContent = voice.name;
    select.appendChild(option);
  }
  const ready = voices.length > 0;
  document.getElementById("voice-field").hidden = !ready;
  document.getElementById("live-field").hidden = !ready;
  document.getElementById("draft").hidden = !ready;
}

async function readTab() {
  const tab = await currentTab();
  if (!tab || !tab.id) throw new Error("no tab");
  const [injected] = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: readLinkedInPage,
  });
  return injected ? injected.result : null;
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
