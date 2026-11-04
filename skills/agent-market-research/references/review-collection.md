# Review collection

The review analysis drives the whole playbook, so the goal is a sample that is **large enough and not biased toward happy customers**. Google sorts by "Most relevant" by default, which over-represents glowing reviews. Always collect across sort orders.

## How much to collect

Per business, aim for:

- the **50 newest** reviews (what the experience is like now),
- **all 1-3 star reviews up to about 40** (where the complaints are),
- the **top 20 "most relevant"** (what Google thinks represents the business).

Deduplicate by reviewer name and date. Fewer than 30 reviews in total is a weak signal: say so in the dossier and lean more on other sites.

Record each review in `research/reviews/<business>.md` as one line: `- ★N | YYYY-MM | reviewer first name or initials | text (trimmed to ~400 chars) | owner replied: yes/no`. Keep the owner's reply when it shows how the business handles complaints; that is useful playbook evidence.

## Browser method (default)

Use whatever browser tool the session has: the built-in browser pane, Claude in Chrome, or Playwright. Text tools (`get_page_text`, `read_page`) beat screenshots for reading reviews.

1. Open `https://www.google.com/maps/search/<business name> <street address> <city>`. With the address included, Maps usually opens the place page directly; otherwise pick the matching listing. Wait about 5 seconds for the side panel to load (the page heading shows the business name), and check the address matches.
2. Note the headline rating and total review count.
3. **With a JavaScript tool (fastest):** run `scripts/gmaps_reviews_extract.js` in the page three times, editing its first two lines each time: `"Newest"`/50, `"Lowest rating"`/40, `"Most relevant"`/20. It opens the Reviews tab, sorts, scrolls the review panel, expands the cut-off reviews, and returns structured JSON plus Google's topic chips ("efficient staff, mentioned in 12 reviews"). Those chips are a free theme signal; copy them into the reviews file. The Lowest-rating run continues into higher ratings once the low ones run out, so keep only reviews of 3 stars or fewer from it. Tested November 2026: about 15 seconds per run.
4. **Without a JavaScript tool:** click the **Reviews** tab, use **Sort** to choose each order, scroll inside the review panel (not the page) to load more (about 10 per scroll), click each **More** to expand long reviews, and read the panel with the page-text tool.
5. Write the deduplicated reviews to the reviews file.

If the script returns `loaded: 0`, Google has likely changed its page; fall back to step 4 and tell the user the extractor needs updating.

Google may show a consent or sign-in prompt. Decline cookies that aren't essential and carry on without signing in. If the panel stops loading or Google blocks the session, stop, use what you have, note the shortfall in the dossier, and offer the paid service.

Doing this in each research subagent works, but several subagents driving one shared browser pane collide. When the browser is a single shared pane, collect reviews for the businesses one after another in the main session, or in one dedicated subagent, before or alongside the dossier subagents.

## Outscraper setup (paid option)

Outscraper's Google Maps Reviews service is pay as you go. The first 500 reviews each month are free, then about $3 per 1,000 (prices checked November 2026 on outscraper.com/pricing; check again if they look off). A typical project of 4 businesses × ~110 reviews costs nothing to about $1.50. API access needs a payment method on file.

Walk the user through this exactly. One step per message, and wait for "done" before the next. Assume they have never used an API key.

1. **Make an account.** "Go to https://outscraper.com and click **Sign Up**. Signing up with Google is quickest. Tell me when you're logged in and see the dashboard."
2. **Add a payment method.** "In the left menu click **Billing** (or **Profile → Billing**). Add a card. You can add prepaid credits, which never expire ($10 is plenty to start), or connect a card that is only charged for what you use above the free 500 a month. Tell me when that's done."
3. **Get your API key.** "Click **Profile** (top right), then **API Key**, then **Generate** if no key is shown. Click the copy icon next to the key. Don't paste it here yet."
4. **Save the key privately.** Give them this to paste into Terminal (on Mac: press Cmd+Space, type Terminal, press Enter). It asks for the key without showing it on screen:

   ```bash
   mkdir -p ~/.config/agent-market-research && printf 'Paste your Outscraper API key and press Enter: ' && read -rs k && printf '%s' "$k" > ~/.config/agent-market-research/outscraper.key && chmod 600 ~/.config/agent-market-research/outscraper.key && echo && echo "Saved."
   ```

   What they should see: `Saved.` If they'd rather paste the key in chat, accept it, write it to that file with `chmod 600` yourself, and never repeat it back.
5. **Test it.** Run the script below on one confirmed business with a small limit, and show the user how many reviews came back:

   ```bash
   python3 <skill-dir>/scripts/fetch_reviews_outscraper.py "<business name>, <full address>" --limit 10 --sort newest
   ```

   If it reports an auth error, the key was mistyped: repeat step 4. If it reports a payment or plan error, the card or credits from step 2 are missing.
6. Record `reviews=outscraper` in `~/.config/agent-market-research/config`. Tell the user it's set up for every future project.

### Collecting with Outscraper

Run the script three times per business, matching the browser sample: `--sort newest --limit 50`, `--sort lowest_rating --limit 40` and `--sort most_relevant --limit 20`. Pass `--out` to write JSON, then convert to the review-line format above. Use the full address in the query so it matches the right location. A Google Place ID is better when you have one.

Never print, log, or commit the key. The script reads it from the file or from `OUTSCRAPER_API_KEY`.
