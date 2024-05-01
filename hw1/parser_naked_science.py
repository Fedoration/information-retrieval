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


def parse_articles_snippets(
    domain_url: str, logger: logging.Logger, pages_limit: int = -1
):
    articles_snippets = []
    page_num = 1
    while True:
        time.sleep(1)
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
            news_tags = bs.find_all("div", attrs={"class": "news-item grid"})
            for tag in news_tags:
                # parse link
                try:
                    article_link = tag.find(
                        "div", attrs={"class": "news-item-title"}
                    ).find("a")["href"]
                except Exception as e:
                    print(f"[ERROR] {e} while parsing article link {url}")
                    logger.error(f"{e} while parsing article link {url}")

                # parse title
                try:
                    article_title = (
                        tag.find("a", class_="animate-custom").contents[0].get_text()
                    )
                    article_title = clean_string(article_title)
                except Exception as e:
                    print(f"[ERROR] {e} while parsing article title {url}")
                    logger.error(f"{e} while parsing article title {url}")

                # parse category
                try:
                    category_tag = tag.find(
                        "div", attrs={"class": "terms-item terms-item--cat"}
                    )
                    if not category_tag:
                        category_tag = tag.find(
                            "div", attrs={"class": "terms-item terms-item--avtor"}
                        )
                    if category_tag:
                        article_category = category_tag.find("a").get_text()
                        article_category = clean_string(article_category)
                except Exception as e:
                    print(f"[ERROR] {e} while parsing article category {url}")
                    logger.error(f"{e} while parsing article category {url}")

                articles_snippets.append(
                    {
                        "article_link": str(article_link),
                        "article_title": str(article_title),
                        "article_category": str(article_category),
                    }
                )

            print(f"[INFO] Parsed {len(articles_snippets)} links, page {page_num}")
            logger.info(f"Parsed {len(articles_snippets)} links, page {page_num}")

            if pages_limit != -1 and page_num > pages_limit:
                print(f"[INFO] Reached pages limit [{pages_limit}], exiting...")
                logger.info(f"Reached pages limit [{pages_limit}], exiting...")
                break

            page_num += 1

    return articles_snippets


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

    # extract text
    text = None
    try:
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

    except Exception as e:
        print(f"[ERROR] {e} while parsing article content {url}")
        logger.error(f"{e} while parsing article content {url}")

    return text


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        filename="naked-science-parser.log",
        filemode="w",
        format="%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
    )
    logger = logging.getLogger()

    PAGES_LIMIT = 200

    corpus = []
    words_count = 0
    domain = "https://naked-science.ru/"
    corpus = parse_articles_snippets(domain, logger, pages_limit=PAGES_LIMIT)

    print(f"[INFO] Parsed {len(corpus)} articles")
    with open("naked_science_articles_snippets.json", "w") as f:
        json.dump(corpus, f)

    # with open("naked_science_articles_links.json", "r") as f:
    #     articles_links = json.load(f)

    parsed_articles_count = 0
    for article in corpus:
        time.sleep(2)

        url = article["article_link"]
        article_content = parse_article_content(url, logger)
        article["text"] = article_content

        if not article_content:
            continue

        words_count += len(article_content.split())
        parsed_articles_count += 1
        print(
            f"[INFO] Parsed {parsed_articles_count} articles so far, total words count: {words_count}"
        )
        logger.info(
            f"Parsed {parsed_articles_count} articles so far, total words count: {words_count}"
        )

        with open("naked_science_corpus.json", "w") as f:
            json.dump(corpus, f)

    with open("naked_science_corpus.json", "w") as f:
        json.dump(corpus, f)

    print(f"[INFO] Parsing finished, total {parsed_articles_count} articles")
    logger.info(f"Parsing finished, total {parsed_articles_count} articles")


# def parse_articles_snippets(
#     domain_url: str, logger: logging.Logger, pages_limit: int = -1
# ):
#     articles_links = []
#     page_num = 1
#     while True:
#         time.sleep(1)
#         url = f"{domain_url}article/page/{page_num}/"
#         response = requests.get(url, headers=HEADERS)

#         status_code = response.status_code
#         if status_code != 200:
#             print(
#                 f"[WARNING] Error fetching page {url}! Status code: {response.status_code}"
#             )
#             logger.warning(
#                 f"Error fetching page {url}! Status code: {response.status_code}"
#             )
#             break
#         else:
#             bs = BeautifulSoup(response.text, "html.parser")

#             tags = bs.find_all("div", attrs={"class": "news-item-title"})

#             if not tags:
#                 print(f"[WARNING] Page {url} is empty or not found, exiting...")
#                 logger.warning(f"Page {url} is empty or not found, exiting...")
#                 break

#             links = [link.find("a")["href"] for link in tags]
#             articles_links.extend(links)

#             print(f"[INFO] Parsed {len(articles_links)} links, page {page_num}")
#             logger.info(f"Parsed {len(articles_links)} links, page {page_num}")

#             if pages_limit != -1 and page_num > pages_limit:
#                 print(f"[INFO] Reached pages limit [{pages_limit}], exiting...")
#                 logger.info(f"Reached pages limit [{pages_limit}], exiting...")
#                 break

#             page_num += 1

#     return articles_links


# def parse_article_content(url, logger):
#     title, category, text = None, None, None

#     response = requests.get(url, headers=HEADERS)
#     status_code = response.status_code
#     if status_code != 200:
#         print(
#             f"[ERROR] Error fetching page content {url}! Status code: {response.status_code}"
#         )
#         logger.error(
#             f"Error fetching page content {url}! Status code: {response.status_code}"
#         )
#         return None

#     bs = BeautifulSoup(response.text, "html.parser")

#     # extract title
#     try:
#         raw_title = bs.find("div", attrs={"class": "post-title"}).find("h1").get_text()
#         title = clean_string(raw_title)
#     except Exception as e:
#         print(f"[ERROR] Error {e} extracting title from {url}")
#         logger.error(f"Error {e} extracting title from {url}")

#     # extract category
#     category_tag = bs.find("div", attrs={"class": "terms-wrapp"}).find(
#         "div", attrs={"class": "terms-item terms-item--cat"}
#     )

#     if not category_tag:
#         category_tag = bs.find("div", attrs={"class": "terms-wrapp"}).find(
#             "div", attrs={"class": "terms-item terms-item--avtor"}
#         )

#     if category_tag:
#         raw_category = category_tag.find("a").get_text()
#         category = clean_string(raw_category)

#     # extract text
#     article_paragraphs = (
#         bs.find("div", attrs={"class": "content"})
#         .find("div", attrs={"class": "body"})
#         .find_all(["p", "h1", "h2", "h3", "h4", "h5"])
#     )
#     text = ""
#     for paragraph in article_paragraphs:
#         if paragraph.name in ["h1", "h2", "h3", "h4", "h5"]:
#             text += clean_string(paragraph.get_text()) + ". "
#         else:
#             text += clean_string(paragraph.get_text()) + " "
#     text = clean_string(text)

#     return title, category, text
