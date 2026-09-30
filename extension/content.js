function readLinkedInPage() {
  function cleaned(node) {
    return (node.innerText || "").replace(/\s+/g, " ").trim();
  }

  function looksLikeChrome(text) {
    const lowered = text.toLowerCase();
    const junk = [
      "messaging",
      "notifications",
      "try premium",
      "people you may know",
      "who your viewers also viewed",
      "advertise",
    ];
    return junk.some((item) => lowered.includes(item) && text.length < 90);
  }

  const nameNode = document.querySelector("h1");
  const name = nameNode ? cleaned(nameNode) : "";
  const selectors = [
    ".update-components-text",
    ".feed-shared-inline-show-more-text",
    ".break-words",
    "span[dir='ltr']",
  ];
  const seen = new Set();
  const texts = [];
  for (const selector of selectors) {
    for (const node of document.querySelectorAll(selector)) {
      const text = cleaned(node);
      if (text.length < 40 || text.length > 1200) continue;
      const key = text.toLowerCase();
      if (seen.has(key) || looksLikeChrome(text)) continue;
      seen.add(key);
      texts.push(text.slice(0, 600));
    }
  }
  texts.sort((a, b) => b.length - a.length);
  return {
    name,
    profile_url: location.href,
    texts: texts.slice(0, 12),
  };
}
