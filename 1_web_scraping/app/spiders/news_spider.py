from datetime import datetime
from typing import Any

import scrapy
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from scrapy.spidermiddlewares.httperror import HttpError


class SportNewsSpider(scrapy.Spider):
    name = "sport_news"
    rus_months = [
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    ]
    month_to_num = {m: i + 1 for i, m in enumerate(rus_months)}

    def __init__(self, name: str | None = None, **kwargs: Any):
        super().__init__(name, **kwargs)
        self._user_agent = UserAgent()
        self._num_page = 10

    def start_requests(self):
        first_page = "https://www.sports.ru/news/top/"
        start_urls = [first_page] + [
            f"{first_page}?page={i}" for i in range(2, self._num_page + 2)
        ]
        for url in start_urls:
            yield scrapy.Request(
                url=url,
                headers={"User-Agent": self._user_agent.random},
                callback=self.parse_short_news,
                errback=self.errback_httpbin,
            )

    def errback_httpbin(self, failure):
        # log all failures
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            # these exceptions come from HttpError spider middleware
            # you can get the non-200 response
            response = failure.value.response
            self.logger.error(f"HttpError with status: {response.status}")

    def parse_short_news(self, response, **kwargs):
        soup = BeautifulSoup(response.text, "lxml")
        active_panel = soup.find("li", {"class": "panel active-panel"})
        short_news_divs = active_panel.find_all("div", {"class": "short-news"})
        for div in short_news_divs:
            p_items = div.find_all("p")
            for p in p_items:
                time = p.find("span", {"class": "time"})
                if (
                    p.find(
                        "span",
                        {"class": ["special", "games", "advert_material", "fantasy"]},
                    )
                    is not None
                ):
                    continue
                short_text = p.find("a", {"class": "short-text"})
                short_news_item = {
                    "time": SportNewsSpider._to_datetime(
                        div.b.text, time.text
                    ).isoformat(),
                    "short_text": short_text.text,
                }
                yield response.follow(
                    short_text.get("href"),
                    callback=self.parse_full_news,
                    cb_kwargs=short_news_item,
                )

    def parse_full_news(self, response, time, short_text):
        soup = BeautifulSoup(response.text, "lxml")
        content = soup.find("div", "news-item__content js-mediator-article")
        full_text = []
        for p in content.find_all("p"):
            if p.strong is not None:
                break
            full_text.append(p.text)
        return {
            "time": time,
            "url": response.url,
            "short_text": short_text,
            "full_text": " ".join(full_text),
        }

    @classmethod
    def _to_datetime(cls, date_str: str, time: str) -> datetime:
        date_str = date_str.strip()
        day, month = date_str.split(" ")
        hours, minutes = time.split(":")
        return datetime(
            year=2023,
            month=cls._month_to_number(month),
            day=int(day),
            hour=int(hours),
            minute=int(minutes),
        )

    @classmethod
    def _month_to_number(cls, month: str) -> int:
        return cls.month_to_num[month]
