import os
from cancer_url import cancer_url
from cancer_context import cancer_context
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
# driver function for extracting cancer site data
# extracted headers are pre-determined using cancer_context.py
# if you need to change the required headers, please run cancer_url.py and cancer_header.py separately and manually change
class extract_driver(object):
    def __init__(self):
        # get this python script location
        self.path = os.path.dirname(os.getcwd())
        self.path = os.path.join(self.path, "download")
    #setup selenium webdriver
    def driverSetup(self):
        options = Options()
        # do not open firefox 
        options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path = "/usr/local/bin/geckodriver", options = options)
        driver.implicitly_wait(1)
        return driver
    # get all ingredients from cancer site as their alphabetic listing
    # generate cancer_herb_url.csv
    def getURL(self, driver):
        urlGetter = cancer_url(driver, self.path)
        urlGetter.run()
    # get section contents for each ingredient
    def getContent(self, driver):
        contGetter = cancer_context(driver, self.path)
        contGetter.run()
    # main function for extraction driver
    def run(self):
        driver = self.driverSetup()
        self.getURL(driver)
        self.getContent(driver)
if __name__ == "__main__":
    x = extract_driver()
    x.run()