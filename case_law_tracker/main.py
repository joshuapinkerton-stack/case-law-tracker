import json
from datetime import datetime, timezone

from apify import Actor
from crawlee.crawlers import CheerioCrawler
from crawlee import router

from .routes import router as court_router


async def main() -> None:
    async with Actor:
        actor_input = await Actor.get_input() or {}

        base_url = actor_input.get(
            'baseUrl',
            'https://www.courtlistener.com/opinion/',
        )
        max_pages = int(actor_input.get('maxPages', 5))

        requests = [
            {'url': f'{base_url}?page={page}', 'userData': {'handler': 'listing'}}
            for page in range(1, max_pages + 1)
        ]

        crawler = CheerioCrawler(
            max_requests_per_crawl=max_pages + 20,
            max_request_retries=4,
            request_handler=court_router,
        )

        await crawler.run(requests)

        dataset = await Actor.open_dataset()
        await dataset.push_data({
            'type': 'crawl_run_meta',
            'crawledAt': datetime.now(timezone.utc).isoformat(),
            'baseUrl': base_url,
            'maxPages': max_pages,
        })

        try:
            await Actor.charge('docket_snapshot', {
                'crawledAt': datetime.now(timezone.utc).isoformat(),
                'baseUrl': base_url,
            })
        except RuntimeError:
            pass

        Actor.log.info(f'Case law tracker completed: {max_pages} pages.')
