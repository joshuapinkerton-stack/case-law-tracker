# US Case Law Tracker

Track US court opinions and docket entries from free public legal sources.

## Example input

{ "baseUrl": "https://www.courtlistener.com/opinion/", "maxPages": 5 }

## Output events

| Event | Shape |
|-------|-------|
| `docket_snapshot` | Listing metadata |
| `case_filing` | Title, court, date, docket number, snippet |

## Pricing

Pay-per-Event: $0.10/case_filing + $0.20/docket_snapshot.
