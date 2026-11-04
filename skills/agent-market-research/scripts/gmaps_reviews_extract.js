// Google Maps review extractor, run inside an open place page (browser JavaScript tool).
// Set SORT and TARGET on the first two lines, paste the whole file as the script, and it
// returns JSON: { sort, loaded, topics, reviews: [{ stars, date, author, text, ownerReply }] }.
// Tested 2026-11-04. If `loaded` is far below TARGET and the listing has more reviews, run it
// again. Google's class names change; if `loaded` stays 0, read the reviews with the
// page-text tool instead and tell the user the extractor needs updating.
const SORT = "Newest";      // "Most relevant" | "Newest" | "Highest rating" | "Lowest rating"
const TARGET = 50;          // stop once this many reviews are loaded

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const labelOf = (el) => el.getAttribute("aria-label") || el.innerText || "";

const reviewsTab = [...document.querySelectorAll("[role=tab]")].find((t) => labelOf(t).startsWith("Reviews"));
if (reviewsTab) { reviewsTab.click(); await sleep(3000); }

const sortButton = [...document.querySelectorAll("button")].find((b) => /sort/i.test(labelOf(b)));
if (sortButton) {
  sortButton.click(); await sleep(1500);
  const option = [...document.querySelectorAll("[role=menuitemradio]")].find((m) => m.innerText.trim() === SORT);
  if (option) { option.click(); await sleep(3000); }
}

// Reviews render only once their panel is scrolled, so find the scroll container that
// holds the Sort button rather than waiting for review cards to appear.
const cards = () => document.querySelectorAll("div.jftiEf");
const scrollable = (el) => el && el.scrollHeight > el.clientHeight + 50 && /(auto|scroll)/.test(getComputedStyle(el).overflowY);
let panel = sortButton;
while (panel && !scrollable(panel)) panel = panel.parentElement;

// The first run on a freshly opened page often stalls while the panel is still loading,
// so wait for the first review cards before scrolling, and allow a few slow loads.
for (let i = 0; i < 10 && panel && cards().length === 0; i++) { panel.scrollTop = panel.scrollHeight; await sleep(1000); }

let stalled = 0;
while (panel && cards().length < TARGET && stalled < 6) {
  const before = cards().length;
  panel.scrollTop = panel.scrollHeight;
  await sleep(1500);
  stalled = cards().length === before ? stalled + 1 : 0;
}

// Google's own topic chips ("efficient staff 12") are a free theme signal.
const topics = [...document.querySelectorAll("button[role=radio]")]
  .map((b) => labelOf(b).replace(/\s+/g, " ").trim())
  .filter((t) => t && !/^all\b/i.test(t));

document.querySelectorAll("button.w8nwRe").forEach((b) => b.click()); // expand "More"
await sleep(800);

const reviews = [...cards()].slice(0, TARGET).map((card) => ({
  stars: parseInt(card.querySelector(".kvMYJc")?.getAttribute("aria-label") || "", 10) || null,
  date: card.querySelector(".rsqaWe")?.innerText || "",
  author: card.querySelector(".d4r55")?.innerText || "",
  text: (card.querySelector(".wiI7pd")?.innerText || "").replace(/\s+/g, " ").trim(),
  ownerReply: (card.querySelector(".CDe7pd")?.innerText || "").replace(/\s+/g, " ").trim().slice(0, 400),
}));

({ sort: SORT, loaded: reviews.length, topics, reviews });
