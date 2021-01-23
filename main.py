#!python3
import os
import re
import time
import pandas as pd
from datetime import datetime
import requests
from requests_html import HTML


CLASSES_TO_FIND = [".text-nowrap",
                   ".offer-item-rooms",
                   ".offer-item-area",
                   ".offer-item-price-per-m",
                   ".offer-item-price"]
PREPARED_DATA = "data.csv"
DATA_VER = "verification.txt"


def url_to_txt(url, save=False):
    r = requests.get(url)
    if r.status_code == 200:
        html_text = r.text

        return html_text
    return None


def parse_text(attr, tag):
    priceperm, price = "", ""
    if attr == CLASSES_TO_FIND[0]:
        return {"City": re.findall('Częstochowa, (.*)', tag[1].text)[0]}

    elif attr == CLASSES_TO_FIND[1]:
        return {"Rooms": int(re.findall('\d{1,2}', tag[0].text)[0])}
    elif attr == CLASSES_TO_FIND[2]:
        temp = tag[0].text.replace(",", ".")
        return {"m2": float(re.findall("\d{1,3}.?\d{1,3}", temp)[0])}
    elif attr == CLASSES_TO_FIND[3]:
        temp = re.findall("\d+", tag[0].text)
        for i in temp:
            priceperm += i
        return {"Price_per_m2": int(priceperm)}
    elif attr == CLASSES_TO_FIND[4]:
        temp = re.findall("\d+", tag[0].text)
        for i in temp:
            price += i
        return {"Price": int(price)}
    else:
        print(f"unexpected attr:{attr}")


def extract_data(article, date):
    obj = {}
    obj.update({"date": date.strftime("%x")})
    obj.update({"item_id": article.attrs["data-item-id"]})
    obj.update({"tracking_id": article.attrs["data-tracking-id"]})
    # obj.update(article.attrs["data-url"])
    for c in CLASSES_TO_FIND:
        r_table = article.find(c)
        obj.update(parse_text(c, r_table))

    # print(obj)
    return obj


def run(url, nr, current_date):
    all_auctions = []

    for i in range(1, nr+1):
        time.sleep(0.5)
        page_url = url+f"&page={i}"
        auction_page = url_to_txt(page_url, save=False)
        r_html = HTML(html=auction_page)
        articles = r_html.find('article')

        for art in articles:
            all_auctions.append(extract_data(art, current_date))
    return all_auctions


def checkPagesNr(url):
    # urllib.request.urlretrieve(url, "page.html")
    number = 1
    # with open("page.html", "r", encoding='utf-8') as f:
    #     auction_page = f.read()

    auction_page = url_to_txt(url, save=False)
    r_html = HTML(html=auction_page)
    pages = r_html.find('.pager')
    if not pages:
        pass
    else:
        numbers = pages[0].find("li")
        for nr in numbers:
            if nr.text.isdigit():
                if int(nr.text) > number:
                    number = int(nr.text)
    return number


if __name__ == "__main__":
    date = datetime.now()
    url = "https://www.otodom.pl/sprzedaz/mieszkanie/blok/?search%5Bfilter_enum_rooms_num%5D%5B0%5D=1&search%5Bfilter_enum_rooms_num%5D%5B1%5D=2&locations%5B0%5D%5Bregion_id%5D=12&locations%5B0%5D%5Bcity_id%5D=176&locations%5B0%5D%5Bdistrict_id%5D=2311&locations%5B1%5D%5Bregion_id%5D=12&locations%5B1%5D%5Bcity_id%5D=176&locations%5B1%5D%5Bdistrict_id%5D=5596&locations%5B2%5D%5Bregion_id%5D=12&locations%5B2%5D%5Bcity_id%5D=176&locations%5B2%5D%5Bdistrict_id%5D=148488&nrAdsPerPage=72"

    try:
        request = requests.get(url, timeout=9)
    except (requests.ConnectionError, requests.Timeout):
        print("No internet connection.")
    else:
        if os.path.exists(DATA_VER):
            with open(DATA_VER, "r") as f:
                old_date = datetime.strptime(f.readline(), "%x")
        else:
            old_date = datetime(2000, 1, 1, 1)
        if datetime.strptime(date.strftime("%x"), "%x") > old_date:
            pages_nr = checkPagesNr(url)
            df = pd.DataFrame(run(url, pages_nr, date))
            df.drop_duplicates(inplace=True)
            if os.path.isfile(PREPARED_DATA):
                df.to_csv(PREPARED_DATA, mode="a", encoding='utf-8',
                          index=False, header=False)
            else:
                df.to_csv(PREPARED_DATA, index=False, encoding='utf-8')
            copyfile = pd.read_csv(PREPARED_DATA)
            copyfile.to_csv(os.path.join(
                "copies", date.strftime("%Y-%m-%d_%H%M%S")+".csv"),  index=False, encoding='utf-8')
            with open(DATA_VER, "w") as f:
                f.writelines(date.strftime("%x"))

        else:
            print("script ran today already")
