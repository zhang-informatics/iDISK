import csv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
## extracting url for each 
class cancer_url(object):
	def __init__(self):
		self.urls = {}
		self.domain = "https://www.mskcc.org/cancer-care"
		self.start_page = "https://www.mskcc.org/cancer-care/diagnosis-treatment/symptom-management/integrative-medicine/herbs/search"
		## pages that are split by herb leading character
		self.pages = {}
		## url for each herb
		self.herbs = {}
	## setup selenium webdriver
	def driverSetup(self):
		options = Options()
		## do not open firefox 
		options.add_argument("--headless")
		driver = webdriver.Firefox(executable_path = "/usr/local/bin/geckodriver", options = options)
		return driver
	## iterate by leading character
	def loadKeyword(self, driver):
		driver.get(self.start_page)
		element =  driver.find_elements_by_class_name("form-keyboard-letter")
		for each in element:
			url = each.get_attribute("href")
			if url.startswith("https://www.mskcc.org/cancer-care"):
				self.pages[each.text] = url
			else:
				url = self.domain + url
				self.pages[each.text] = url
		self.write()
		driver.close()
	## get href in the html class
	def getHref(self, item):
		return item.get_attribute("href")
	## write urls to file
	def write(self):
		print("start writing leading character specific website into file")
		with open("cancer_url.csv", "w") as f:
			w = csv.writer(f)
			w.writerows(self.pages.items())
		print("Finished!")
	## write herb url to local file
	def writeHerb(self):
		with open("cancer_herb_url.csv", "a") as f:
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
	def extract(self, driver):
		element = driver.find_elements_by_class_name("baseball-card__link")
		for each in element:
			link = each.get_attribute("href")
			link = self.complete(link)
			name = each.text.strip()
			self.save(name, link)
	## load each page entirely
	def loadMore(self, driver):
		print("Start to extract")
		try:
			with open("cancer_url.csv", "r") as f:
				readCSV = csv.reader(f, delimiter = ",")
				for row in readCSV:
					url = row[1]
					driver.get(url)
					try: 
						while driver.find_element_by_link_text("Load More"):
							driver.find_element_by_link_text("Load More").click()
							self.extract(driver)
					except NoSuchElementException:
						self.extract(driver)
			self.writeHerb()					
		except IOError:
			print("No such file, generating the file now....")
			self.loadKeyword(driver)
			print("Re-running the function...")
			self.loadMore(driver)
		print("Finish extracting")
	## main function
	def run(self):
		driver = self.driverSetup()
		driver.implicitly_wait(5)
		self.loadMore(driver)



x = cancer_url()
x.run()


