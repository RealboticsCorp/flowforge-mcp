---
name: agent-market-research
description: Guided market research that ends in an AI voice agent demo. Walks the user step by step, asking every question, from industry, city and role to target businesses, full dossiers (services, pricing, owners, staff, tech stack, review analysis), a review-based role playbook, and an approved agent spec with ranked industry apps per integration. Then it hands off to goal-based-voice-agent to build a FlowForge demo. Use whenever the user wants market research to build an agent, even vaguely ("I want to do some market research", "help me find a niche for an AI agent"), types /agent-market-research with nothing else, wants business dossiers or competitor review analysis for a role, wants to know which apps a vertical uses, or wants to spec or demo an AI receptionist, concierge, intake or scheduling agent for a new industry. Use it even if they don't name the skill or know how it works.
---

# Agent Market Research

Turns "industry + city + role" into evidence-backed research and an approved spec for an AI voice agent, then hands the spec to `goal-based-voice-agent` to build a demo in FlowForge. The user runs this once per industry and city, often several times, to compare verticals before choosing where to sell. So every output is a Markdown file in a predictable folder, not an artifact or chat text, and every claim cites a source.

The user is often a non-technical agency owner. Write to them in plain English, give one clear question at a time at the gates, and never make them do setup you could do for them.

## You drive the process

Assume the user knows nothing about how this skill works. They may have typed only `/agent-market-research`, or said something as loose as "I want to do some market research to build an agent". Either way, you lead from the first message to the finished demo:

- **Open by explaining and asking.** If the user gave no details, reply with a short welcome that says in 3-4 lines what's about to happen (find example businesses, research them, turn their reviews into a job playbook, design the AI agent, build a demo they can call), then ask the first intake question. Example:

  > Let's research a market and design an AI voice agent for it. Here's how it works: we pick an industry and a city, I find 3-4 real businesses there and research them in depth, including what their customers praise and complain about, then I design an AI employee that does one job better than they do and build a demo you can call. I'll ask you a few quick questions as we go. First: what type of business do you want to target? (e.g. med spas, dental offices, law firms, HVAC companies)

- **Ask, don't wait.** Collect intake answers one or two questions at a time, offering examples or suggestions with every question so the user is never stuck on a blank prompt. If the user already gave some answers, acknowledge them and ask only for what's missing.
- **Move forward on your own.** When a stage finishes, say in one line what was done and where it's saved, then start the next stage in the same turn. Only the two gates (confirming businesses, approving the spec) and the one-time review-method choice pause for the user, and each of those ends with a single clear question.
- **Never end a turn without a next step.** Every message either asks the user exactly one question, or says what you're doing next and does it. The user should never have to say "next" or know what stage comes after.
- **Report progress during long work.** Dossier research takes a while; tell the user roughly how long, and give a one-line update as each business finishes.

## The stages

| # | Stage | Output | Gate |
|---|-------|--------|------|
| 0 | Intake | `STATUS.md` | |
| 1 | Find and confirm target businesses | `research/targets.md` | **User confirms 3-4 businesses** |
| 2 | Choose how to collect reviews | method recorded in `STATUS.md` | user picks (asked once) |
| 3 | Dossiers (parallel) | `research/dossiers/*.md`, `research/reviews/*.md` | |
| 4 | Review synthesis + role playbook | `research/review-themes.md`, `roles/<role>/playbook.md` | |
| 5 | Agent spec | `roles/<role>/agent-spec.md` | **User approves the spec** |
| 6 | Handoff to build + iterate | `roles/<role>/build/` | user tests the demo |

Stop at each gate and wait. The gates exist because the expensive work (dossiers, the build) is wasted if the target or the design is wrong.

**Resuming.** If the user names an existing project ("continue med spas LA", "iterate the receptionist"), read its `STATUS.md` first and pick up at the recorded stage. Never redo a finished stage unless asked.

## Folder layout

Projects live under a research root. On the first ever run, ask once where to keep them (suggest `~/AgentResearch`), then save it as `root=` in `~/.config/agent-market-research/config` and reuse it silently. Folder names are lowercase-hyphenated.

```
<root>/
└── <industry>/                     e.g. med-spas/
    └── <city>/                     e.g. los-angeles/
        ├── STATUS.md               stage, decisions, links to every file
        ├── research/               role-independent: reusable for any role
        │   ├── targets.md          candidates found, why, which were confirmed
        │   ├── dossiers/<business>.md
        │   ├── reviews/<business>.md   raw review extract used for analysis
        │   ├── tech-stack.md       software these businesses and the industry use
        │   └── review-themes.md    praises/complaints pooled across businesses
        └── roles/
            └── <role>/             e.g. receptionist-concierge/
                ├── playbook.md
                ├── agent-spec.md   the handoff contract for the build
                └── build/          prompt, config, build log, change log
```

