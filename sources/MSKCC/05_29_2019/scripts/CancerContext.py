import csv
import json
import os
from selenium.common.exceptions import NoSuchElementException


class CancerContext(object):
    """
    Extract section contents for each ingredient
    This is a following-up class for CancerUrl.py
    """
    def __init__(self, driver, path, file_hl, file_con):
        # common headers for each herb
        self.common_header = ["scientific_name", "clinical_summary",
                              "purported_uses", "food_sources",
                              "mechanism_of_action", "warnings",
                              "adverse_reactions", "herb-drug_interactions"]
        # selenium driver, setup in ExtractDriver class
        self.driver = driver
        # local file path to store extracted content
        self.path = path
        # csv file to store all MSKCC herb's URLs
        self.file_hl = file_hl
        # JSONL file to store all pre-defined content
        self.file_con = file_con

    def get_common_name(self):
        """
        Get each herb's common name
        Return a list that has all common names for the herb

        :return: a list that has all common names for the herb
        :rtype: list
        """
        context = self.driver.find_element_by_id("block-mskcc-content")
        # check if the herb has common names
        try:
            value = context.find_element_by_class_name("list-bullets")
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
        context = self.driver.find_elements_by_css_selector("div.mskcc__article:nth-child(5)")  # noqa
        for each in context:
            try:
                # check if the section is For Healthcare Professionals
                each.find_element_by_css_selector("#msk_professional")
                print("under For Healthcare Professionals")
                # find all sections under For Healthcare Professionals
                headers = each.find_elements_by_class_name("accordion ")
                return self.get_pro_content(headers)
            except NoSuchElementException:
                print("ignoring other sections")
                pass

    def get_pro_content(self, headers):
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

    def get_last_update(self):
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

    def write_to_file_con(self, data):
        """
        Write extracted info, data, to local JSONL file, file_con

        :param dict data: a dict that stores all extracted info
        """
        with open(os.path.join(self.path, self.file_con), "a") as output:
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
        with open(os.path.join(self.path, self.file_hl), "r") as f:
            readCSV = csv.reader(f, delimiter=",")
            for row in readCSV:
                # the dict to save all extracted info
                data = {}
                print("========================")
                print("processing: " + row[0])
                data["name"] = row[0]
                # use selenium to open URL
                self.driver.get(row[1])
                sections = self.correct_section()
                # merge sections into data
                # ignore the NoneType created by other sections
                try:
                    for k, v in sections.items():
                        data[k] = v
                except AttributeError:
                    pass
                # get herb's lastest update date
                date = self.get_last_update()
                data["last_updated"] = date
                data["url"] = row[1]
                # get herb's common name(s)
                common_names = self.get_common_name()
                data["common_name"] = common_names
                self.write_to_file_con(data)
