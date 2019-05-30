import csv
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from collections import Counter
# counting all section to find the required ones
class cancer_header(object):
	def __init__(self):
		self.herb = "cancer_herb_url.csv"
		## header names
		self.headers = []
	def driverSetup(self):
		options = Options()
		## do not open firefox 
		options.add_argument("--headless")
		driver = webdriver.Firefox(executable_path = "/usr/local/bin/geckodriver", options = options)
		return driver
	## extract all headers
	def extractHeader(self, driver):
		print("Extracting headers")
		headers = driver.find_elements_by_class_name("accordion__headline")
		for each in headers:
			name = each.get_attribute("data-listname")
			self.headers.append(name.strip())
	## write to files
	def write(self):
		print("Writing to files....")
		with open("cancer_herb_header.csv", "w") as f:
			w = csv.writer(f)
			w.writerows(Counter(self.headers).items())
		print("Finish writing")
	## main function
	def run(self):
		driver = self.driverSetup()
		driver.implicitly_wait(1)
		try:
			with open("cancer_herb_url.csv", "r") as f:
				readCSV = csv.reader(f, delimiter = ",")
				for row in readCSV:
					print("Extracting " + row[0] + " headers")
					driver.get(row[1])
					self.extractHeader(driver)
					print("=====================================")
			self.write()
		except IOError:
			print("No such file, please run cancer_url.py first")
		driver.close()

x = cancer_header()
x.run()
