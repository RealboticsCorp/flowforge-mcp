#!/usr/bin/env python3
"""Fetch Google Maps reviews for one business through the Outscraper API.

The key comes from OUTSCRAPER_API_KEY or ~/.config/agent-market-research/outscraper.key
and is never printed. Standard library only, so it runs with any Python 3.9+.

Usage:
  fetch_reviews_outscraper.py "Business Name, 123 Main St, Los Angeles, CA" \
      --limit 50 --sort newest [--out reviews.json]
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = "https://api.app.outscraper.com/maps/reviews-v3"
KEY_FILE = Path.home() / ".config" / "agent-market-research" / "outscraper.key"
SORTS = ("most_relevant", "newest", "highest_rating", "lowest_rating")
TIMEOUT_SECONDS = 300


def load_key() -> str:
    key = os.environ.get("OUTSCRAPER_API_KEY", "").strip()
    if not key and KEY_FILE.exists():
        key = KEY_FILE.read_text().strip()
    if not key:
        sys.exit(f"No Outscraper key found. Save it to {KEY_FILE} (see review-collection.md step 4).")
    return key


def fetch(query: str, limit: int, sort: str, language: str) -> list:
    params = urllib.parse.urlencode({
        "query": query,
        "reviewsLimit": limit,
        "sort": sort,
        "language": language,
        "limit": 1,
        "async": "false",
    })
    request = urllib.request.Request(f"{ENDPOINT}?{params}", headers={"X-API-KEY": load_key()})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        hint = {
            401: "the API key was rejected; save it again",
            402: "payment needed; add a card or credits in Outscraper Billing",
            403: "the key is not allowed to use the API; check Billing",
            422: "the query was not understood; use 'name, full address' or a Place ID",
        }.get(error.code, "see the Outscraper dashboard for details")
        sys.exit(f"Outscraper returned HTTP {error.code}: {hint}.")
    except urllib.error.URLError as error:
        sys.exit(f"Could not reach Outscraper: {error.reason}")
    return payload.get("data", [])


def summarise(places: list) -> list:
    """Keep only the fields the dossier uses, one record per place."""
    out = []
    for place in places:
        reviews = [
            {
                "rating": r.get("review_rating"),
                "date": datetime.fromtimestamp(r["review_timestamp"], timezone.utc).strftime("%Y-%m-%d")
                if r.get("review_timestamp") else r.get("review_datetime_utc"),
                "author": r.get("author_title"),
                "text": r.get("review_text"),
                "owner_reply": r.get("owner_answer"),
            }
            for r in place.get("reviews_data") or []
        ]
        out.append({
            "name": place.get("name"),
            "address": place.get("full_address"),
            "place_id": place.get("place_id"),
            "rating": place.get("rating"),
            "review_count": place.get("reviews"),
            "reviews": reviews,
        })
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", help="'Business name, full address' or a Google Place ID")
    parser.add_argument("--limit", type=int, default=50, help="reviews to fetch (default 50)")
    parser.add_argument("--sort", choices=SORTS, default="newest")
    parser.add_argument("--language", default="en")
    parser.add_argument("--out", type=Path, help="write JSON here instead of stdout")
    args = parser.parse_args()

    places = summarise(fetch(args.query, args.limit, args.sort, args.language))
    if not places:
        sys.exit("No matching place found. Add the full street address or use a Place ID.")

    text = json.dumps(places, indent=2, ensure_ascii=False)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text)
    for place in places:
        print(f"{place['name']}: {len(place['reviews'])} reviews fetched "
              f"(listing shows {place['review_count']} at {place['rating']}★)", file=sys.stderr)


if __name__ == "__main__":
    main()
