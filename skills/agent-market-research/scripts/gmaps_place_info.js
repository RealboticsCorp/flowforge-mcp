// Google Maps place details, run inside an open place page (browser JavaScript tool).
// Waits for the side panel to load, then returns
// { name, rating, reviewCount, category, address, website, phone, url }.
// Used in Stage 1 to confirm each business and in the dossier for the Google basics.
// If `name` comes back empty, the panel never loaded: click the red map pin or reload,
// then run it again.
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
for (let i = 0; i < 15 && !document.querySelector("div.F7nice"); i++) await sleep(1000);

const q = (s) => document.querySelector(s);
const label = (s) => (q(s)?.getAttribute("aria-label") || "").replace(/^[^:]+:\s*/, "").trim();
const [rating, count] = (q("div.F7nice")?.innerText || "").split("\n");

({
  name: q("h1")?.innerText || "",
  rating: rating || "",
  reviewCount: (count || "").replace(/[()]/g, ""),
  category: q("button.DkEaL")?.innerText || "",
  address: label('button[data-item-id="address"]'),
  website: q('a[data-item-id="authority"]')?.href || "",
  phone: label('button[data-item-id^="phone"]'),
  url: location.href.split("?")[0],
});
