import os
import csv
import pickle
import shutil
import argparse

from tqdm import tqdm
from collections import defaultdict, namedtuple

import idlib


"""
Extend the UMLS Metathesaurus RRF files with iDISK concepts from the
specified version. The files created are
 MRCONSO.RRF (Concepts and Atoms)
 MRSTY.RRF (Semantic types of Concepts)
 MRSAB.RRF (Data sources)
 MRRANK.RRF (Ranking of data source from most to least preferred)
 SM.DB (Semantic network. Not modified from input UMLS files)

These are all the files required to run the MetaMap Data File Builder.
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--idisk_version_dir", type=str, required=True)
    parser.add_argument("--umls_mth_dir", type=str, required=True)
    parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--use_semtypes", type=str, default=None,
                        help="""File of semantic types to use (long names),
                                one per line.""")
    return parser.parse_args()


def main(args):
    # mrconso: dict of UMLS CUI to rows in original file.
    mrconso_pickle_path = os.path.join(args.umls_mth_dir, "mrconso.pkl")
    if os.path.exists(mrconso_pickle_path):
        print(f"Loading MRCONSO from pickle file '{mrconso_pickle_path}'")
        mrconso = pickle.load(open(mrconso_pickle_path, 'rb'))
    else:
        in_mrconso_path = os.path.join(args.umls_mth_dir, "META/MRCONSO.RRF")
        mrconso = load_rrf(in_mrconso_path)
        print(f"Saving MRCONSO to pickle file '{mrconso_pickle_path}'")
        pickle.dump(mrconso, open(mrconso_pickle_path, 'wb'))

    # mrsty: dict of UMLS CUI to rows in original file.
    mrsty_pickle_path = os.path.join(args.umls_mth_dir, "mrsty.pkl")
    if os.path.exists(mrsty_pickle_path):
        print(f"Loading MRSTY from pickle file '{mrsty_pickle_path}'")
        mrsty = pickle.load(open(mrsty_pickle_path, 'rb'))
    else:
        in_mrsty_path = os.path.join(args.umls_mth_dir, "META/MRSTY.RRF")
        mrsty = load_rrf(in_mrsty_path)
        print(f"Saving MRSTY to pickle file '{mrsty_pickle_path}'")
        pickle.dump(mrsty, open(mrsty_pickle_path, 'wb'))

    keep_semtypes = []
    if args.use_semtypes is not None:
        keep_semtypes = {sty.strip() for sty in open(args.use_semtypes)}
    # SRDEF contains semantic type information.
    srdef_path = os.path.join(args.umls_mth_dir, "NET/SRDEF")
    # srdef: dict Semantic type code (e.g. T101)
    #  to all other semantic type data.
    srdef = load_srdef(srdef_path, keep_semtypes=keep_semtypes)

    # Number of attributes in the existing MRSTY, so we know what the next
    # attribute number should be when adding them.
    atr_count = max([int(row[4].replace("AT", ''))
                     for sublist in mrsty.values() for row in sublist])
    atr_count += 1

    # Load iDISK
    idisk = idlib.load_kb(args.idisk_version_dir)

    # UMLS CUI to list(iDISK concepts)
    umls2idisk = find_umls_links(idisk, mrconso)

    out_mrconso_path = os.path.join(args.outdir, "MRCONSO.RRF")
    out_mrsty_path = os.path.join(args.outdir, "MRSTY.RRF")

    # Number of terms and CUIs belonging to iDISK is needed for MRSAB
    idisk_terms = []
    idisk_cuis = set()
    with open(out_mrconso_path, 'w') as conso_out, open(out_mrsty_path, 'w') as sty_out:  # noqa
        conso_writer = csv.writer(conso_out, delimiter='|')
        sty_writer = csv.writer(sty_out, delimiter='|')

        # For each UMLS concept
        max_cui = 0
        for (cui, rows) in mrconso.items():
            cui_num = int(cui.replace('C', ''))
            if cui_num > max_cui:
                max_cui = cui_num
            # Get its semantic types
            stys = mrsty[cui]
            # Get the iDISK concepts linked to it.
            idisk_concepts = umls2idisk[cui]
            # If there are iDISK concepts linked, it's a DS,
            # so prepend a 'D' to the CUI to indicate that.
            if len(idisk_concepts) > 0:
                cui = 'D' + cui
            # Write the original UMLS atom rows to the new MRCONSO.
            for row in rows:
                row[0] = cui
                conso_writer.writerow(row)
            # Write the original UMLS semantic type rows to MRSTY.
            seen_stys = set()
            for sty in stys:
                sty[0] = cui
                try:
                    srdef[sty[1]]
                except KeyError:
                    # "Skipping semantic type '{sty[3]}' for concept {cui}"
                    continue
                sty_writer.writerow(sty)
                seen_stys.add(sty[1])
            # Write any linked iDISK concepts to MRCONSO and MRSTY.
            for idisk_concept in idisk_concepts:
                idisk_terms.extend([a.ui for a in idisk_concept.get_atoms()])
                idisk_cuis.add(idisk_concept.ui)
                write_idisk2mrconso(conso_writer, idisk_concept, new_cui=cui)
                added = write_idisk2mrsty(
                        sty_writer, idisk_concept, srdef,
                        atr_count, new_cui=cui, seen_stys=seen_stys)
                atr_count += len(added)
                seen_stys.update(added)

        count = 1
        for concept in idisk:
            if concept.concept_type != "SDSI":
                continue
            if concept.ui in idisk_cuis:
                continue
            new_cui = f"DC{max_cui+count:>07}"
            write_idisk2mrconso(conso_writer, idisk_concept, new_cui=new_cui)
            added = write_idisk2mrsty(sty_writer, concept, srdef,
                                      atr_count, new_cui=new_cui)
            atr_count += len(added)
            count += 1

    # MRSAB
    in_mrsab_path = os.path.join(args.umls_mth_dir, "META/MRSAB.RRF")
    out_mrsab_path = os.path.join(args.outdir, "MRSAB.RRF")
    shutil.copy2(in_mrsab_path, out_mrsab_path)
    add_idisk2mrsab(out_mrsab_path, len(idisk_terms), len(idisk_cuis))

    # MRRANK
    in_mrrank_path = os.path.join(args.umls_mth_dir, "META/MRRANK.RRF")
    out_mrrank_path = os.path.join(args.outdir, "MRRANK.RRF")
    shutil.copy2(in_mrrank_path, out_mrrank_path)
    add_idisk2mrrank(out_mrrank_path)

    # SM.DB
    # Just copy it as we make no changes.
    smdb_path = os.path.join(args.umls_mth_dir, "LEX/LEX_DB/SM.DB")
    shutil.copy2(smdb_path, args.outdir)


def load_rrf(filepath):
    rrf = defaultdict(list)
    with open(filepath, 'r') as inF:
        reader = csv.reader(inF, delimiter='|')
        for row in tqdm(reader):
            cui = row[0]
            rrf[cui].append(row)
    return rrf


def load_srdef(filepath, keep_semtypes=None):
    STY = namedtuple("STY", ["code", "treecode", "shortform", "longform"])
    srdef = dict()
    with open(filepath, 'r') as inF:
        reader = csv.reader(inF, delimiter='|')
        for row in reader:
            shortform = row[8]  # orgm
            code = row[1]  # T001
            treecode = row[3]  # A1.1
            longform = row[2]  # Organism
            if keep_semtypes is not None:
                if longform not in keep_semtypes:
                    print(f"Not using semantic type: {longform}")
                    continue
            sty = STY(code=code, treecode=treecode,
                      shortform=shortform, longform=longform)
            srdef[shortform] = sty
            srdef[code] = sty
    return srdef


def find_umls_links(idisk, mrconso):
    umls2idisk = defaultdict(list)
    for concept in idisk:
        if concept.concept_type != "SDSI":
            continue
        for atom in concept.get_atoms():
            if atom.src == "UMLS":
                cui = atom.src_id
                if cui in mrconso.keys():
                    umls2idisk[cui].append(concept)
    return umls2idisk


def write_idisk2mrconso(csvwriter, concept, new_cui):
    for atom in concept.get_atoms():
        if atom.src == "UMLS":
            continue
        # iDISK is UTF-8 but MetaMap requires ASCII
        if atom.term.isascii() is False:
            continue
        aui = atom.ui
        lui = atom.ui.replace("DA", "DL")
        sui = atom.ui.replace("DA", "DS")
        term_status = 'S'
        ispref = 'N'
        row = [new_cui, "ENG", term_status, lui, "PF",
               sui, ispref, aui, '', '', '', "IDISK",
               atom.term_type, concept.ui, atom.term,
               0, 'N', '', '']
        csvwriter.writerow(row)


def write_idisk2mrsty(csvwriter, concept, srdef, atr_count,
                      new_cui=None, seen_stys=set()):
    if new_cui is not None:
        cui = new_cui
    else:
        cui = concept.ui
    stys_added = []
    count = atr_count
    for atr in concept.get_attributes(atr_name="umls_semantic_type"):
        sty_abbrev = atr.atr_value
        try:
            sty_data = srdef[sty_abbrev]
        except KeyError:
            # "Skipping semtype '{sty_abbrev}' for {concept.ui}"
            continue
        if sty_data.code in seen_stys:
            continue
        seen_stys.add(sty_data.code)
        row = [cui, sty_data.code, sty_data.treecode, sty_data.longform,
               f"DAT{count:>07}", "111"]
        csvwriter.writerow(row)
        stys_added.append(sty_data.code)
        count += 1

    # Add Pharmacologic Substance to every dietary supplement
    # so that it is treated as such.
    phsu_data = srdef["phsu"]  # Pharmacologic substance
    if phsu_data.code not in set(stys_added).union(seen_stys):
        row = [cui, phsu_data.code, phsu_data.treecode,
               phsu_data.longform, f"DAT{count:>07}", "111"]
        csvwriter.writerow(row)
        stys_added.append(phsu_data.code)
    return stys_added


def add_idisk2mrrank(mrrank_path):
    """
    iDISK is the lowest ranked source.
    """
    mrrank_rows = []
    with open(mrrank_path, 'r') as inF:
        reader = csv.reader(inF, delimiter='|')
        mrrank_rows = [row for row in reader]

    idisk_rows = []
    for (i, tty) in enumerate(["SY", "CN", "SN"]):
        rank = i + 1
        row = [f"{rank:>04}", "IDISK", tty, 'N']
        idisk_rows.append(row)
    # Reverse so it goes high to low like the other rows.
    idisk_rows = idisk_rows[::-1]

    with open(mrrank_path, 'a') as outF:
        writer = csv.writer(outF, delimiter='|')
        for row in mrrank_rows:
            rank = int(row[0]) + len(idisk_rows)
            row[0] = f"{rank:>04}"
            writer.writerow(row)
        for row in idisk_rows:
            writer.writerow(row)


def add_idisk2mrsab(mrsab_path, num_idisk_terms, num_idisk_cuis):
    with open(mrsab_path, 'a') as outF:
        writer = csv.writer(outF, delimiter='|')
        count = 666
        sab = "IDISK"
        sab_cui = f"DC{count:>07}"
        sab_versioned = "IDISK_v1.0.1"
        longname = "Integrated Dietary Supplements Knowledge Base"
        version = "1.0.1"
        start_date = "2019_01_01"
        end_date = ''
        meta_insert_date = ''
        meta_remove_date = ''
        contact_info = "Rui Zhang (zhan1386@umn.edu)"
        source_restriction_level = 0
        term_freq = num_idisk_terms
        cui_freq = num_idisk_cuis
        context_type = "FULL"
        tty_list = "SN,CN,SY"
        atr_list = ''
        lang = "ENG"
        encoding = 'UTF-8'
        current_version = 'Y'
        source_in_subset = 'Y'
        institute = "University of Minnesota - Twin Cities, Insitute for Health Informatics."  # noqa
        row = [sab_cui, sab_cui, sab_versioned, sab, longname, sab,
               version, start_date, end_date, meta_insert_date,
               meta_remove_date, contact_info, contact_info,
               source_restriction_level, term_freq, cui_freq,
               context_type, tty_list, atr_list, lang, encoding,
               current_version, source_in_subset, institute, '']
        writer.writerow(row)


if __name__ == "__main__":
    args = parse_args()
    main(args)
