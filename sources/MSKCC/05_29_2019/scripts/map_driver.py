# driver function for annotation process
from umlsAnn import umlsAnn
from meddraAnn import meddraAnn
import json
import os
class driver(object):
	def __init__(self, location):
		# MetaMap location
		self.location = location
		# get this python script location
		self.path = self.path = os.path.dirname(os.getcwd())
		self.path = os.path.join(self.path, "download")
		# stored MSKCC data
		self.read_file = "cancer_herb_content.jsonl"
		# remove "herb-drug_interactions", "adverse_reactions", "purported_uses" for specific pre-processing
		self.headers = ["contraindications", "last_updated", "common_name", "scientific_name", "warnings", "clinical_summary", "food_sources", "mechanism_of_action"]
		# overlap ingredients
		self.overlap_herbs = ["Andrographis", "Blue-Green Algae", "Bromelain", "Butterbur"
							"Calcium", "Cranberry", "Elderberry", "Fenugreek",
                              "Flaxseed", "Folic Acid", "Ginkgo", "Grape",
                              "Hops", "Indole-3-Carbinol", "Kudzu", "L-Arginine",
                              "L-Tryptophan", "Melatonin", "N-Acetyl Cysteine", "Pomegranate",
                              "Red Clover", "Reishi Mushroom", "Shiitake Mushroom", "Siberian Ginseng",
                              "Turmeric", "Vitamin B12", "Vitamin E", "Vitamin K",
                              "Blue-green Algae", "Folate", "Grape seeds", "Arginine",
                              "5-HTP", "N-Acetylcysteine"]
	def readFile(self):
		meddra = meddraAnn()
		mm = umlsAnn(self.location, self.path)
		mm.start()
		with open(os.path.join(self.path, self.read_file), "r") as f:
			for line in f:
				data = {}
				herb = json.loads(line)
				name = herb["name"]
				data["name"] = name
				print("-----------------")
				print(name)
				# get annotations
				hdi_content = herb["herb-drug_interactions"]
				data["HDI"] = hdi_content
				data["annotated_HDI"] = mm.process(name, hdi_content, "HDI")
				pu_content = herb["purported_uses"]
				data["PU"] = pu_content
				data["annotated_PU"] = mm.process(name, pu_content, "PU")
				adr_content = herb["adverse_reactions"]
				data["ADR"] = adr_content
				data["annotated_ADR"] = meddra.main(adr_content)
				# rest components
				for item in self.headers:
					data[item] = herb[item]
				print("-----------------")
				self.write(data, "cancer_ann_data.jsonl")
				
	## write to local file
	def write(self, data, outptu_file):
		with open(os.path.join(self.path, outptu_file), "a") as output:
			json.dump(data, output)
			output.write("\n")
	# main function
	def run(self):
		self.readFile()
	# test function
	def test(self):
		meddra = meddraAnn()
		mm = umlsAnn(self.location, self.path)
		mm.start()
		with open(os.path.join(self.path, self.read_file), "r") as f:
			for line in f:
				data = {}
				herb = json.loads(line)
				name = herb["name"]
				data["name"] = name
				if name in self.overlap_herbs:
					print("-----------------")
					print(name)
					'''
					# get annotations
					hdi_content = herb["herb-drug_interactions"]
					data["HDI"] = hdi_content
					data["annotated_HDI"] = mm.process(name, hdi_content, "HDI")
					pu_content = herb["purported_uses"]
					data["PU"] = pu_content
					data["annotated_PU"] = mm.process(name, pu_content, "PU")
					print("annotated hdi: ")
					pprint(data["annotated_HDI"])
					print("\n")
					print("annotated pu: ")
					pprint(data["annotated_PU"])
					print("-----------------")
					self.write(data, "test.jsonl")
					'''
					adr_content = herb["adverse_reactions"]
					data["ADR"] = adr_content
					data["annotated_ADR"] = meddra.main(adr_content)
					self.write(data, "test.jsonl")
					print("-----------------")
	
if __name__ == "__main__":
    x = driver("/Users/Changye/Documents/workspace/public_mm")
    x.run()


