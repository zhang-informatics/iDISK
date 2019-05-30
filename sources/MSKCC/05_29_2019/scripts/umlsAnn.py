import os
import subprocess
from operator import itemgetter
import re
import pandas as pd
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
        print(output)
    # get MM command
    # @value: content to be annotated
    # @additional: additional command to be added
    # @relax: true if use relax model for term processing
    # return MM commands
    # TODO: add more supported commands

    def getComm(self, value, additional="", relax=True):
        if relax:
            command = "echo " + value + " | " + "./bin/metamap16" + " -I " + "-Z 2018AB -V Base --relaxed_model " + \
                "--silent " + "--ignore_word_order" + additional  # +  "--term_processing "
            return command
        else:
            command = "echo " + value + " | " + "./bin/metamap16" + " -I " + "-Z 2018AB -V Base " + \
                "--silent " + "--ignore_word_order" + additional  # +  "--term_processing "
            return command

    # get annotated terms using UMLS without output format
    # @command: full command from @getComm function
    # return MM output, split by "\n"

    def getAnnNoOutput(self, command):
        # echo lung cancer | ./bin/metamap16 -I
        # check if value is valid
        output = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE).stdout.read()
        return output

    # concate list of string into single string
    # @value: content to be concated
    # @sep: separator, i.e. "\t", "\n", " "

    def concate(self, value, sep):
        if isinstance(value, list):
            return (sep.join(value))
        else:
            return value
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

    # flatten nested list
    # @patterns: nested list, extracted suing re.findall(r'\[(.*?)\]', s)
    # return unique flattened list
    def flatten(self, patterns):
        # check if the list is nested
        if all(isinstance(i, list) for i in patterns):
            patterns = [item for sublist in patterns for item in sublist]
            patterns = list(set(patterns))
            patterns = list(filter(None, patterns))
            return patterns
        else:
            return patterns

    # check if a list is a subset of another list
    # @list1: shorter list
    # @list2: longer list
    # return true if list1 is a subset of list2, otherwise false

    def isSubset(self, list1, list2):
        return all(elem in list2 for elem in list1)

    # select MM annotated term based on list elements
    # @output: list of MM output, split by "\n"
    # return a list of annotated terms
    def selectChunks(self, output):
        chunk = [each for each in output if not each.startswith("Processing")]
        chunk = [each for each in chunk if not each.startswith("Phrase")]
        chunk = [each for each in chunk if not each.startswith("Meta Mapping")]
        chunk = list(filter(None, chunk))
        chunk = [each.lstrip() for each in chunk]
        chunk = [each for each in chunk if each != " "]
        #chunk = [self.remove(each) for each in chunk]
        return chunk

    # split semantic types string into list
    # specifically for HDI content
    # @patterns: extracted semantic types strings

    def getSplitHDI(self, patterns):
        new_patterns = []
        for each in patterns:
            if isinstance(each, list):
                new_patterns.extend(each)
            if isinstance(each, str):
                new_patterns.append(each)
        new_patterns = list(set(new_patterns))
        res = []
        for each in new_patterns:
            if "Amino Acid, Peptide, or Protein" in each:
                each = each.replace("Amino Acid, Peptide, or Protein", "")
                res.append("Amino Acid, Peptide, or Protein")
                res.append(each.split(",")[-1])
            elif "Element, Ion, or Isotope" in each:
                each = each.replace("Element, Ion, or Isotope", "")
                res.append("Element, Ion, or Isotope")
                res.append(each.split(",")[-1])
            elif "Indicator, Reagent, or Diagnostic Aid" in each:
                each = each.replace(
                    "Indicator, Reagent, or Diagnostic Aid", "")
                res.append("Indicator, Reagent, or Diagnostic Aid")
                res.append(each.split(",")[-1])
            elif "Nucleic Acid, Nucleoside, or Nucleotide" in each:
                each = each.replace(
                    "Nucleic Acid, Nucleoside, or Nucleotide", "")
                res.append("Nucleic Acid, Nucleoside, or Nucleotide")
                res.append(each.split(",")[-1])
            else:
                res.extend(each.split(","))
        return res

    # split semantic type into list
    # @patterns: extracted semantic types
    # return split patterns

    def getSplit(self, patterns):
        patterns = list(filter(None, patterns))
        if len(patterns) == 1:
            return patterns
        else:
            new_patterns = []
            for each in patterns:
                if isinstance(each, list):
                    new_patterns.append(each[0])
                else:
                    new_patterns.append(each)
            return new_patterns

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


    # get MM chunks that have required semantic types
    # @output: MM output
    # @types: required semantic types, in list format
    # @splitFunction: the function to split MM semantic types
    # return all qualified MM output

    def limit(self, chunks, types, splitFunction):
        # if there is no such MM output
        if not chunks:
            print("No valid MM output chunk")
            return " "
        else:
            # if there is only one term in the chunk
            if len(chunks) == 1:
                s = chunks[0]
                patterns = re.findall(r'\[(.*?)\]', s)
                patterns = splitFunction(patterns)
                #patterns = self.flatten(patterns)
                # check if the annotated term has required semantic types
                if self.isSubset(patterns, types):
                    return s
                else:
                    print("no terms match required semantic types")
                    return " "
            # if there are multiple terms in the chunk
            else:
                qualified_terms = []
                for each in chunks:
                    patterns = re.findall(r'\[(.*?)\]', each)
                    patterns = splitFunction(patterns)
                    #patterns = self.flatten(patterns)
                    if self.isSubset(patterns, types):
                        qualified_terms.append(each)
                return qualified_terms

    # select term with max score
    # if has the same max score, select the term with more semantic types
    # @terms: a list of output from self.limit() function
    # return qualified terms

    def qualified(self, terms):
        # if current term is empty, i.e. last few lines in MM output
        if not terms:
            return " "
        else:
            scores = [re.findall(r"^\d+", each) for each in terms]
            scores = [each[0] for each in scores]
            max_index = [index for index, value in enumerate(
                                    scores) if value == max(scores)]
            temp_term1 = itemgetter(*max_index)(terms)
            # if has a single max score
            if len(temp_term1) == 1:
                if isinstance(temp_term1, tuple):
                    return temp_term1[0]
                else:
                    return temp_term1
            else:
                # find term with most number of semantic types
                patterns = [re.findall(r'\[(.*?)\]', each) for each in temp_term1]
                lens = [len(each) for each in patterns]
                # if all terms have same number of semantic types
                if len(set(lens)) == 1:
                    if isinstance(temp_term1, tuple):
                        return temp_term1[0]
                    else:
                        return temp_term1
                else:
                    max_len = [index for index, value in enumerate(
                                    lens) if value == max(lens)]
                    final_term = itemgetter(*max_len)(temp_term1)
                    return final_term

    # output selection main function
    # @output: MM output, in string format
    # @splitFun: split function for MM output semantic types
    # return qualified terms

    def outputHelper(self, output, types, splitFun):
        # remove first line
        output = output.split("\n")[1:]
        chunks = self.selectChunks(output)
        terms = self.limit(chunks, types, splitFun)
        if isinstance(terms, str):
            return terms
        elif isinstance(terms, list):
            return self.qualified(terms)
        else:
            return " "

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

    # find mapped word
    # @content: MM input word
    # @term: MM output
    # return the mapped word, with the structured format
    def findMapping(self, term, content):
        s = term.split(":")
        # check if it's a valid output
        if len(s) == 1:
            return " "
        else:
            # find mapping id
            ids = s[0].split(" ")[-1]
            # find semantic types
            semantic = re.findall(r'\[(.*?)\]', s[1])
            # remove () and [] area
            # find mapping word
            res = re.sub(r" ?\([^)]+\)", "", s[1])
            res = re.sub(r" \[(.*?)\]", "", res)
            # check if any addition brackets left
            if ")" in res:
                res = res.replace(")", "").rstrip()
                d = {"term": res.lstrip("-"), "id": ids, "source_db": "umls", "original_string": content, "semtype": semantic}
                return d
            elif "(" in res:
                res = res.replace("(", "").rstrip()
                d = {"term": res.lstrip("-"), "id": ids, "source_db": "umls", "original_string": content, "semtype": semantic}
                return d
            else:
                res = res.rstrip()
                d = {"term": res.lstrip("-"), "id": ids, "source_db": "umls", "original_string": content, "semtype": semantic} 
                return d

    # strcture the output as
    '''
    "annotated_ADR": [
        {"term": dermatitis, "id": 10012431, "source_db": meddra, "original_string": Dermatitis},
        {"term": nausea, "id": 10028813, "source_db": meddra, "original_string": nausea},
        ...
    ]
    '''
    # @content: the input value for MM
    # @anno_terms: seletected MM output
    # return a list of dictionary, or an empty dict, in the structure as desribed above
    def structure(self, content, anno_terms):
        # check if anno_terms is empty
        if not anno_terms:
            return " "
        else:
            better_strcture = []
            if isinstance(anno_terms, list):
                for each in anno_terms:
                    # if the term is already annotated
                    if isinstance(each, dict):
                        better_strcture.append(each)
                    else:
                        d = self.findMapping(each, content)
                        better_strcture.append(d)
            else:
                s = anno_terms.split(":")
                # not a valid output
                if len(s) == 1:
                    return " "
                else:
                    d = self.findMapping(anno_terms, content)
                    better_strcture.append(d)
            return better_strcture
    
    # remove duplicated mapping output for HDI
    # remove the record if the mapping word is same as the herb name
    # @anno: a list of structured output from self.structure()
    # @name: herb name
    def duplicateHDI(self, anno, name):
        final_output = []
        for each in anno:
            # check if each anno term is structured 
            if isinstance(each, dict):
                if each["term"].lower() != name.lower():
                    final_output.append(each)
            else:
                final_output.append(each)
        return final_output

    # structure helper function
    # @each: the input value for MM
    # @anno: selected MM output
    # @anno_terms: list for storing sturctured annotated output
    # return a list of structured annotated output
    def struHelper(self, each, anno, anno_terms):
        if isinstance(anno, list):
            better_anno = self.structure(each, anno)
            if isinstance(better_anno, list):
                anno_terms.extend(better_anno)
            else:
                anno_terms.append(better_anno)
        else:
            better_anno = self.structure(each, anno)
            if isinstance(better_anno, list):
                anno_terms.extend(better_anno)
            else:
                anno_terms.append(better_anno)
        return anno_terms

    # annotation with list content process
    # @content: section content, in list format
    # @types: a list of required semantic types
    # @splitFun: content split function
    # return a list of annotated terms
    def listAnn(self,content, types, splitFun):
        anno_terms = []
        for each in content:
            command = self.getComm(each, additional = " --term_processing")
            output = self.getAnnNoOutput(command).decode("utf-8")
            anno = self.outputHelper(output, types, splitFun)
            self.struHelper(each, anno, anno_terms)
        return anno_terms
    
    # annotation with string content process
    # @content: section content, in list format
    # @types: a list of required semantic types
    # @splitFun: content split function
    # return a list of annotated terms
    def strAnn(self, content, types, splitFun):
        anno_terms = []
        content = content.split("\n")
        # if the content cannot be split by newline
        if len(content) == 1:
            command = self.getComm(content[0], additional = " --term_processing")
            output = self.getAnnNoOutput(command).decode("utf-8")
            anno = self.outputHelper(output, types, splitFun)
            self.struHelper(content[0], anno, anno_terms)
        # there are multiple items in the content
        else:
            anno = self.listAnn(content, types, splitFun)
            self.struHelper(content, anno, anno_terms)
        return anno_terms

    # a new process function for HDI and PU
    # @name: herb name
    # @content: section content
    # @fun: a string to decide which content is to be processed, i.e. "HDI" or "PU"
    def process(self, name, content, fun):
        # HDI process
        if fun.upper() == "HDI":
            content = self.remove(self.getBefore(content))
            content = self.SplitContent(content)
            hdi_types = self.readTypes("HDI")
            # check if content is empty
            if not content:
                return " "
            else:
                anno_terms = []
                if isinstance(content, list):
                    anno = self.listAnn(content, hdi_types, self.getSplitHDI)
                    anno_terms.extend(anno)
                else:
                    anno = self.strAnn(content, hdi_types, self.getSplitHDI)
            anno_terms = self.duplicateHDI(anno_terms, name)
            return anno_terms
        # PU process
        elif fun.upper() == "PU":
            content = self.remove(content)
            pu_types = self.readTypes("PU")
            # check if content is empty
            if not content:
                return " "
            else:
                anno_terms = []
                if isinstance(content, list):
                    anno = self.listAnn(content, pu_types, self.getSplit)
                    anno_terms.extend(anno)
                else:
                    anno = self.strAnn(content, pu_types, self.getSplit)
                    anno_terms.extend(anno)
            return anno_terms
        else:
            raise ValueError("Currently only supports HDI and PU")
