import re
import json
import logging
import requests
from bs4 import BeautifulSoup


def clean_string(input_string):
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

    return cleaned_string


def parse_hub_links(logger):
    hubs_links = []
    page_num = 1
    while True:
        url = f"https://habr.com/ru/hubs/page{page_num}/"
        response = requests.get(url)
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
            bs = BeautifulSoup(
                response.text,
                "html.parser",
            )

            not_found_page = bs.find_all(
                "h1", attrs={"class": "tm-error-message__title"}
            )
            tags = bs.find_all("a", attrs={"class": "tm-hub__title"})

            if not_found_page or not tags:
                print(f"[WARNING] Page {url} is empty or not found, exiting...")
                logger.warning(f"Page {url} is empty or not found, exiting...")
                break

            links = ["https://habr.com" + l["href"] for l in tags]
            hubs_links.extend(links)
            page_num += 1

            print(f"[INFO] Parsed {len(hubs_links)} links")
            logger.info(f"Parsed {len(hubs_links)} links")

    return hubs_links


def parse_hub_title(hub_url, logger):
    response = requests.get(hub_url)
    bs = BeautifulSoup(response.text, "html.parser")
    hub_title = bs.h1.text.strip()
    hub_title = hub_title.replace("  *", "").strip()
    return hub_title


def parse_hub_articles(hub_link: str, logger):
    articles_links = []
    page_num = 1
    while True:
        url = f"{hub_link}articles/page{page_num}/"
        response = requests.get(url)
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
            bs = BeautifulSoup(
                response.text,
                "html.parser",
            )
            not_found_page = bs.find_all(
                "h1", attrs={"class": "tm-error-message__title"}
            )
            tags = bs.find_all("a", attrs={"class": "tm-title__link"})

            if not_found_page or not tags:
                print(f"[WARNING] Page {url} is empty or not found, exiting...")
                logger.warning(f"Page {url} is empty or not found, exiting...")
                break

            links = ["https://habr.com" + l["href"] for l in tags]
            articles_links.extend(links)
            page_num += 1

            print(f"[INFO] Parsed {len(articles_links)} links")
            logger.info(f"Parsed {len(articles_links)} links")

    return articles_links


def get_content_version(bs: BeautifulSoup) -> str:
    tags_v1 = bs.find_all(
        "div",
        attrs={
            "class": "article-formatted-body article-formatted-body article-formatted-body_version-1"
        },
    )
    tags_v2 = bs.find_all(
        "div",
        attrs={
            "class": "article-formatted-body article-formatted-body article-formatted-body_version-2"
        },
    )
    if tags_v1:
        return "1", tags_v1
    if tags_v2:
        return "2", tags_v2
    return None, None


def parse_article_content(url, logger):
    response = requests.get(url)
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
    content_version, tags = get_content_version(bs)
    if content_version == "1":
        article_text = tags[0].get_text().strip()
    elif content_version == "2":
        article_paragraphs = tags[0].find_all(["p", "h1", "h2", "h3", "h4", "h5"])
        article_text = ""
        for paragraph in article_paragraphs:
            if paragraph.name in ["h1", "h2", "h3", "h4", "h5"]:
                article_text += paragraph.get_text() + ". "
            else:
                article_text += paragraph.get_text() + " "
    else:
        print(f"[ERROR] Undefined conent version for {url}!")
        logger.error(f"Undefined conent version for {url}!")
        return None

    article_title = bs.h1.text
    article_text = clean_string(article_text)

    return article_title, article_text


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        filename="habr_parser.log",
        filemode="w",
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    )
    logger = logging.getLogger()

    corpus = []
    hubs_links = parse_hub_links(logger)

    for hub_url in hubs_links:
        hub_name = parse_hub_title(hub_url, logger)
        articles_links = parse_hub_articles(hub_url, logger)

        for article_url in articles_links:
            article_title, article_text = None, None
            article_content = parse_article_content(article_url, logger)
            if article_content:
                article_title, article_text = article_content
            else:
                print(f"[ERROR] No content found for article: {article_url}")
                logger.error(f"No content found for article: {article_url}")
            corpus.append(
                {
                    "hub_url": hub_url,
                    "article_url": article_url,
                    "hub_name": hub_name,
                    "title": article_title,
                    "text": article_text,
                }
            )
            print(f"[INFO] Parsed {len(corpus)} articles so far")
            logger.info(f"Parsed {len(corpus)} articles so far")

        with open("corpus.json", "w") as f:
            json.dump(corpus, f)

    with open("corpus.json", "w") as f:
        json.dump(corpus, f)
