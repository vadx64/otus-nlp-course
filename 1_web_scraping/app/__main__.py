import sys

from scrapy.crawler import CrawlerProcess
from app.spiders.news_spider import SportNewsSpider


def main() -> int:
    process = CrawlerProcess(
        settings={
            "FEEDS": {
                "output/sport_news.jsonl": {
                    "format": "jsonlines",
                    "encoding": "utf8",
                    "store_empty": False,
                    "overwrite": True,
                }
            },
            "DOWNLOAD_DELAY": 1,
            "RANDOMIZE_DOWNLOAD_DELAY": True,
            "JOBDIR": "crawls",
        }
    )

    process.crawl(SportNewsSpider)
    process.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
