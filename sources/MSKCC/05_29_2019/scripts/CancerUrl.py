import csv
import os
from selenium.common.exceptions import NoSuchElementException


class CancerUrl(object):
    """
    Get MSKCC ingredients URLs by alphabetic listing.
    Save the alphabetic listing file to local as file_al.
    From each URL in fila_al, load the entire page and extract all herbs.
    Save each herb's URL into file_hl
    """

    def __init__(self, driver, path, file_al, file_hl):
        self.urls = {}
        self.domain = "https://www.mskcc.org/cancer-care"  # noqa
        self.start_page = "https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs/search"  # noqa
        # pages that are split by herb leading character
        self.pages = {}
        # url for each herb
        self.herbs = {}
        # selenium driver, setup in ExtractDriver class
        self.driver = driver
        # local file path to store extracted content
        self.path = path
        # csv file to store alphabetic listing
        self.file_al = file_al
        # csv file to store all MSKCC herb's URLs
        self.file_hl = file_hl

    def load_keyword(self, file_al):
        """
        For alphabetic listing
        Load herb URL in alphabetic listing

        :param str file_al: The file name to write the alphabetic listing URL
        """

        self.driver.get(self.start_page)
        element = self.driver.find_elements_by_class_name(
            "form-keyboard-letter")
        for each in element:
            url = each.get_attribute("href")
            if url.startswith("https://www.mskcc.org/cancer-care"):
                self.pages[each.text] = url
            else:
                url = self.domain + url
                self.pages[each.text] = url
        self.write_to_al_file(file_al)

    def write_to_al_file(self, file_al):
        """
        For alphabetic listing
        Write the alphabetic listing URL into a local file: file_al

        :param str file_al: the file name to write the alphabetic listing URL
        """

        print("start writing leading character specific website into file")
        with open(os.path.join(self.path, file_al), "w") as f:
            w = csv.writer(f)
            w.writerows(self.pages.items())
        print("Finished!")

    def write_to_hl_file(self, file_hl):
        """
        For individual herb
        Write the dict, self.herbs, to the local file: file_hl
        self.herbs stores every single herb and the associated URL
        i.e., self.herb["herb_A"]: "herb_A_url_in_MSKCC"

        :param str file_hl: the file name to write the
        """
        with open(os.path.join(self.path, file_hl), "a") as f:
            w = csv.writer(f)
            w.writerows(self.herbs.items())

    def save_to_dict(self, name, link):
        """
        For individual herb
        Save the herb name and the associated URL in self.herbs, a dictionday

        :param str name: individual herb name, i.e. Vitamin E
        :param str link: the extracted herb's URL
        """
        if name not in self.herbs:
            self.herbs[name] = link

    def complete_url(self, link):
        """
        For individual herb
        Complete the extracted herb URL if the URL is not full
        Return the full URL

        :param str link: the extracted herb's URL, from self.extract_url
        :return: full herb URL
        :rtype: str
        """
        if link.startswith("https://www.mskcc.org/cancer-care"):
            return link
        else:
            link = self.domain + link
            return link

    def extract_url(self):
        """
        For individual herb
        Extract herb URL
        """
        element = self.driver.find_elements_by_class_name(
            "baseball-card__link")
        for each in element:
            link = each.get_attribute("href")
            link = self.complete_url(link)
            name = each.text.strip()
            self.save_to_dict(name, link)

    def load_entire_page(self, file_al, file_hl):
        """
        For alphabetic listing
        Load entire page for a specific character
        I.e., load entire page under leading character "A"
        """
        print("Start to extract")
        try:
            with open(os.path.join(self.path, file_al), "r") as f:
                readCSV = csv.reader(f, delimiter=",")
                for row in readCSV:
                    url = row[1]
                    self.driver.get(url)
                    try:
                        while self.driver.find_element_by_link_text("Load More"):  # noqa
                            self.driver.find_element_by_link_text(
                                "Load More").click()
                            self.extract_url()
                    except NoSuchElementException:
                        self.extract_url()
            self.write_to_hl_file(file_hl)
        except IOError:
            print("No such file, generating the file now....")
            self.load_keyword(file_al)
            print("Re-running the function...")
            self.load_entire_page(file_al, file_hl)
        print("Finish extracting")

    def run(self):
        """
        Main function for CancerUrl class
        """
        # find alphabetic listing url
        self.load_keyword(self.file_al)
        # find all ingredient urls
        self.load_entire_page(self.file_al, self.file_hl)
