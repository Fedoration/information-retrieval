import re
import json
import logging
import requests
from bs4 import BeautifulSoup
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 YaBrowser/23.5.1.762 Yowser/2.5 Safari/537.36",
    "Content-Type": "application/json",
}


def clean_string(input_string):
    input_string = input_string.strip()
    cleaned_string = (
        input_string.replace("\n\n\r\n", " ")
        .replace("\r\n", " ")
        .replace("\n\n", " ")
        .replace("\n", " ")
        .replace("\n\n\n", " ")
        .replace("\n\r\n", " ")
        .replace("\r\n\r\n", " ")
        .replace("\n\n\n\n", " ")
    )
    cleaned_string = " ".join(cleaned_string.split())
    cleaned_string = cleaned_string.strip()

    return cleaned_string


def parse_articles_links(
    domain_url: str, logger: logging.Logger, pages_limit: int = -1
):
    articles_links = []
    page_num = 1
    while True:
        time.sleep(0.2)
        url = f"{domain_url}article/page/{page_num}/"
        response = requests.get(url, headers=HEADERS)

        status_code = response.status_code
        if status_code != 200:
            print(
                f"[WARNING] Error fetching page {url}! Status code: {response.status_code}"
            )
            logger.warning(
                f"Error fetching page {url}! Status code: {response.status_code}"
            )
            break
        else:
            bs = BeautifulSoup(response.text, "html.parser")

            tags = bs.find_all("div", attrs={"class": "news-item-title"})

            if not tags:
                print(f"[WARNING] Page {url} is empty or not found, exiting...")
                logger.warning(f"Page {url} is empty or not found, exiting...")
                break

            links = [link.find("a")["href"] for link in tags]
            articles_links.extend(links)
            page_num += 1

            print(f"[INFO] Parsed {len(articles_links)} links")
            logger.info(f"Parsed {len(articles_links)} links")

            if pages_limit != -1 and page_num > pages_limit:
                print(f"[INFO] Reached pages limit [{pages_limit}], exiting...")
                logger.info(f"Reached pages limit [{pages_limit}], exiting...")
                break

    return articles_links


def parse_article_content(url, logger):
    response = requests.get(url, headers=HEADERS)
    status_code = response.status_code
    if status_code != 200:
        print(
            f"[ERROR] Error fetching page content {url}! Status code: {response.status_code}"
        )
        logger.error(
            f"Error fetching page content {url}! Status code: {response.status_code}"
        )
        return None

    bs = BeautifulSoup(response.text, "html.parser")

    # extract title
    raw_title = bs.find("div", attrs={"class": "post-title"}).find("h1").get_text()
    title = clean_string(raw_title)

    # extract category
    raw_category = (
        bs.find("div", attrs={"class": "terms-wrapp"})
        .find("div", attrs={"class": "terms-item terms-item--cat"})
        .find("a")
        .get_text()
    )
    category = clean_string(raw_category)

    # extract text
    article_paragraphs = (
        bs.find("div", attrs={"class": "content"})
        .find("div", attrs={"class": "body"})
        .find_all(["p", "h1", "h2", "h3", "h4", "h5"])
    )
    text = ""
    for paragraph in article_paragraphs:
        if paragraph.name in ["h1", "h2", "h3", "h4", "h5"]:
            text += clean_string(paragraph.get_text()) + ". "
        else:
            text += clean_string(paragraph.get_text()) + " "
    text = clean_string(text)

    return title, category, text


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        filename="habr_parser.log",
        filemode="w",
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    )
    logger = logging.getLogger()

    PAGES_LIMIT = 100

    corpus = []
    words_count = 0
    domain = "https://naked-science.ru/"
    articles_links = parse_articles_links(domain, logger, pages_limit=PAGES_LIMIT)
    for url in articles_links:
        title, category, text = None, None, None
        article_content = parse_article_content(url, logger)
        if article_content:
            title, category, text = article_content
        else:
            print(f"[ERROR] No content found for article: {url}")
            logger.error(f"No content found for article: {url}")
        corpus.append(
            {
                "article_url": url,
                "category": category,
                "title": title,
                "text": text,
            }
        )
        words_count += len(text.split())
        print(
            f"[INFO] Parsed {len(corpus)} articles so far, total words count: {words_count}"
        )
        logger.info(
            f"Parsed {len(corpus)} articles so far, total words count: {words_count}"
        )

        with open("naked_science_corpus.json", "w") as f:
            json.dump(corpus, f)

    with open("naked_science_corpus.json", "w") as f:
        json.dump(corpus, f)
