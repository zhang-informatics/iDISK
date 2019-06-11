import csv
import os
import argparse
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException

class CancerUrl(object):
	"""
	Get MSKCC ingredients URLs by alphabetic listing.
	Save the alphabetic listing file to local as file_al.
	From each URL in fila_al, load the entire page and extract all herbs.
	Save each herb's URL into file_hl
	"""
	def __init__(self, driver, path):
		self.urls = {}
		self.domain = "https://www.mskcc.org/cancer-care"
		self.start_page = "https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs/search"
		# pages that are split by herb leading character
		self.pages = {}
		# url for each herb
		self.herbs = {}
		# driverfunction
		self.driver = driver
		self.path = path

	def parse_arg(self):
		parser = argparse.ArgumentParser()
		parser.add_argument("--file_al", type = str, 
							required = True,
							help = "File to store alphabetic listing URL.")
		parser.add_argument("--file_hl", type = str,
							required = True,
							help = "File to store all MSKCC herb's URLs.")

	def load_keyword(self, file_al):
		"""
		Load herb URL in alphabetic listing

		:param str file_al: The file name to write the alphabetic listing URL
		"""
		self.driver.get(self.start_page)
		element = self.driver.find_elements_by_class_name("form-keyboard-letter")
		for each in element:
			url = each.get_attribute("href")
			if url.startswith("https://www.mskcc.org/cancer-care"):
				self.pages[each.text] = url
			else:
				url = self.domain + url
				self.pages[each.text] = url
		self.write(file_al)

	def write(self, file_al):
		"""
		Write the alphabetic listing URL into a local file. fila_al

		:param str file_al: The file name to write the alphabetic listing URL
		"""
		print("start writing leading character specific website into file")
		with open(os.path.join(self.path, file_al), "w") as f:
			w = csv.writer(f)
			w.writerows(self.pages.items())
		print("Finished!")
	## write herb url to local file
	def writeHerb(self):
		with open(os.path.join(self.path, "cancer_herb_url.csv"), "a") as f:
			w = csv.writer(f)
			w.writerows(self.herbs.items())
	## save to self.herb dict
	def save(self, name, link):
		if name in self.herbs:
			pass
		else:
			self.herbs[name] = link
	## check if url is completed
	def complete(self, link):
		if link.startswith("https://www.mskcc.org/cancer-care"):
			return link
		else:
			link = self.domain + link
			return link
	## extract url information from html
	def extract(self):
		element = self.driver.find_elements_by_class_name("baseball-card__link")
		for each in element:
			link = each.get_attribute("href")
			link = self.complete(link)
			name = each.text.strip()
			self.save(name, link)
	## load each page entirely
	def loadMore(self):
		print("Start to extract")
		try:
			with open(os.path.join(self.path, "cancer_url.csv"), "r") as f:
				readCSV = csv.reader(f, delimiter = ",")
				for row in readCSV:
					url = row[1]
					self.driver.get(url)
					try: 
						while self.driver.find_element_by_link_text("Load More"):
							self.driver.find_element_by_link_text("Load More").click()
							self.extract()
					except NoSuchElementException:
						self.extract()
			self.writeHerb()		
		except IOError:
			print("No such file, generating the file now....")
			self.loadKeyword()
			print("Re-running the function...")
			self.loadMore()
		print("Finish extracting")
	## main function
	def run(self):
		# find alphabetic listing url
		self.loadKeyword()
		# find all ingredient urls
		self.loadMore()


