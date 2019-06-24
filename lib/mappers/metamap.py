import os
import subprocess
import re
import json
import warnings


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

        :param list data: A list of strings to clean.
        """
        cleaned = []
        for d in data:
            d = re.sub(r'[^\x00-\x7F]+', " ", d)
            d = re.sub(r" ?\([^)]+\)", "", d)
            cleaned.append(d)
        return cleaned

    def _get_call(self, inputs, term_processing=False,
                  options=None, relaxed=True):
        """
        Build the command line call to MetaMap.

        :param str inputs: newline delimited string of terms to map.
        :param bool term_processing: Whether to use the --term_processing
                                     option and the recommend options to
                                     accompany it. (default False).
        :param str options: any additional arguments to pass to MetaMap
                            (default None).
        :param bool relaxed: If True, use the --relaxed_model (default True).
        :returns: MetaMap call
        :rtype: str
        """
        term_processing_options = [
                "--term_processing",  # Process term by term
                "--ignore_word_order"]
        if term_processing is True:
            has_ids_match = re.match(r'.+\|.+', inputs.split('\n')[0])
            if has_ids_match is None:
                msg = "input does not seem to contain IDs. \
                       Should be of the form 'ID|STRING'."
                warnings.warn(msg)
        args = [f"-Z {self.data_year}",
                f"-V {self.data_version}",
                "--silent",  # Don't show logging/version info
                "--sldiID",  # Single line delimited input with IDs
                "--JSONn"]  # Output unformatted JSON
        if term_processing is True:
            args.extend(term_processing_options)
        if relaxed is True:
            args.append("--relaxed_model")
        if options is not None:
            args.append(options)
        args_str = ' '.join(args)

        call = f"echo '{inputs}' | {self.metamap} {args_str}"
        return call

    # TODO: Add support for unstructured text input.
    def _run_call(self, call):
        """
        Run the MetaMap call.

        :param str call: MetaMap call. Output of self.get_call()
        :returns: The call and the output of the call.
        :rtype: tuple
        """
        res = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
        output = res.stdout.read().decode("utf-8")
        output = json.loads(output.split('\n', maxsplit=1)[1])
        return output

    def _process_output(self, output, keep_semtypes={}):
        """
        Format the JSON output by MetaMap into something a bit
        more accessible. Outputs a nested dictionary of
        `{input_text: {phrase_text: candidate_mapping}}`.

        :param dict output: JSON formatted output from self.run_call()
        :param list keep_semtypes: dictionary of the form
                                   `{input_term_id: [semtypes, [...]]}`
                                   for each input term. If an ID is missing,
                                   does not filter the concepts for that term.
                                   (default None).
        :returns: dictionary of candidate mappings, one for each phrase in
                  each line in the input.
        :rtype: dict
        """
        all_mappings = {}
        docs = output["AllDocuments"]
        for doc in docs:
            doc_id = None
            doc_mappings = {}  # {phrase: mappings}

            # We want to collapse the utterances in this document
            # into a collection of phrases.
            for utt in doc["Document"]["Utterances"]:
                if doc_id is None:
                    doc_id = utt["PMID"]
                for phrase in utt["Phrases"]:
                    phrase_text = phrase["PhraseText"]
                    candidates = [c for m in phrase["Mappings"]
                                  for c in m["MappingCandidates"]]
                    # Filter candidates on semantic types
                    if doc_id in keep_semtypes:
                        types = set(keep_semtypes[doc_id])
                        candidates = [c for c in candidates
                                      if len(types & set(c["SemTypes"])) > 0]
                    if candidates != []:
                        doc_mappings[phrase_text] = candidates
            all_mappings[doc_id] = doc_mappings

        return all_mappings

    def map(self, input_strings, term_processing=False,
            call_options=None, keep_semtypes={}):
        """
        Map an input string or list of strings to UMLS concepts.

        :param list input_strings: list of strings to input to MetaMap
        :param bool term_processing: process a list of terms rather than a
                                     list of texts. (default False).
        :param str call_options: other command line options to pass to metamap.
                                 (default None)
        :param list keep_semtypes: list of strings of semantic types to keep.
                                   (default None)
        :returns: mapping from input to UMLS concepts
        :rtype: dict
        """
        if not isinstance(keep_semtypes, dict):
            raise ValueError("keep_semtypes must be a dict")
        if isinstance(input_strings, str):
            input_strings = [input_strings]

        clean = self._clean_data(input_strings)
        indata = '\n'.join(clean)
        call = self._get_call(indata, term_processing=term_processing,
                              options=call_options)
        output = self._run_call(call)
        mappings = self._process_output(output, keep_semtypes)
        return mappings

    def get_best_mappings(self, mappings, min_score=800):
        """
        Returns the candidate mapping with the highest score
        for each input term.
        Warning! If two or more concepts are tied, one will
        be returned at random.

        :param dict mappings: dict of candidate mappings. Output of self.map.
        :param int min_score: minimum candidate mapping score to accept.
        :returns: The best candidate mapping for each input term.
        :rtype: dict
        """
        if not isinstance(mappings, dict):
            raise ValueError(f"Unsupported input type '{type(mappings)}.")

        all_concepts = {}
        for (doc_id, phrases) in mappings.items():
            phrase2candidate = {}
            for (phrase_text, candidates) in phrases.items():
                best_score = float("-inf")
                best_candidate = None
                for c in candidates:
                    score = abs(int(c["CandidateScore"]))
                    if score > best_score and score > min_score:
                        best_score = score
                        best_candidate = c
                if best_candidate is None:
                    warnings.warn(
                            f"No best candidate for input '{phrase_text}'.")
                phrase2candidate[phrase_text] = best_candidate
            all_concepts[doc_id] = phrase2candidate
        return all_concepts
