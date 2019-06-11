import os
import subprocess
from operator import itemgetter
import re
import pandas as pd
import json
# get UMLS annotation for HDI, contradictions and purposed uses


class umlsAnn(object):
    def __init__(self, location, path):
        # MetaMap location
        #self.location = "/Users/Changye/Documents/workspace/public_mm"
        self.location = location
        # get this python script location
        self.path = path
    # start MM server

    def start(self):
        os.chdir(self.location)
        output = subprocess.check_output(["./bin/skrmedpostctl", "start"])
        print(output.decode("utf8"))
    # get MM command
    # @value: content to be annotated
    # @additional: additional command to be added
    # @relax: true if use relax model for term processing
    # return MM commands
    # TODO: add more supported commands

    def getComm(self, value, additional="", relax=True):
        if relax:
            command = "echo " + value + " | " + "./bin/metamap16" + " -I " + "-Z 2018AB -V Base --relaxed_model " + \
                "--silent " + "--ignore_word_order" + " " + additional +  "--term_processing " + "--JSONn"
            return command
        else:
            command = "echo " + value + " | " + "./bin/metamap16" + " -I " + "-Z 2018AB -V Base " + \
                "--silent " + "--ignore_word_order" + " " + additional +  "--term_processing " + "--JSONn"
            return command

    # get annotated terms using UMLS without output format
    # @command: full command from @getComm function
    # return MM output

    def getAnn(self, command):
        # echo lung cancer | ./bin/metamap16 -I
        # check if value is valid
        output = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE).stdout.read()
        return output

    # remove all non-ASCII characters in the content
    # remove contents inside of ()
    # @value: the content needs to be cleaned

    def remove(self, value):
        if isinstance(value, list):
            value = [re.sub(r'[^\x00-\x7F]+', " ", each) for each in value]
            value = [re.sub(r" \([^)]*\)", "", each) for each in value]
            return value
        else:
            value = re.sub(r'[^\x00-\x7F]+', " ", value)
            value = re.sub(r" \([^)]*\)", "", value)
        return value

    # get content before ":"
    # @content: content need to be split
    # return a list of contents that are before ":"

    def getBefore(self, content):
        if isinstance(content, list):
            value = [each.split(":")[0] for each in content]
            return value
        else:
            value = content.split("\n")
            value = [each.split(":")[0] for each in value]
        return value

    # split HDI content with "/" or ","
    # @content: herb["herb-drug_interacitons"]
    # return separate HDI content as list

    def SplitContent(self, content):
        if isinstance(content, list):
            split_content = []
            for each in content:
                if "/" in each:
                    items = each.split("/")
                    split_content.extend(items)
                elif "," in each:
                    items = each.split(",")
                    split_content.extend(items)
                else:
                    split_content.append(each)
            return split_content
        else:
            return content

    # read MM type file
    # @fun: annotation section names, i.e. PU, HDI
    # each section will return a list of MM types

    def readTypes(self, fun):
        full_types = pd.read_csv(os.path.join(self.path, "mmtypes.txt"),
                                 sep="|", header=None, index_col=False)
        full_types.columns = ["abbrev", "name", "tui", "types"]
        if fun.upper() not in ["HDI", "PU"]:
            raise ValueError("Currently only supports HDI and PU")
        else:
            # hdi mm types
            if fun.upper() == "HDI":
                hdi_types = pd.read_csv(
                    os.path.join(self.path, "hdi_types.txt"),
                    sep="|", header=None, index_col=False)
                hdi_types.columns = ["group", "group_name", "tui", "types"]
                hdi_types = hdi_types["tui"].values.tolist()
                hdi = full_types.loc[full_types["tui"].isin(hdi_types)]
                return hdi["types"].values.tolist()
            # pu mm types
            if fun.upper() == "PU":
                pu_types = pd.read_csv(
                    os.path.join(self.path, "pu_types.txt"),
                    sep="|", header=None, index_col=False)
                pu_types.columns = ["group", "group_name", "tui", "types"]
                pu_types = pu_types["tui"].values.tolist()
                pu = full_types.loc[full_types["tui"].isin(pu_types)]
        return pu["types"].values.tolist()

    # select qualified items from MM output
    # @mp: single MM mapping output, in dict format
    # types: a list of sematic types

    # subprocess function for HDI and PU
    # @item: the term needs to be processed
    # @types: a list of semantic types
    def subProcess(self, item):
        comm = self.getComm(item)
        ann = self.getAnn(comm).decode("utf8")
        ## remove MetaMap command
        ann = ann.split("\n")[1]
        ann = json.loads(ann)
        print(item)
        ann = ann["AllDocuments"]
        for each in ann:
            doc = each["Document"]
            # find the mapping phrase
            mapping = doc["Utterances"][0]["Phrases"][0]["Mappings"]
            # only one or no mapping
            if len(mapping) == 1 or len(mapping) == 0:
                pass
            else:
                # multiple mappings
                for mp in mapping:
                    print(mp["MappingCandidates"][0])

    # a new process function for HDI and PU
    # @name: herb name
    # @content: section content
    # @fun: a string to decide which content is to be processed, i.e. "HDI" or "PU"
    def process(self, name, content, fun):
        if fun.upper() not in ["HDI", "PU"]:
            raise ValueError("Currently only supports HDI and PU")
        else:
            ## HDI process
            if fun.upper() == "HDI":
                content = self.remove(self.getBefore(content))
                content = self.SplitContent(content)
                hdi_types = self.readTypes("HDI")
                hdi_types = [x.lower() for x in hdi_types]
                if not content:
                    return " "
                else:
                    if isinstance(content, list):
                        for each in content:
                            self.subProcess(each)
                    else:
                        self.subProcess(content)

            ## PU process
            else:
                pass