import os
import subprocess
import re
import json
import logging


logging.getLogger().setLevel(logging.INFO)


class CandidateLink(object):
    """
    Candidate link from an input string to an external data
    source as discovered by an EntityLinker.

    :param str input_string: The raw string that was linked.
    :param str candidate_term: The preferred term of the linked entity in
                               the data source.
    :param str candidate_source: The data source to which the input string
                                 was linked.
    :param str candidate_id: The unique identifier of the linked entity
                             in the data source.
    :param attrs: Keyword arguments containing other necessary information
                  about this linking. For example, the CandidateScore from
                  the output of MetaMap.
    """
    def __init__(self, input_string, candidate_term,
                 candidate_source, candidate_id, **attrs):
        self.input_string = input_string
        self.candidate_term = candidate_term
        self.candidate_source = candidate_source
        self.candidate_id = candidate_id
        self._attrs = attrs

    def __str__(self):
        map_str = f"{self.input_string} -> {self.candidate_term}"
        src_str = f" ({self.candidate_source} {self.candidate_id})"
        return map_str + src_str

    def __getitem__(self, key):
        """
        Return the value corresponding to key in self._attrs,
        otherwise raise a KeyError.

        :param str key: The name of the attribute to look up.
        :returns: The value corresponding to key.
        :raises: KeyError
        """
        return self._attrs[key]

    @property
    def attrs(self):
        return self._attrs

    @attrs.setter
    def attrs(self):
        msg = "CandidateLink does not support attribute modification."
        raise TypeError(msg)


class EntityLinker(object):
    """
    Abstract class for doing entity linking.

    :param str name: The name of this entity linker.
    """

    def __init__(self, name):
        self.name = name

    def _log(self, msg, level="info"):
        func = getattr(logging, level)
        msg = f"<{self.name}> " + msg
        func(msg)

    def link(self, input_strings, **kwargs):
        """
        Link an input string or sequence of input strings
        to entities in the corresponding database. Outputs a nested
        dictionary of the format

            {input_string: {matched_input: CandidateLink}}.

        :param list input_strings: String or strings to link.
        :returns: Dictionary of input strings to CandidateLink instances.
        :rtype: dict
        """
        raise NotImplementedError()

    def get_best_links(self, candidate_links, **kwargs):
        """
        Given a set of candidate links for a set of input
        strings returned by EntityLinker.link(), choose
        the "best" linking for each input string from among
        the candidate links.

        :param dict candidate_links: Dictionary of input strings
                                     to candidate linkings.
        :returns: candidate_links filtered to include only the "best" links.
        :rtype: list
        """
        raise NotImplementedError()


