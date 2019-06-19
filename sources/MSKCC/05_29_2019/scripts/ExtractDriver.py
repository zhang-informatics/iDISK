import argparse

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from mskcc_web_scraper import MSKCC_URL
from mskcc_web_scraper import MSKCC_Content


def parse_args():
    """
    Set up arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--al_file", type=str,
                        required=True,
                        help="Full path to the CSV file to store alphabetic listing URL.")  # noqa
    parser.add_argument("--herb_file", type=str,
                        required=True,
                        help="Full path to the CSV file to store all MSKCC herb's URLs.")  # noqa
    parser.add_argument("--content_file", type=str,
                        required=True,
                        help="Full path to the JSONL file to store herb and its content.")  # noqa
    args = parser.parse_args()
    return args


class ExtractDriver(object):
    """
    The driver for extracting herb url and pre-defined headers
    """

    def __init__(self, al_file, herb_file, content_file):
        """
        ExtractDriver consturctor

        :param str al_file: the full path of alphabetic listing CSV file  # noqa
        :param str herb_file: the full path of herb URL CSV file  # noqa
        :param str content_file: the full path of herb content JSONL file  # noqa
        """
        self.al_file = al_file
        self.herb_file = herb_file
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

    def get_herb_url(self, driver, al_file, herb_file):
        """
        Get URL for each MSKCC herb

        :param WebDriver driver: selenium driver
        :param str path: local file to store extracted info
        :param str al_file: csv file to store alphabetic listing
        :param str herb_file: csv file to store all MSKCC herb's URLs
        """
        url_getter = MSKCC_URL(driver, al_file, herb_file)
        url_getter.run()

    def get_herb_content(self, driver, herb_file, content_file):
        """
        Get contents for each MSKCC herb

        :param WebDriver driver: selenium driver
        :param str herb_file: CSV file to store all MSKCC herb's URLs
        :param str content_file: JSONL file to store all extracted contents
        """
        content_getter = MSKCC_Content(driver, herb_file, content_file)
        content_getter.process_file()

    def extract_process(self):
        """
        Main function for ExtractDriver class
        """
        # set up driver
        driver = self.setup_driver()
        # extract herb url
        self.get_herb_url(driver, self.al_file,
                          self.herb_file)
        # extract herb content
        self.get_herb_content(driver, self.herb_file,
                              self.content_file)


if __name__ == "__main__":
    args = parse_args()
    x = ExtractDriver(args.al_file, args.herb_file, args.content_file)
    x.extract_process()
