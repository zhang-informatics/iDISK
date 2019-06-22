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

    def __init__(self, driver):
        """
        MSKCC_URL class constructor

        :param WebDriver driver: selenium driver, setup in ExtractDriver class
        :param str infile_csv: full path for alphabetic listing csv file
        :param str outfile_csv: full path for each MSKCC herb
        """
        self.domain = "https://www.mskcc.org/cancer-care"  # noqa
        self.start_page = "https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs/search"  # noqa
        # pages that are split by herb leading character
        self.pages = {}
        # url for each herb
        self.herbs = {}
        self.driver = driver

    def create_keyword_file(self):
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
            if name not in self.herbs:
                self.herbs[name] = link

    def load_entire_page(self):
        """
        For alphabetic listing
        Load entire page for a specific character
        I.e., load entire page under leading character "A"
        """
        print("Start to extract")
        for char, url in self.pages.items():
            print("Currently processing leading char: " + char)
            self.driver.get(url)
            # load all page
            try:
                while self.driver.find_element_by_link_text("Load More"):  # noqa
                    self.driver.find_element_by_link_text(
                                    "Load More").click()
                    self.extract_url()
            except NoSuchElementException:
                self.extract_url()
        print("Finish extracting.")

    def get_herb_url(self):
        """
        Main function for MSKCC_URL class
        Return self.herbs that follows the below format
        self.herbs["herb_a"] = "herb_a's url"

        :return: dict that contains each herb's URL
        :rtype: dict
        """
        # find alphabetic listing url
        self.create_keyword_file()
        # find all ingredient urls
        self.load_entire_page()
        return self.herbs


class MSKCC_Content(object):
    """
    Extract section contents for each ingredient
    This is a following-up class for MSKCC_URL.py
    """

    def __init__(self, driver):
        """
        MSKCC_Content constructor

        :param WebDriver driver: selenium driver, setup in ExtractDriver class
        :param dict herbs: MSKCC herb and its URL, generated from MSKCC_URL
        :param str outfile: full path for each herb content JSONL file
        """
        # common headers for each herb
        self.common_header = ["scientific_name", "clinical_summary",
                              "purported_uses", "food_sources",
                              "mechanism_of_action", "warnings",
                              "adverse_reactions", "herb-drug_interactions"]
        # selenium driver, setup in ExtractDriver class
        self.driver = driver

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

    def get_content_from_url(self, herb_name, url):
        """
        For every line in herb_file, do:
        1. Use selenium driver to open the herb's URL
        2. Save each extracted info to a dict
        3. Return the dict

        :return: the dict that contains required content
        :rtype: dict
        """
        data = {}
        data["herb_name"] = herb_name
        data["url"] = url
        print("---------------------")
        print("Currently processing herb: " + herb_name)
        self.driver.get(url)
        sections = self.correct_section()
        # merge sections into data
        if sections is not None:
            data.update(sections)
        data["last_updated_date"] = self.get_last_updated_date()
        data["common_name"] = self.get_common_name()
        print("---------------------")
        return data