class MetaMapDriver(EntityLinker):
    """
    Class to start and use a MetaMap instance from within Python.

    :param str mm_bin: path to MetaMap bin/ directory.
    :param str data_year: corresponds to the -V option. E.g. '2018AA'
    :param str data_version: corresponds to the -Z option. E.g. 'Base'
    """

    def __init__(self, mm_bin, data_year="2018AB", data_version="Base"):
        super().__init__("metamap")
        self.mm_bin = mm_bin
        self.metamap = os.path.join(self.mm_bin, "metamap16")
        self.data_year = data_year
        self.data_version = data_version
        self._start()

    def _start(self):
        """
        Start the MetaMap servers.
        """
        self._log("Starting tagger server.")
        tagger_server = os.path.join(self.mm_bin, "skrmedpostctl")
        tagger_out = subprocess.check_output([tagger_server, "start"])
        self._log(tagger_out.decode("utf-8"))
        self._log("You may want to start the WSD server before continuing.")
        self._log(f"  Run {self.mm_bin}/wsdserverctl start")

    def _clean_data(self, data):
        """
        Remove all non-ASCII characters in the content and
        remove content inside of ().

        :param list data: A list of strings to clean.
        :returns: cleaned data.
        :rtype: list
        """
        cleaned = []
        for d in data:
            d = re.sub(r'[^\x00-\x7F]+', " ", d)
            d = re.sub(r" ?\([^)]+\)", "", d)
            cleaned.append(d)
        return cleaned

    def _add_ids(self, data):
        """
        Add IDs to each input string. Required by the metamap
        --sldiID option which is used by default in _get_call().

        :param list data: A list of strings to which to add IDs.
        :returns: data with IDs added.
        :rtype: list
        """
        return [f"{i}|{input}" for (i, input) in enumerate(data)]

    def _get_call(self, data_filename, term_processing=False,
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

        call = f"{self.metamap} {args_str} {data_filename}"
        return call

    def _run_call(self, call):
        """
        Run the MetaMap call.

        :param str call: MetaMap call. Output of self.get_call()
        :returns: The call and the output of the call.
        :rtype: tuple
        """
        process = subprocess.Popen(call, shell=True, stdout=subprocess.PIPE)
        process.wait()
        output = json.loads(open("tmp.txt.out", 'r').read())
        return output

    def _convert_output_to_candidate_links(self, output, keep_semtypes={}):
        """
        Convert the JSON output by MetaMap into a collection of CandidateLink
        instances. Outputs a nested dictionary of
        `{input_text: {phrase_text: CandidateLink}}`.

        :param dict output: JSON formatted output from self.run_call()
        :param list keep_semtypes: dictionary of the form
                                   `{input_term_id: [semtypes, [...]]}`
                                   for each input term. If an ID is missing,
                                   does not filter the concepts for that term.
                                   (default None).
        :returns: dictionary of candidate links, one for each phrase in
                  each line in the input.
        :rtype: dict
        """

        def _convert_to_candidate_link(input_string, candidate):
            pref_term = candidate["CandidatePreferred"]
            return CandidateLink(input_string=input_string,
                                 candidate_term=pref_term,
                                 candidate_source="UMLS",
                                 candidate_id=candidate["CandidateCUI"],
                                 # attrs
                                 linking_score=candidate["CandidateScore"],
                                 umls_semantic_type=candidate["SemTypes"])

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
                    if doc_id in keep_semtypes:
                        # Filter candidates on semantic types
                        types = set(keep_semtypes[doc_id])
                        candidates = [c for c in candidates
                                      if len(types & set(c["SemTypes"])) > 0]
                    if candidates != []:
                        candidates = [_convert_to_candidate_link(phrase_text, c)  # noqa
                                      for c in candidates]
                        doc_mappings[phrase_text] = candidates
            all_mappings[doc_id] = doc_mappings

        return all_mappings

    def link(self, input_strings, term_processing=False,
             call_options=None, keep_semtypes={}):
        """
        Link an input string or list of strings to UMLS concepts.

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
        # Add IDs if they were not added by the user.
        has_ids_match = re.match(r'.+\|.+', clean[0])
        if not has_ids_match:
            msg = "Inputs do not seem to have IDs. Adding them."
            self._log(msg, level="warn")
            clean = self._add_ids(clean)

        # TODO: Figure out best way to specify the input/output filename.
        indata = '\n'.join(clean)
        with open("tmp.txt", 'w') as outF:
            outF.write(indata)
            outF.write('\n')  # MetaMap requires an extra newline at the end.
        call = self._get_call("tmp.txt", term_processing=term_processing,
                              options=call_options)
        output = self._run_call(call)
        links = self._convert_output_to_candidate_links(output,
                                                        keep_semtypes)
        return links

    def get_best_links(self, candidate_links, min_score=800):
        """
        Returns the candidate link with the highest score
        for each input term.
        Warning! If two or more concepts are tied, one will
        be returned at random.

        :param dict mappings: dict of candidate mappings. Output of self.map.
        :param int min_score: minimum candidate mapping score to accept.
        :returns: The best candidate mapping for each input term.
        :rtype: list
        """
        if not isinstance(candidate_links, dict):
            raise ValueError(f"Unsupported type '{type(candidate_links)}.")

        all_concepts = {}
        for (doc_id, phrases) in candidate_links.items():
            #phrase2candidate = {}
            best_candidates = []
            for (phrase_text, candidates) in phrases.items():
                best_score = float("-inf")
                best_candidate = None
                for c in candidates:
                    score = abs(int(c["linking_score"]))
                    if score > best_score and score > min_score:
                        best_score = score
                        best_candidate = c
                if best_candidate is None:
                    msg = f"No best candidate for input '{phrase_text}'."
                    self._log(msg, level="warn")

                best_candidates.append(best_candidate)
                #phrase2candidate[phrase_text] = best_candidate
            #all_concepts[doc_id] = phrase2candidate
            all_concepts[doc_id] = best_candidate
        return all_concepts
