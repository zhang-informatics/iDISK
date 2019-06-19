import csv
import json
import os

from selenium.common.exceptions import NoSuchElementException


"""
The combined script for extracting MSKCC data
class MSKCC_URL: extracting MSKCC data by alphabetic listing,
                 then load each page and extract all herbs from [A-Z]
class MSKCC_Content: extract pre-defiend section contents for each ingredient
"""


class MSKCC_URL(object):
    """
    Get MSKCC ingredients URLs by alphabetic listing.
    Save the alphabetic listing file to local as file_al.
    From each URL in fila_al, load the entire page and extract all herbs.
    Save each herb's URL into file_hl
    """

    def __init__(self, driver, infile_csv, outfile_csv):
        """
        MSKCC_URL class constructor

        :param WebDriver driver: selenium driver, setup in ExtractDriver class
        :param str infile_csv: full path for alphabetic listing csv file
        :param str outfile_csv: full path for each MSKCC herb
        """
        self.urls = {}
        self.domain = "https://www.mskcc.org/cancer-care"  # noqa
        self.start_page = "https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs/search"  # noqa
        # pages that are split by herb leading character
        self.pages = {}
        # url for each herb
        self.herbs = {}
        self.driver = driver
        self.infile = infile_csv
        self.outfile = outfile_csv

    def create_keyword_file(self, infile):
        """
        For alphabetic listing
        Load herb URL in alphabetic listing

        :param str infile: the full path of alphabetic listing URL csv file
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
        self.write_to_alphabetic_listing_csv(infile)

    def write_to_alphabetic_listing_csv(self, infile):
        """
        For alphabetic listing
        Write the alphabetic listing URL into a local file: file_al

        :param str infile: the full path of alphabetic listing URL csv file
        """
        print("start writing leading character specific website into file")
        headers = ["char", "url"]
        # if it is the first time, write header before anything else
        file_exists = os.path.isfile(infile)
        with open(infile, "a") as f:
            w = csv.DictWriter(f, delimiter=",",
                               fieldnames=headers)
            if not file_exists:
                w.writeheader()
            for k, v in self.pages.items():
                w.writerow({"char": k, "url": v})

    def write_to_herb_listing_csv(self, outfile):
        """
        For individual herb
        Write the dict, self.herbs, to the local file: file_hl
        self.herbs stores every single herb and the associated URL
        i.e., self.herb["herb_A"]: "herb_A_url_in_MSKCC"

        :param str outfile: the full path of herb listing URL csv file
        """
        headers = ["herb", "url"]
        # if it is the first time, write header before anything else
        file_exists = os.path.isfile(outfile)
        with open(outfile, "a") as f:
            w = csv.DictWriter(f, delimiter=",",
                               fieldnames=headers)
            if not file_exists:
                w.writeheader()
            for k, v in self.herbs.items():
                w.writerow({"herb": k, "url": v})

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

    def load_entire_page(self, infile, outfile):
        """
        For alphabetic listing
        Load entire page for a specific character
        I.e., load entire page under leading character "A"

        :param str infile: the full path of alphabetic listing URL csv file
        :param str outfile: the full path of herb listing URL csv file
        """
        print("Start to extract")
        # check if the file exists
        if os.path.exists(infile):
            with open(infile, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row["url"]
                    self.driver.get(url)
                    try:
                        while self.driver.find_element_by_link_text("Load More"):  # noqa
                            self.driver.find_element_by_link_text(
                                    "Load More").click()
                            self.extract_url()
                    except NoSuchElementException:
                        self.extract_url()
            self.write_to_herb_listing_csv(outfile)
        else:
            print("No such file, regenrating now...")
            self.create_keyword_file(infile)
            print("Re-running the function...")
            self.load_entire_page(infile, outfile)
        print("Finish extracting.")

    def run(self):
        """
        Main function for CancerUrl class
        """
        # find alphabetic listing url
        self.create_keyword_file(self.infile)
        # find all ingredient urls
        self.load_entire_page(self.infile, self.outfile)


class MSKCC_Content(object):
    """
    Extract section contents for each ingredient
    This is a following-up class for MSKCC_URL.py
    """

    def __init__(self, driver, infile, outfile):
        """
        MSKCC_Content constructor

        :param WebDriver driver: selenium driver, setup in ExtractDriver class
        :param str infile: full path for each herb csv file
                               generated from MSKCC_URL
        :param str outfile: full path for each herb content JSONL file
        """
        # common headers for each herb
        self.common_header = ["scientific_name", "clinical_summary",
                              "purported_uses", "food_sources",
                              "mechanism_of_action", "warnings",
                              "adverse_reactions", "herb-drug_interactions"]
        # selenium driver, setup in ExtractDriver class
        self.driver = driver
        # csv file to store all MSKCC herb's URLs
        self.infile = infile
        # JSONL file to store all pre-defined content
        self.outfile = outfile

    def get_common_name(self):
        """
        Get each herb's common name
        Return a list that has all common names for the herb

        :return: a list that has all common names for the herb
        :rtype: list
        """
        content = self.driver.find_element_by_id("block-mskcc-content")
        # check if the herb has common names
        try:
            value = content.find_element_by_class_name("list-bullets")
            items = value.find_elements_by_tag_name("li")
            names = []
            for each in items:
                names.append(each.text.strip())
            return names
        except NoSuchElementException:
            print("No common names")
            return ""

    def correct_section(self):
        """
        Extract all subsections under For Healthcare Professionals
        Return sections, a dict that stores all required extracted info

        :return: a dict that stores all required extracted info
        :rtype: dict
        """
        content = self.driver.find_elements_by_css_selector("div.mskcc__article:nth-child(5)")  # noqa
        for each in content:
            try:
                # check if the section is For Healthcare Professionals
                each.find_element_by_css_selector("#msk_professional")
                print("under For Healthcare Professionals")
                # find all sections under For Healthcare Professionals
                headers = each.find_elements_by_class_name("accordion ")
                return self.get_content_from_healthcare_professionals(headers)
            except NoSuchElementException:
                print("ignoring other sections")
                return None

    def get_content_from_healthcare_professionals(self, headers):
        """
        Get pre-defined section contents for each For Healthcare Professionals
        Store the required secitons to a dict, sections
        Return sections

        :param WebDriver headers: blocks of herb's info
        :param dict sections:
        :return: a dict that contains all pre-defined sections and contents
        :rtype: dict
        """
        # dict to save required sections
        sections = {}
        # iterate all sections
        for each in headers:
            # find section name: accordion__headline
            section_name = each.find_element_by_class_name("accordion__headline")  # noqa
            section_name = section_name.get_attribute("data-listname").strip()
            section_name = section_name.lower().split(" ")
            section_name = "_".join(section_name)
            # check if the section is needed
            if section_name in self.common_header:
                # find section content
                section_content = each.find_element_by_class_name("field-item")
                # check if the section has bullet points
                try:
                    value = section_content.find_element_by_class_name("bullet-list")  # noqa
                    items = value.find_elements_by_tag_name("li")
                    bullets = []
                    for item in items:
                        bullets.append(item.text.strip())
                    sections[section_name] = bullets
                except NoSuchElementException:
                    sections[section_name] = section_content.text.strip()
        # check if there is any missing headers
        res = set(self.common_header) - set(sections.keys())
        for each in res:
            sections[each] = ""
        return sections

    def get_last_updated_date(self):
        """
        Find the date the the herb is last updated
        Return date

        :return: latest update date
        :rtype: str
        """
        section = self.driver.find_element_by_xpath('//*[@id="field-shared-last-updated"]')  # noqa
        date = section.find_element_by_class_name("datetime")
        date = date.get_attribute("datetime")
        return date

    def write_to_output_file(self, data):
        """
        Write extracted info, data, to local JSONL file, file_con

        :param dict data: a dict that stores all extracted info
        """
        with open(self.outfile, "a") as output:
            json.dump(data, output)
            output.write("\n")

    def process_file(self):
        """
        For every line in file_hl, do:
        1. Use selenium driver to open the herb's URL
        2. Save each extracted info to a dict
        3. Save the dict to local JSONL file, file_con
        """
        # open the file_hl
        with open(self.infile, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # the dict to save all extracted info
                data = {}
                print("========================")
                print("processing: " + row["herb"])
                data["name"] = row["herb"]
                # use selenium to open URL
                self.driver.get(row["url"])
                sections = self.correct_section()
                # merge sections into data
                # ignore the NoneType created by other sections
                try:
                    for k, v in sections.items():
                        data[k] = v
                except AttributeError:
                    pass
                # get herb's lastest update date
                date = self.get_last_updated_date()
                data["last_updated"] = date
                data["url"] = row["url"]
                # get herb's common name(s)
                common_names = self.get_common_name()
                data["common_name"] = common_names
                self.write_to_output_file(data)