Research is split from roles on purpose: a second role in the same city ("now do an after-hours nurse line") reuses the dossiers and only adds a new `roles/` folder. Templates for every file are in `assets/`; copy and fill them rather than inventing structure, so projects stay comparable across industries.

## Stage 0: Intake

Ask for these in order, skipping any the user already gave:

1. **Industry or business type.** Offer examples.
2. **City or area.** Ask how wide: one city, a metro area, or specific neighbourhoods.
3. **The role the AI agent will fill.** Suggest the 2-3 most common phone-facing roles for that industry (e.g. for med spas: front desk receptionist and concierge, new-client consultation booker, after-hours line) and let them pick or describe their own.
4. **Example businesses.** "Do you already have 3-4 businesses in mind that are exactly the kind you want to sell to? If not, no problem, I'll find some." Names or website links are enough.
5. **Where to save** (first ever run only): suggest `~/AgentResearch` and accept a plain yes.

Then create the project folders and `STATUS.md` from `assets/status-template.md`, tell the user the folder path, and go straight into Stage 1.

## Stage 1: Find and confirm target businesses

The user needs 3-4 businesses that are dead on target for their ideal customer. Researching the wrong kind of business is the most expensive mistake this skill can make, so confirm before any dossier work.

- **User gave 3+ businesses:** look each up quickly (website, Google listing) to confirm it exists and is in the area, show the short table below, and ask "Are these right?" in one line.
- **User gave fewer than 3, or none:** search Google (web search, Google Maps) for the industry in that area and collect 5-6 candidates, filling the gap around whatever the user gave. Prefer independent or small multi-location businesses with an active website and a healthy number of Google reviews (roughly 50+), because thin review counts make weak playbooks. Note chains and franchises as such; they are often a different buyer.

Show the candidates as a table: name, neighbourhood, website, Google rating and review count, a one-line "why it fits", and anything that might make it off-target. Then ask one question: **"Are these the right type of business, and which 3-4 should we focus on?"** If the user corrects the target ("smaller, single-location"), write that correction into `targets.md` as an ICP note and search again. Repeat until at least 3 are confirmed. Record candidates, the ICP notes and the confirmed list in `research/targets.md` (`assets/targets-template.md`).

## Stage 2: Choose how to collect reviews

Ask once per user, not per project, then remember the answer as `reviews=` in the config file:

> I'll read each business's Google reviews myself in the browser. That's free, just slower (a few minutes per business). If you plan to research many industries, a paid review service is faster and more complete. It costs about 3 US dollars per 1,000 reviews after 500 free a month, and I'll walk you through setting it up step by step. Which would you like?

- **Browser (default and recommended for most):** read `references/review-collection.md` § Browser method.
- **Paid service:** read `references/review-collection.md` § Outscraper setup and walk the user through it exactly as written. Test it on one confirmed business before relying on it. If setup stalls, fall back to the browser without fuss.

Google is the primary source either way; Yelp and industry review sites (e.g. RealSelf for aesthetics, Healthgrades for medical) are added in Stage 3 when they exist.

## Stage 3: Dossiers

**One subagent per business, all running in parallel.** Each confirmed business gets its own research subagent that owns everything about that business from start to finish: collecting its reviews, researching the dossier, analysing the reviews, and writing the finished dossier. Spawn all of them in a single message so they run at the same time; never research businesses one after another, and never split one business's work across a serial queue. This is the slowest stage, and running in parallel turns 4 × the work into roughly 1 × the wait. It also keeps each business's page dumps out of the main context.

Read `references/dossier-research.md` for the subagent brief and fill it in once per business. Each subagent writes:
- `research/reviews/<business>.md`: the raw reviews (Google first, then other sites);
- `research/dossiers/<business>.md`: the full dossier from `assets/dossier-template.md`, including section 7, Review analysis.

