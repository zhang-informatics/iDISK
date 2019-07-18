import os
import subprocess
import re
import json
import logging
import urllib
import urllib.parse
import urllib.request

from datetime import datetime
from collections import defaultdict
from quickumls import QuickUMLS


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

    def _get_query_directory_name(self):
        """
        Queries to the entity linker and their results are
        stored in a timestamped directory for debugging
        purposes.
        """
        datetime_str = datetime.now().strftime("%Y_%m_%d_%H:%M:%S")
        dirname = f".query_{self.name}_{datetime_str}"
        return dirname

    def _add_ids(self, queries):
        """
        Add IDs to each query.

        :param list data: A list of strings to which to add IDs.
        :returns: data with IDs added.
        :rtype: list
        """

    def _prepare_queries(self, queries, ascii_only=True):
        """
        Get the queries into the expected format.
        Ensures the input is a list of (ID, text) tuples
        Removes non-ASCII characters and text in parentheses.

        :param list queries: queries to process.
        :returns: (ID, query) pair(s).
        :rtype: list
        """
        if isinstance(queries, str):
            queries = [queries]
        # Add IDs if they were not added by the user.
        if not isinstance(queries[0], (tuple, list)):
            msg = "Queries do not seem to have IDs. Adding them."
            self._log(msg, level="warning")
            queries = [(str(i), query) for (i, query) in enumerate(queries)]

        cleaned = []
        for (i, q) in queries:
            if ascii_only is True:
                q = re.sub(r'[^\x00-\x7F]+', " ", q)
            q = re.sub(r" ?\([^)]+\)", "", q)
            cleaned.append((i, q))
        return cleaned

    def link(self, queries, **kwargs):
        """
        Link query or list of queries to entities in the
        corresponding database. Input should be a
        sequence of (ID, text pairs). Outputs a nested
        dictionary of the format

            {input_string: {matched_input: CandidateLink}}.

        :param list input_strings: List of (ID, string) pairs to link.
        :returns: Dictionary of input strings to CandidateLink instances.
        :rtype: dict
        """
        queries = self._prepare_queries(queries)
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
    :param int min_score: minimum score of a candidate mapping to keep.
    """

    def __init__(self, name="metamap", mm_bin="", data_year="2018AB",
                 data_version="Base", min_score=800, keep_semtypes=None):
        super().__init__(name)
        self.mm_bin = mm_bin
        self.metamap = os.path.join(self.mm_bin, "metamap16")
        self.data_year = data_year
        self.data_version = data_version
        self.min_score = min_score
        self.keep_semtypes = keep_semtypes or []
        self._log_parameters()
        self._start()

    def _log_parameters(self):
        self._log(f"Staring annotator '{self.name}'")
        self._log(f"{self.name} parameters:")
        self._log(f"  mm_bin : {self.mm_bin}")
        self._log(f"  metamap_cmd : {self.metamap}")
        self._log(f"  data_year : {self.data_year}")
        self._log(f"  data_version : {self.data_version}")
        self._log(f"  min_score : {self.min_score}")
        self._log(f"  keep_semtypes: {self.keep_semtypes}")

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

    def _get_call(self, indata, term_processing=False,
                  options=None, relaxed=True):
        """
        Build the command line call to MetaMap.

        :param list indata: list of strings to map.
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

        log_dir = self._get_query_directory_name()
        os.makedirs(log_dir)
        self._log(f"Logging query to {log_dir}")
        infile = os.path.join(log_dir, "query.in")
        outfile = os.path.join(log_dir, "query.out")

        # Write the query to a file for logging and for MetaMap to read.
        # MetaMap requires an extra newline at the end.
        indata = '\n'.join(indata) + '\n'
        with open(infile, 'w') as outF:
            outF.write(indata)

        call = f"{self.metamap} {args_str} {infile} {outfile}"
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
        outfile = call.split()[-1]
        output = json.loads(open(outfile, 'r').read())
        return output

    def _convert_output_to_candidate_links(self, output, keep_semtypes={}):
        """
        Convert the JSON output by MetaMap into a collection of CandidateLink
        instances. Outputs a nested dictionary of

        `{input_id: {phrase_text: [CandidateLink, [...]]}}`.

        :param dict output: JSON formatted output from self.run_call()
        :param list keep_semtypes: If list, a list of semtypes to keep.
                                   If dict, dictionary of the form
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
                                 linked_string=input_string,
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

                    # Filter candidates on semantic types
                    if keep_semtypes:
                        if isinstance(keep_semtypes, dict) \
                           and doc_id in keep_semtypes:
                            types = set(keep_semtypes[doc_id])
                        elif isinstance(keep_semtypes, list):
                            types = set(keep_semtypes)
                        if types is not None:
                            candidates = [c for c in candidates
                                          if len(types & set(c["SemTypes"])) > 0]  # noqa

                    if candidates != []:
                        candidates = [_convert_to_candidate_link(phrase_text, c)  # noqa
                                      for c in candidates]
                        doc_mappings[phrase_text] = candidates

            all_mappings[doc_id] = doc_mappings

        return all_mappings

    def link(self, queries, term_processing=False,
             call_options=None, keep_semtypes=None):
        """
        Link a query or list of queries to UMLS concepts. Outputs a nested
        dictionary of the format

        `{input_id: {phrase_text: [CandidateLink, [...]]}}`.

        :param list queries: list of queries to send to MetaMap
        :param bool term_processing: process a list of terms rather than a
                                     list of texts. (default False).
        :param str call_options: other command line options to pass to metamap.
                                 (default None)
        :param dict keep_semtypes: If list, list of semantic types to include.
                                   If dict, maps input IDs to list of semantic
                                   types to keep. (default None)
        :returns: mapping from input to UMLS concepts
        :rtype: dict
        """
        if keep_semtypes is None:
            keep_semtypes = self.keep_semtypes
        if not isinstance(keep_semtypes, (list, dict)):
            raise ValueError("keep_semtypes must be a list or a dict")

        queries = self._prepare_queries(queries)
        formatted_for_metamap = [f"{i}|{query}" for (i, query) in queries]
        call = self._get_call(formatted_for_metamap,
                              term_processing=term_processing,
                              options=call_options)
        output = self._run_call(call)
        links = self._convert_output_to_candidate_links(output,
                                                        keep_semtypes)
        return links

    def get_best_links(self, candidate_links, min_score=0):
        """
        Returns the candidate link with the highest score
        for each input term. The output format is

        `{input_id: {phrase_text: CandidateLink}}`.

        Warning! If two or more concepts are tied, one will
        be returned at random.

        :param dict mappings: dict of candidate mappings. Output of self.map.
        :param int min_score: (Optional) minimum candidate mapping score to
                              accept. If not specified, defaults to
                              self.min_score.
        :returns: The best candidate mapping for each input term.
        :rtype: dict
        """
        if not isinstance(candidate_links, dict):
            raise ValueError(f"Unsupported type '{type(candidate_links)}.")

        all_concepts = {}
        for (doc_id, phrases) in candidate_links.items():
            phrase2candidate = {}
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
                    self._log(msg, level="warning")

                phrase2candidate[phrase_text] = best_candidate
            all_concepts[doc_id] = phrase2candidate
        return all_concepts


class QuickUMLSDriver(EntityLinker):

    def __init__(self, name="quickumls", quickumls_install="",
                 min_score=0.7, keep_semtypes=None):
        """
        Interface to QuickUMLS.

        :param str quickumls_install: The path to the QuickUMLS installation.
        :param float min_score: Minimum score to consider, between 0 and 1.0.
        :param list keep_semtypes: List of semantic types to consider.
        """
        super().__init__(name)
        self.quickumls_install = quickumls_install
        self.min_score = min_score
        self.keep_semtypes = keep_semtypes
        self._log_parameters()
        self._start()

    def _log_parameters(self):
        self._log(f"Staring annotator '{self.name}'")
        self._log(f"{self.name} parameters:")
        self._log(f"  quickumls_install : {self.quickumls_install}")
        self._log(f"  min_score : {self.min_score}")
        self._log(f"  keep_semtypes : {self.keep_semtypes}")

    def _start(self):
        """
        Instantiate the QuickUMLS matcher.
        """
        self._linker = QuickUMLS(self.quickumls_install,
                                 threshold=self.min_score,
                                 accepted_semtypes=self.keep_semtypes)
        self._log("Started")

    def _convert_output_to_candidate_links(self, outputs):
        """
        Convert the raw QuickUMLS output into CandidateLink
        instances. Output is of the format:

        {matched_string: [CandidateLink, [...]]}

        :param list outputs: List of outputs from QuickUMLS.match().
    def __init__(self, input_string, candidate_term,
                 candidate_source, candidate_id, **attrs):
        """
        links = defaultdict(list)
        for phrase in outputs:
            for match in phrase:
                candidate = CandidateLink(input_string=match["ngram"],
                                          candidate_term=match["term"],
                                          candidate_source="UMLS",
                                          candidate_id=match["cui"],
                                          # attrs
                                          linked_string=match["ngram"],
                                          linking_score=match["similarity"],
                                          umls_semantic_type=match["semtypes"])
                links[match["ngram"]].append(candidate)
        return links

    def link(self, queries):
        """
        Link query or list of queries to entities in the
        corresponding database. Input should be a
        sequence of (ID, text pairs). Outputs a nested
        dictionary of the format

            {input_id: {matched_input: [CandidateLink, [...]]}}.

        :param list input_strings: List of (ID, string) pairs to link.
        :returns: Dictionary of input strings to CandidateLink instances.
        :rtype: dict
        """
        queries = self._prepare_queries(queries, ascii_only=False)
        all_links = {}
        for (qid, query) in queries:
            output = self._linker.match(query)
            links = self._convert_output_to_candidate_links(output)
            all_links[qid] = links
        return all_links

    def get_best_links(self, candidate_links):
        """
        Given a set of candidate links for a set of input
        strings returned by EntityLinker.link(), choose
        the "best" linking for each input string from among
        the candidate links.

            {input_id: {matched_input: CandidateLink}}

        :param dict candidate_links: Dictionary of input strings
                                     to candidate linkings.
        :returns: candidate_links filtered to include only the "best" links.
        :rtype: list
        """
        best_links = {}
        for qid in candidate_links.keys():
            phrase2candidate = {}
            for (matched_str, candidates) in candidate_links[qid].items():
                best = sorted(candidates,
                              key=lambda c: c["linking_score"],
                              reverse=True)[0]
                phrase2candidate[matched_str] = best
            best_links[qid] = phrase2candidate
        return best_links


class BioPortalDriver(EntityLinker):
    """
    Interfaces with the Bioportal API for performing entity linking.
    Uses the BioPortal annotator API interface.

    :param str name: The name of this entity linker.
    """

    def __init__(self, name="bioportal", rest_url="", query_url="",
                 query_options="", api_key=""):
        super().__init__(name)
        self.rest_url = rest_url
        self.query_url = query_url
        self.query_options = query_options
        self.api_key = api_key
        self._log_parameters()

    def _log_parameters(self):
        self._log(f"Staring annotator '{self.name}'")
        self._log(f"{self.name} parameters:")
        self._log(f"  rest_url : {self.rest_url}")
        self._log(f"  query_url : {self.query_url}")
        self._log(f"  query_options : {self.query_options}")
        self._log(f"  api_key : {self.api_key}")

    def _query_bioportal_api(self, url):
        opener = urllib.request.build_opener()
        if self.api_key != "":
            opener.addheaders = [("Authorization",
                                  f"apikey token={self.api_key}")]
        annotations = json.loads(opener.open(url).read())
        return annotations

    def _get_linked_entities(self, annotations):
        links = defaultdict(list)
        for annotation in annotations:
            try:
                class_details = self._query_bioportal_api(
                        annotation["annotatedClass"]["links"]["self"])
            except urllib.error.HTTPError:
                ann_id = class_details['annotatedClass']['@id']
                msg = f"Error retrieving label for {ann_id}"
                self._log(msg, level="warning")

            matched_str = annotation["annotations"][0]["text"]
            ann_id = class_details["@id"].split('/')[-1]
            term = class_details["prefLabel"]
            candidate = CandidateLink(input_string=matched_str,
                                      candidate_term=term,
                                      candidate_source="MEDDRA",
                                      candidate_id=ann_id)
            links[matched_str].append(candidate)
        return links

    def link(self, queries, get_class=True):
        """
        Link a query or list of queries to entities in
        the corresponding database. Outputs a nested
        dictionary of the format

            {input_id: {matched_input: [CandidateLink, [...]]}}.

        :param list input_strings: String or strings to link.
        :returns: Dictionary of input strings to CandidateLink instances.
        :rtype: dict
        """
        all_links = {}
        raw_queries = queries
        queries = self._prepare_queries(raw_queries)
        for (qid, query_str) in queries:
            query = self.query_url + urllib.parse.quote(query_str)
            request = self.rest_url + query + self.query_options
            annotations = self._query_bioportal_api(request)
            if get_class is False:
                return annotations
            links = self._get_linked_entities(annotations)
            all_links[qid] = links

        return all_links

    def get_best_links(self, candidate_links):
        """
        Given a set of candidate links for a set of input
        strings returned by EntityLinker.link(), choose
        the "best" linking for each input string from among
        the candidate links.

            {input_id: {matched_input: CandidateLink}}.

        :param dict candidate_links: Dictionary of input strings
                                     to candidate linkings.
        :returns: candidate_links filtered to include only the "best" links.
        :rtype: list
        """
        msg = "get_best_links() just gets the first candidate."
        self._log(msg, level="warning")
        best_links = {}
        for qid in candidate_links.keys():
            phrase2candidate = {}
            for (matched_str, candidates) in candidate_links[qid].items():
                if not candidates:
                    best = None
                else:
                    best = candidates[0]
                phrase2candidate[matched_str] = best
            best_links[qid] = phrase2candidate
        return best_links


class MedDRARuleBased(EntityLinker):
    """
    A simple rule-based annotator for MedDRA system organ classes (SOCs).
    """
    def __init__(self, name="meddra_soc"):
        super().__init__(name)

    def _start(self):
        self._log(f"Starting {self.name}")

    def _soc_lookup(self, term):
        soc_table = {
                "cardiovascular": [("cardio", "Cardiac disorders", "10007541"),
                                   ("vascular", "Vascular disorders", "10047065")],  # noqa
                "dental": [("", "Dental and gingival conditions", "10044018")],
                "dermatologic": [("", "Skin and subcutaneous tissue disorders", "10040785")],  # noqa
                "endocrine": [("", "Endocrine disorders", "10014698")],
                "gastrointestinal": [("", "Gastrointestinal disorders", "10017947")],  # noqa
                "genitourinary": [("genito", "Reproductive system and breast disorders", "10038604"),  # noqa
                                  ("urinary", "Renal and urinary disorders", "10038359")],  # noqa
                "hematologic": [("", "Blood and lymphatic system disorders", "10005329")],  # noqa
                "hepatic": [("", "Hepatobiliary disorders", "10019805")],
                "immunologic": [("", "Immune system disorders", "10021428")],
                "musculoskeletal": [("", "Musculoskeletal and connective tissue disorders", "10028395")],  # noqa
                "neurologic/cns": [("", "Nervous system disorders", "10029205")],  # noqa
                "ocular/otic": [("", "Eye disorders", "10015919")],
                "oncologic": [("", "Neoplasms benign, malignant and unspecified (incl cysts and polyps)", "10029104")],  # noqa
                "psychiatric": [("", "Psychiatric disorders", "10037175")],
                "pulmonary/respiratory": [("", "Respiratory, thoracic and mediastinal disorders", "10038738")],  # noqa
                "renal": [("", "Renal and urinary disorders", "10038359")],
                     }
        candidates = []
        socs = soc_table.get(term.lower())
        for soc in socs:
            matched_str = soc[0]
            if soc[0] == "":
                matched_str = term.lower()
            candidate = CandidateLink(input_string=matched_str,
                                      candidate_term=soc[1],
                                      candidate_id=soc[2],
                                      candidate_source="MEDDRA")
            candidates.append(candidate)
        return candidates

    def link(self, queries):
        """
        """
        all_candidates = {}
        queries = self._prepare_queries(queries, ascii_only=False)
        for (qid, query) in queries:
            matches = defaultdict(list)
            candidates = self._soc_lookup(query)
            for candidate in candidates:
                matches[candidate.input_string].append(candidate)
            all_candidates[qid] = matches
        return all_candidates

    def get_best_links(self, candidate_links):
        """
        """
        best_links = {}
        for qid in candidate_links:
            phrase2candidate = {}
            for (matched_str, candidates) in candidate_links[qid].items():
                phrase2candidate[matched_str] = candidates[0]
            best_links[qid] = phrase2candidate
        return best_links
