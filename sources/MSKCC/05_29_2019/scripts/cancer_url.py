import csv
import os
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
# extracting url for each alphabetic listing page
# from each alphabetic listing page, extracting all ingredients
class cancer_url(object):
	def __init__(self, driver, path):
		self.urls = {}
		self.domain = "https://www.mskcc.org/cancer-care"
		self.start_page = "https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs/search"
		## pages that are split by herb leading character
		self.pages = {}
		## url for each herb
		self.herbs = {}
		## driverfunction
		self.driver = driver
		self.path = path
	## iterate by leading character
	def loadKeyword(self):
		self.driver.get(self.start_page)
		element = self.driver.find_elements_by_class_name("form-keyboard-letter")
		for each in element:
			url = each.get_attribute("href")
			if url.startswith("https://www.mskcc.org/cancer-care"):
				self.pages[each.text] = url
			else:
				url = self.domain + url
				self.pages[each.text] = url
		self.write()
	## get href in the html class
	def getHref(self, item):
		return item.get_attribute("href")
	## write urls to file
	def write(self):
		print("start writing leading character specific website into file")
		with open(os.path.join(self.path, "cancer_url.csv"), "w") as f:
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


