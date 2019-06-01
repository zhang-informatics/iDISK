import os
import subprocess
import re
import json


class MetaMapDriver(object):
    """
    Class to start and use a MetaMap instance from within Python.

    :param str mm_bin: path to MetaMap bin/ directory.
    :param str data_year: corresponds to the -V option. E.g. '2018AA'
    :param str data_version: corresponds to the -Z option. E.g. 'Base'
    """

    def __init__(self, mm_bin, data_year="2018AB", data_version="Base"):
        self.mm_bin = mm_bin
        self.metamap = os.path.join(self.mm_bin, "metamap16")
        self.data_year = data_year
        self.data_version = data_version
        self._start()

    def _start(self):
        """
        Start the MetaMap servers.
        """
        print("Starting tagger server.")
        tagger_server = os.path.join(self.mm_bin, "skrmedpostctl")
        tagger_out = subprocess.check_output([tagger_server, "start"])
        print(tagger_out.decode("utf-8"))
        print("You may want to start the WSD server before continuing.")
        print(f"  Run {self.mm_bin}/wsdserverctl start")

    def _clean_data(self, data):
        """
        Remove all non-ASCII characters in the content and
        remove content inside of ().

        :param data list(str): A list of strings to clean.
        """
        cleaned = []
        for d in data:
            d = re.sub(r'[^\x00-\x7F]+', " ", d)
            d = re.sub(r" ?\([^)]+\)", "", d)
            cleaned.append(d)
        return cleaned

    def _get_call(self, inputs, options=None, relaxed=True):
        """
        Build the command line call to MetaMap.

        :param inputs str: newline delimited list of terms to map.
        :param options str: any additional arguments to pass to MetaMap
                            (default None).
        :param relaxed bool: If True, use the --relaxed_model (default True).
        :returns: MetaMap call
        :rtype: str
        """
        id_match = re.match(r'.+\|.+', inputs.split('\n')[0])
        if id_match is None:
            msg = "input does not seem to contain IDs. \
                   Should be of the form 'ID|STRING'."
            warnings.warn(msg)
        args = [f"-Z {self.data_year}",
                f"-V {self.data_version}",
                "--silent",  # Don't show logging/version info
                "--term_processing",  # Process term by term
                "--ignore_word_order",
                "--sldiID",  # Single line delimited input with IDs
                "--JSONn"]  # Output unformatted JSON
        if relaxed is True:
            args.append("--relaxed_model")
        if options is not None:
            args.append(options)
        args_str = ' '.join(args)

        call = f"echo '{inputs}' | {self.metamap} {args_str}"
        return call

    def _run_call(self, call):
        """
        Run the MetaMap call.

        :param call str: MetaMap call. Output of self.get_call()
        :returns: The call and the output of the call.
        :rtype: tuple(str, str)
        """

        res = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
        output = res.stdout.read().decode("utf-8")
        output = json.loads(output.split('\n', maxsplit=1)[1])
        return output

    def _process_output(self, output, keep_semtypes={}):
        """
        Format the JSON output by MetaMap into something a bit
        more accessible. Outputs a dictionary of {term: candidate_mapping}.

        :param output dict: JSON formatted output from self.run_call()
        :param keep_semtypes list: dictionary of the form
                                   {input_term: [semtypes, [...]]} for each
                                   input term. If an input term is missing,
                                   does not filter the concepts for that term.
        :returns: dictionary of best candidate mappings, one for each line.
        :rtype: dict
        """
        all_mappings = {}
        docs = output["AllDocuments"]
        for doc in docs:
            utt = doc["Document"]["Utterances"][0]
            intext = utt["UttText"]
            mappings = [m for p in utt["Phrases"] for m in p["Mappings"]]
            candidates = [c for m in mappings for c in m["MappingCandidates"]]
            # Filter candidates on semantic types
            if intext in keep_semtypes:
                types = set(keep_semtypes[intext])
                candidates = [c for c in candidates
                              if len(types & set(c["SemTypes"])) > 0]
            all_mappings[intext] = candidates
        return all_mappings

    def map(self, input_strings, keep_semtypes={}):
        """
        Map an input string or list of strings to UMLS concepts.

        :param input_strings list: list of strings to input to MetaMap
        :param keep_semtypes list: list of strings of semantic types to keep.
        :returns: mapping from input to UMLS concepts
        :rtype: dict
        """
        if type(keep_semtypes) is not dict:
            raise ValueError("keep_semtypes must be a dict")
        if type(input_strings) == str:
            input_strings = [input_strings]

        clean = self._clean_data(input_strings)
        indata = '\n'.join(clean)
        call = self._get_call(indata)
        output = self._run_call(call)
        mappings = self._process_output(output, keep_semtypes)
        return mappings

    def get_best_mappings(self, mappings, min_score=800):
        """
        Returns the candidate mapping with the highest score
        for each input term.
        Warning! If two or more concepts are tied, one will
        be returned at random.

        :param mappings dict: dict of candidate mappings. Output of self.map.
        :param min_score int: minimum candidate mapping score to accept.
        :returns: The best candidate mapping for each input term.
        :rtype: dict
        """
        if type(mappings) is not dict:
            raise ValueError(f"Unsupported input type '{type(mappings)}.")

        all_concepts = {}
        for (term, candidates) in mappings.items():
            best_score = float("-inf")
            best_candidate = None
            for c in candidates:
                score = abs(int(c["CandidateScore"]))
                if score > best_score:
                    best_score = score
                    best_candidate = c
            if best_score >= min_score:
                all_concepts[term] = best_candidate
        return all_concepts
