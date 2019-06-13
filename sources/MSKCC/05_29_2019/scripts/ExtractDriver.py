import os
import argparse
from CancerUrl import CancerUrl
from CancerContext import CancerContext
from selenium import webdriver
from selenium.webdriver.firefox.options import Options


class ExtractDriver(object):
    """
    The driver for extracting herb url and pre-defined headers
    """

    def __init__(self):
        # get downloaded file location
        self.path = os.path.dirname(os.getcwd())
        self.path = os.path.join(self.path, "download")

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

    def parse_arg(self):
        """
        Set up arguments
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("--file_al", type=str,
                            required=True,
                            help="JSONL file to store alphabetic listing URL.")
        parser.add_argument("--file_hl", type=str,
                            required=True,
                            help="csv file to store all MSKCC herb's URLs.")
        parser.add_argument("--file_con", type=str,
                            required=True,
                            help="JSONL file to store herb and its content.")
        args = parser.parse_args()
        return args

    def get_herb_url(self, driver, path, file_al, file_hl):
        """
        Get URL for each MSKCC herb

        :param WebDriver driver: selenium driver
        :param str path: local file to store extracted info
        :param str file_al: csv file to store alphabetic listing
        :param str fiel_hl: csv file to store all MSKCC herb's URLs
        """
        url_getter = CancerUrl(driver, path, file_al, file_hl)
        url_getter.run()

    def get_herb_content(self, driver, path, file_hl, file_con):
        """
        Get contents for each MSKCC herb

        :param WebDriver driver: selenium driver
        :param str path: local file to store extracted info
        :param str fiel_hl: csv file to store all MSKCC herb's URLs
        :param str file_con: JSONL file to store all extracted contents
        """
        content_getter = CancerContext(driver, path, file_hl, file_con)
        content_getter.process_file()

    def extract_process(self):
        """
        Main function for ExtractDriver
        """
        # set up arguments
        args = self.parse_arg()
        # set up driver
        driver = self.setup_driver()
        '''
        # extract herb url
        self.get_herb_url(driver, self.path,
                          args.file_al, args.file_hl)
        '''
        # extract herb content
        self.get_herb_content(driver, self.path,
                              args.file_hl, args.file_con)


if __name__ == "__main__":
    x = ExtractDriver()
    x.extract_process()
