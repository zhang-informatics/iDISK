import argparse
import json

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from mskcc_web_scraper import MSKCC_URL
from mskcc_web_scraper import MSKCC_Content


def parse_args():
    """
    Set up arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--outfile", type=str,
                        required=True,
                        help="""Full path to the JSONL file to store herb
                                and its content.""")
    args = parser.parse_args()
    return args


class ExtractDriver(object):
    """
    The driver for extracting herb url and pre-defined headers
    """

    def __init__(self, content_file):
        """
        ExtractDriver consturctor

        :param str content_file: the full path of herb content JSONL file  # noqa
        """
        self.content_file = content_file

    def setup_driver(self):
        """
        Set up selenium driver
        """
        options = Options()
        # do not open firefox
        options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path="/usr/local/bin/geckodriver",  # noqa
                                   options=options)
        driver.implicitly_wait(1)
        return driver

    def extract_process(self):
        """
        Main function for ExtractDriver class
        """
        # set up driver
        driver = self.setup_driver()
        url_getter = MSKCC_URL(driver)
        content_getter = MSKCC_Content(driver)
        # extract herb url
        name2url = url_getter.get_herb_url()
        # keep tracked if the line is already added
        line_seen = []
        # iterate name2url to get content
        for herb_name, url in name2url.items():
            content = content_getter.get_content_from_url(herb_name, url)
            with open(self.content_file, "a") as f:
                if content not in line_seen:
                    json.dump(content, f)
                    f.write("\n")


if __name__ == "__main__":
    args = parse_args()
    x = ExtractDriver(args.outfile)
    x.extract_process()
