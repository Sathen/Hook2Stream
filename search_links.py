import json
import logging
import time
import urllib.parse

import requests
from bs4 import BeautifulSoup

from settings import USER_AGENT, HOST, SEARCH_QUERY

logging.basicConfig(level=logging.INFO)


def get_document(url):
    headers = {
        "User-Agent": USER_AGENT
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def search_film(film_name_r, season):
    links = []
    search_url = get_search_url(film_name_r, season)
    search_doc = get_document(search_url)
    link_to_film = search_doc.select_one("div#block-search-page div.row div.col div.item a[href]")

    if not link_to_film:
        logging.info("Фільм не знайдено у пошуку.")
        return []

    film_page_url = HOST + link_to_film["href"]
    film_data = get_film_data(film_page_url)
    embed_urls = get_embed_url(film_data, season)

    for url in embed_urls:
        time.sleep(1)
        embed_doc = get_document(url)
        if not embed_doc:
            logging.info(f"Embed link not found: {url}")
            return []
        video_options = embed_doc.select("option[data-type=link]")
        links.append(get_source_url(video_options))

    return links


def get_source_url(video_options):
    for option in video_options:
        value = option.get("value", "")
        if "ashdi" in value:
            return value


def get_embed_url(film_data, season):
    if film_data['@type'] == 'TVSeason':
        return get_tv_embed_url(film_data, season)
    elif film_data['@type'] == 'Movie':
        return get_movie_embed_url(film_data)


def get_movie_embed_url(film_data):
    film_page_url = film_data['url']
    film_doc = get_document(film_page_url)
    embed_iframe = film_doc.select_one("div.video-holder iframe#embed")
    return HOST + embed_iframe["src"]


def get_tv_embed_url(film_data, season):
    season = season - 1 or 0
    film_page_url = film_data['partOfTVSeries']['containsSeason'][season]['url']
    film_doc = get_document(film_page_url)
    selector = f"select#select-series option[data-series-number]"
    embed_iframe = film_doc.select(selector)
    links = list()
    for option in embed_iframe:
        links.append(HOST + option["value"])
    return links


def get_search_url(film_name_r, season):
    search_value = film_name_r
    if season:
        search_value = film_name_r + " " + str(season)

    normalize_film_name = urllib.parse.quote_plus(search_value)
    search_url = f"{HOST}/{SEARCH_QUERY}{normalize_film_name}"
    return search_url


def get_film_data(url):
    film_page = get_document(url)
    script_tag = film_page.find('script', type='application/ld+json')
    if script_tag:
        json_data = script_tag.string

        try:
            data = json.loads(json_data)
            return data
        except json.JSONDecodeError as e:
            logging.info(f"Помилка при розборі JSON: {e}")
    else:
        logging.info("Не знайдено тег <script type='application/ld+json'>")