**Browser access for parallel review collection.** Each subagent opens its **own browser tab** (the browser's new-tab tool) and passes that tab's ID on every browser call, so several subagents can read Google Maps at once without clicking on each other's pages. If the browser tools can't open separate tabs, or parallel tabs stall, use the paid review service if it's set up; otherwise let the subagents do all their non-browser research in parallel and collect reviews in their tabs one at a time. Never hold back the other research while waiting for reviews.

While they run, research the industry tech stack yourself (`references/dossier-research.md` § Tech stack) and write `research/tech-stack.md`. The spec's integration rankings depend on it. Give the user a one-line update as each business's subagent finishes.

When they finish, open each dossier and check it against the template: every section filled or explicitly marked "not found (searched: …)", sources cited, every claim tagged **[verified]** (seen at a source) or **[inferred]** (reasoned from evidence). Send a subagent back for anything thin rather than papering over it. Give the user a 4-6 line summary per business and the folder path, then go straight into Stage 4.

Personal information boundary: record people only in their business role (owner, medical director, manager, named staff from the site or reviews). Leave out home addresses, personal phones, family details and anything not tied to the business.

## Stage 4: Review synthesis and role playbook

First pool the reviews across all businesses into `research/review-themes.md` (`assets/review-themes-template.md`): cluster praises and complaints into themes, count how many reviews and how many businesses each theme appears in, and keep 2-3 short real quotes per theme. Ranking by spread across businesses, not raw count, stops one very large business from defining the industry.

Then write `roles/<role>/playbook.md` from `assets/playbook-template.md`. The core move: for each theme, ask "what would the person in this role do, every time, so that this praise happens again / this complaint never happens again?" and write it as a concrete procedure or rule, citing the theme. Themes the role cannot influence (for example, treatment results) go in a short "outside this role" list, so the user sees they were considered and not ignored. Include how the role speaks (tone, phrases to use and avoid, sample lines), service standards with numbers where reviews justify them (answer within 3 rings, confirm the day before), and when to hand off to a human.

Show the user the top themes and the 5-8 most important rules, then move straight on to the spec. The playbook is input, not a gate.

## Stage 5: Agent spec (gate)

Write `roles/<role>/agent-spec.md` from `assets/agent-spec-template.md`. This file is the official input contract for `goal-based-voice-agent`, so keep its section headings exactly as in the template. The build skill maps them onto its SCRIPT phases.

The spec turns the playbook into what an AI phone agent can actually do:

1. **Skills.** Each distinct job the agent performs on a call (book, reschedule, cancel, answer pricing, pre- and after-care questions, take a message, transfer). For each: trigger, step-by-step flow, data it needs, success condition, and the playbook rules it enforces.
2. **Integrations per skill.** What system each skill touches (practice-management or booking software, calendar, CRM, SMS, payments, knowledge base, human transfer).
3. **Ranked apps per integration.** For each integration, the 3-5 most-used apps **in this industry**, ranked, with evidence from `research/tech-stack.md`, starting with what the confirmed businesses actually use. Mark the top 2-3 as **preset** (built and supported in the standard build) and the rest as **add on demand**. Never default to a generic tool (Google Calendar, Calendly) unless the research shows this industry uses it.
4. **Demo plan.** Which integrations are live in the demo and which are described but not connected. Live means real: a real demo account on a ranked app, or a real demo calendar for booking. Never a fake that pretends to work. If something cannot be made live yet, say so in the spec and leave it out of the demo.
5. Personality, call flows, knowledge-base contents, escalation rules, and 10-15 test scenarios drawn from real review complaints (the angry rescheduler, the price shopper, the post-treatment worry call).

Ask whether the demo should be a **generic industry demo** (a made-up business name, composite details) or **tailored to one target business** for a pitch. Record the answer in the spec.

Present a one-screen summary: skills, integrations with their preset apps, personality in a line, and what is live in the demo. Then ask: **"Approve this spec so I can build the demo in FlowForge?"** Apply any changes to the file and re-ask. Record the approval and date in `STATUS.md`.

## Stage 6: Handoff to build and iterate

Once approved, invoke the `goal-based-voice-agent` skill and tell it: "Build from the approved agent spec at `<path to agent-spec.md>`, platform FlowForge, artifacts in `<role>/build/`." That skill's spec mode reads the file and runs the SCRIPT build and deployment. Do not re-derive the design inside this skill; the spec is the source of truth.

After the build, update `STATUS.md` with the assistant ID, the demo phone number or test link, and how to call it, then give the user numbered steps to try the demo. Close by asking for their feedback, and suggest what to listen for (does it book correctly, does it sound like the business, how does it handle an upset caller), so they know what kind of feedback helps.

Iteration: when the user gives feedback, decide whether it changes the design (update `agent-spec.md` first, adding a dated entry to its change log) or only the wording or prompt (leave the spec alone). Then hand the change to `goal-based-voice-agent` as an iterative update, which works on a branch, tests and publishes. Every round adds a line to `build/changelog.md`: date, feedback, what changed, test result.

## STATUS.md discipline

Update `STATUS.md` at the end of every stage: current stage, decisions (confirmed businesses, review method, demo type, spec approval date), links to every file, and the next step. It is how a later session, or the user asking "where should I start across these five industries?", finds everything without rereading the research.

## Reference files

- `references/review-collection.md`: browser method step by step; Outscraper setup walkthrough for non-technical users; how much to collect.
- `references/dossier-research.md`: where to find each dossier field, the subagent brief, and the tech-stack research method.
- `assets/*-template.md`: one template per output file.
- `scripts/fetch_reviews_outscraper.py`: pulls reviews through Outscraper once a key is set up.
