from pathlib import Path
import argparse
from datetime import date
from datetime import datetime

import bs4 as bs
import request
import pandas as pd
import json


class Immo24scrape:
    def __init__(self):
        pass

    def main(self):
        self.parse()
        self.set_filepath()
        self.run()

    def run(self):
        # iterate over all available result pages showing 20 results each
        self.page = 1
        self.broken_pages = []
        while True:
            print(f"Scraping results from page {self.page}.")
            # check if pagenumber exists
            try:
                self.get_pagelinks()
                self.get_pagedata()
                self.write_pagedata()
            # catch urllib errors
            except (URLError, HTTPError):
                # Skip broken pages until there have been 5, then break
                print(f"Skipping page {self.page}.")
                self.broken_pages.append(self.page)
                if len(self.broken_pages) > 5:
                    break
            self.page += 1

    def parse(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--type",
            choices=["mieten", "kaufen"],
            help="chose between 'mieten' and 'kaufen'",
            type=str,
            default="mieten",
        )
        self.args = parser.parse_args()

    def set_filepath(self):
        self.filename = self.args.type + str(date.today()) + ".csv"
        # get absolute path to script directory and select data folder in parent directory
        self.savepath = str((Path(__file__).parent.absolute() / "../data/").resolve())
        self.filepath = self.savepath + "/" + self.filename

    def get_pagelinks(self):
        # scrape links to exposes from every individual result page
        self.links = []
        # use urllib.request and beautiful soup to extract links
        soup = bs.BeautifulSoup(
            urllib.request.urlopen(
                "https://www.immobilienscout24.de/Suche/de/wohnung-"
                + self.args.type
                + "?pagenumber="
                + str(self.page)
            ).read(),
            "lxml",
        )
        # find all paragraphs in html-page
        for paragraph in soup.find_all("a"):
            # get expose numbers
            if r"/expose/" in str(paragraph.get("href")):
                self.links.append(paragraph.get("href").split("#")[0])
            # use set function to only keep one link per expose
            self.links = list(set(self.links))

    def get_pagedata(self):
        self.pagedata = pd.DataFrame()
        # get data from every expose link
        for link in self.links:
            # use urllib.request and Beautiful soup to extract data
            soup = bs.BeautifulSoup(
                urllib.request.urlopen(
                    "https://www.immobilienscout24.de" + link
                ).read(),
                "lxml",
            )
            # extract features into Pandas Dataframe with json loader
            linkdata = pd.DataFrame(
                json.loads(
                    str(soup.find_all("script")).split("keyValues = ")[1].split("}")[0]
                    + str("}")
                ),
                index=[str(datetime.now())],
            )
            # save URL as unique identifier
            linkdata["URL"] = str(link)
            self.pagedata = self.pagedata.append(linkdata)

    def write_pagedata(self):
        print(f"Appending data of page {self.page} to {self.filepath}")
        with open(self.filepath, "a") as f:
            self.pagedata.to_csv(
                f,
                # only create header if file is newly created
                header=f.tell() == 0,
                sep=";",
                decimal=",",
                encoding="utf-8",
                index_label="timestamp",
            )


if __name__ == "__main__":
    dataset = Immo24scrape()
    dataset.main()
