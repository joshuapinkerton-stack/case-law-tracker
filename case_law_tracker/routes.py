import json
from datetime import datetime, timezone

from apify import Actor
from crawlee.crawlers import Router

router = Router[dict]()


@router.handler('listing')
async def handle_listing(context) -> None:
    response = await context.get_current_page().response_async()
    html = await response.text_async()

    from selectolax.parser import HTMLParser
    doc = HTMLParser(html)

    articles = doc.css('article')
    seen = set()
    for article in articles:
        link_node = article.css_first('a')
        if not link_node:
            continue
        href = link_node.attributes.get('href', '')
        if not href or href in seen:
            continue
        seen.add(href)
        if href.startswith('/'):
            href = f'https://www.courtlistener.com{href}'
        await context.add_requests([{'url': href, 'userData': {'handler': 'opinion'}}])

    try:
        await Actor.charge('docket_snapshot', {
            'crawledAt': datetime.now(timezone.utc).isoformat(),
            'url': response.url,
            'enqueuedCases': len(seen),
        })
    except RuntimeError:
        pass


@router.handler('opinion')
async def handle_opinion(context) -> None:
    response = await context.get_current_page().response_async()
    html = await response.text_async()

    from selectolax.parser import HTMLParser
    doc = HTMLParser(html)

    title_node = doc.css_first('h1, .case-title')
    title = title_node.text().strip() if title_node else ''

    court_node = doc.css_first('.court, .panel-title')
    court = court_node.text().strip() if court_node else ''

    date_node = doc.css_first('time, .date')
    date_filed = date_node.text().strip() if date_node else ''

    docket_node = doc.css_first('.docket, [id*=docket]')
    docket = docket_node.text().strip() if docket_node else ''

    text_node = doc.css_first('.opinion, .content, article')
    text = text_node.text().strip()[:500] if text_node else ''

    item = {
        'title': title,
        'court': court,
        'dateFiled': date_filed,
        'docketNumber': docket,
        'url': response.url,
        'textSnippet': text,
        'detectedAt': datetime.now(timezone.utc).isoformat(),
    }

    dataset = await Actor.open_dataset()
    await dataset.push_data(item)

    try:
        await Actor.charge('case_filing', item)
    except RuntimeError:
        pass
