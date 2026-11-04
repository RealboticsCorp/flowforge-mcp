# Dossier research

## Contents
- Where each field comes from
- Researcher subagent brief
- Tech stack research
- Quality bar

## Where each field comes from

| Dossier section | Best sources, in order |
|---|---|
| Basics (legal name, DBA, address, phone, hours, website, socials) | Google Business Profile; website footer and contact page; Instagram/Facebook bio |
| Services and pricing | Website service and pricing pages; booking page (shows every service with duration and price); price lists on Instagram highlights; review mentions of prices |
| Offers, memberships, financing | Website; booking page; ads (Meta Ad Library: facebook.com/ads/library) |
| Booking and intake process | Click through the online booking flow without completing it: which software, deposit, cancellation policy, intake forms, consultation required? |
| Ownership and legal entity | State business registry (e.g. California: bizfileonline.sos.ca.gov; other states: "<state> secretary of state business search"); About page; press; LinkedIn |
| Management and clinical staff | Team or About page; LinkedIn; licensing boards for clinical roles (e.g. California Medical Board / Board of Registered Nursing lookups) to confirm a medical director or injector is licensed |
| Front desk / staff mentioned by customers | Names that recur in reviews (good and bad); team page |
| Size and footprint | Number of locations; staff count on team page or LinkedIn; years in business (registry filing date, "since" on site) |
| Reputation | Google rating and count; Yelp; industry sites (RealSelf, Healthgrades, Zocdoc, Vagaro/Booksy listing ratings); BBB; owner reply behaviour |
| Phone experience | What reviews say about calls, voicemail, call-backs, booking by phone; whether the website pushes online booking over calling; after-hours handling |
| Tech stack | See § Tech stack research |
| Marketing and positioning | Homepage headline, target customer, price tier, awards, influencer or celebrity tie-ins, ad activity |

Do not call the business, book, submit forms or create accounts. Reading public pages and walking a booking flow up to (not past) the point of entering personal details is fine.

## Researcher subagent brief

Spawn one subagent per confirmed business, **all in one message so they run in parallel**, each with this brief and the brackets filled in. Each subagent owns its business end to end: reviews, research, review analysis and the finished dossier. Give each one the full paths of the templates and output files.

> Research [business name], [address, website, phone, Google rating and count], a [industry] business in [city], and write its complete dossier. We are designing an AI [role] for businesses like this one, so pay extra attention to anything about phones, booking, front desk, communication and customer experience. Other subagents are researching other businesses at the same time; touch only this business's files.
>
> Read `[skill-dir]/references/dossier-research.md` for where to find each field, and fill `[skill-dir]/assets/dossier-template.md` completely, section 7 included. Write it to `[project]/research/dossiers/[slug].md`. Industry context: `[project]/research/tech-stack.md` (may still be in progress).
>
> 1. **Reviews.** [Browser: "Open your own browser tab with the new-tab tool and pass its tab ID on every browser call; never navigate a tab you didn't open. Collect Google reviews following `[skill-dir]/references/review-collection.md` § Browser method." OR Outscraper: "Collect Google reviews with `[skill-dir]/scripts/fetch_reviews_outscraper.py` following `review-collection.md` § Collecting with Outscraper."] Write them to `[project]/research/reviews/[slug].md`. Then search Yelp, [industry review site, e.g. RealSelf] and other review sites and append notable reviews under a heading per site, especially complaints and anything about phones, booking or reception.
> 2. **Research** every other dossier section from the sources in the table above. Do the web research while slow browser steps are loading; don't wait idle.
> 3. **Review analysis (section 7).** Read every review you collected. Cluster into themes: up to 10 praise themes and up to 5 criticism themes, ranked by share of the sample (N of total and %), with 1-3 short real quotes each (★ and first name or initial). Analyse every review of 3★ or below closely, including any owner reply and what it shows about how complaints are handled. If low-rated reviews are scarce, say so plainly and mine mild friction inside positive reviews ("a bit of a wait", "hard to get an appointment"), labelled as such. Never invent complaints. List every front-desk, phone, booking or follow-up mention. Copy Google's topic chips at the top, and end with a "Sample note:" on sample size and limits.
> 4. **Section 10 (Implications)** last, built on sections 4, 7 and 8.
>
> Rules: cite a source URL for every fact. Tag each claim [verified] (you saw it at the source) or [inferred] (reasoned from evidence, say from what). When a field isn't found, write "Not found (searched: …)". Record people only in their business role, by first name or initial for reviewers; no home addresses, personal phone numbers or family details. Don't contact the business, book, sign in, or submit any form.
>
> Return a 5-line summary: rating and review sample, top 3 praises, top complaints (or "none found"), booking and phone setup, anything surprising.

## Tech stack research

The agent spec ranks apps per integration, and those rankings must reflect what **this industry** actually uses. Do it in two passes and write `research/tech-stack.md` from `assets/tech-stack-template.md`.

**Pass 1: what the confirmed businesses use (strongest evidence).**
- Booking links and widgets: the domain a "Book now" button goes to (e.g. a vendor's hosted booking domain) names the software.
- Page source: script and iframe URLs. Fetch the page and search the HTML for vendor names, or use the browser's page reading.
- Forms, patient portals, review-request emails mentioned in reviews, payment and financing badges, chat widgets, phone and SMS systems.
- Job postings for the business ("experience with [software] preferred") on Indeed or LinkedIn.

**Pass 2: what the industry uses (breadth).**
- Search "[industry] software", "best [industry] booking software [year]", "[industry] practice management market share", industry association surveys, and vendor customer counts.
- Search the industry's subreddit or forums: "what software do you use for [industry]".
- For each integration category the role needs (booking or practice management, calendar, CRM or marketing, SMS, payments or memberships, phone system, reviews), list the 3-5 leading products. Rank them with a short reason and evidence (seen at N of the confirmed businesses; survey share; vendor claims, marked as such).

Check whether each leading product has an API or a webhook/Zapier/Make integration, because a product the agent cannot connect to can only be "add on demand" no matter how popular it is. Note the evidence (developer docs URL).

## Quality bar

A dossier is done when someone could prepare a sales call from it without opening a browser: every template section is filled or explicitly not found, prices are real numbers with sources, the reviews section has real quotes, and the "Implications for the [role]" section says something specific to this business, not generic advice.
