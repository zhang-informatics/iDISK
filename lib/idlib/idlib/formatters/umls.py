import os
import shutil
import warnings
import argparse
import logging
import csv
import pickle
import pandas as pd
from tqdm import tqdm
from collections import defaultdict, namedtuple

import idlib

logging.getLogger().setLevel(logging.INFO)


"""
Create UMLS Metathesaurus formatted files for the specified concepts.
The file created are
  MRCONSO.RRF (Concepts and Atoms)
  MRSTY.RRF (Semantic types of Concepts)
  MRSAB.RRF (Data sources)
  MRRANK.RRF (Ranking of data sources from most to least preferred)
  SM.DB (Empty)
"""


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--idisk_version_dir", type=str, required=True,
                        help="iDISK version to load.")
    parser.add_argument("--outdir", type=str, required=True,
                        help="Where to save the resulting files.")
    parser.add_argument("--umls_mth_dir", type=str, required=True,
                        help="""Directory containing UMLS Metathesaurus files
                                to extend.""")
    parser.add_argument("--mrconso_pickle", type=str, default=None,
                        help="Pickled defaultdict of CUIs to MRCONSO rows.")
    parser.add_argument("--use_semtypes", type=str, default=None,
                        help="File of semantic types to use, one per line.")
    return parser.parse_args()


def main(args):
    os.makedirs(args.outdir, exist_ok=True)

    keep_semtypes = None
    if args.use_semtypes is not None:
        keep_semtypes = {code.strip() for code in open(args.use_semtypes)}

    umls_mrsty_path = os.path.join(args.umls_mth_dir, "META/MRSTY.RRF")
    mrsty_path = os.path.join(args.outdir, "MRSTY.RRF")
    if os.path.exists(mrsty_path):
        raise OSError("MRSTY.RRF already exists at '{mrsty_path}'.")
    # copy UMLS MRSTY to new location, removing unwanted semtypes
    if keep_semtypes is not None:
        print("Filtering semantic types into new MRSTY.RRF")
        with open(umls_mrsty_path, 'r') as inF, open(mrsty_path, 'w') as outF:
            reader = csv.reader(inF, delimiter='|')
            writer = csv.writer(outF, delimiter='|')
            for row in reader:
                if row[3] in keep_semtypes:
                    writer.writerow(row)
    else:
        shutil.copy2(umls_mrsty_path, args.outdir)
    mrsty_handle = open(mrsty_path, 'a')
    mrsty_writer = csv.writer(mrsty_handle, delimiter='|')

    umls_mrconso_path = os.path.join(args.umls_mth_dir, "META/MRCONSO.RRF")
    # shutil.copy2(umls_mrconso_path, args.outdir)
    mrconso_path = os.path.join(args.outdir, "MRCONSO.RRF")
    if os.path.exists(mrconso_path):
        raise OSError("MRCONSO.RRF already exists at '{mrconso_path}'.")
    mrconso_handle = open(mrconso_path, 'a')
    mrconso_writer = csv.writer(mrconso_handle, delimiter='|')

    if args.mrconso_pickle is None:
        print("Loading MRCONSO from file.")
        umls_mrconso = defaultdict(list)
        with open(umls_mrconso_path, 'r') as inF:
            reader = csv.reader(inF, delimiter='|')
            for row in tqdm(reader):
                cui = row[0]
                umls_mrconso[cui].append(row)
        pickle_path = os.path.join(args.outdir, "umls_mrconso.pickle")
        print("  Pickling MRCONSO to {pickle_path}")
        pickle.dump(umls_mrconso, open(pickle_path, 'wb'))
    else:
        print("Loading MRCONSO from pickle file.")
        umls_mrconso = pickle.load(open(args.mrconso_pickle, 'rb'))
    print("Done")

    print("Loading SRDEF")
    srdef_path = os.path.join(args.umls_mth_dir, "NET/SRDEF")
    srdef_df = pd.read_csv(srdef_path, sep='|', header=None)
    sty2data = get_sty_data(srdef_df, keep_semtypes)
    print("Done")
    print("Using the following semantic types")
    for (k, v) in sorted(sty2data.items(), key=lambda x: x[0]):
        print(k, v)

    kb = idlib.load_kb(args.idisk_version_dir)

    print("Extending UMLS Metathesaurus files")
    sty_atr_count = 0  # Keeps track of the number of semantic type attributes.
    source2tty = defaultdict(set)
    cuis_per_sab = defaultdict(set)
    terms_per_sab = defaultdict(set)
    cuis_to_rm = set()
    for concept in tqdm(kb):
        if concept.concept_type != "SDSI":
            continue
        concept._prefix = "DC"
        new_count = write2sty(mrsty_writer, concept, sty2data, sty_atr_count)
        sty_atr_count = new_count

        idisk_atoms = []
        umls_atoms = []
        for atom in concept.get_atoms():
            if atom.src == "UMLS":
                cuis_to_rm.add(atom.src_id)
                # umls_atoms = get_umls_atoms_from_concept(atom.src_id,
                #                                          umls_mrconso)
                umls_atoms = get_umls_atoms_from_concept_raw(
                        atom.src_id, umls_mrconso, new_cui=concept.ui)
                umls_atoms.extend(umls_atoms)
            atom._prefix = "DA"
            #write2conso(mrconso_writer, concept, atom)
            idisk_atoms.append(atom)
            source2tty[atom.src].add(atom.term_type)
            cuis_per_sab[atom.src].add(concept.ui)
            terms_per_sab[atom.src].add(atom.term)
        for atom in idisk_atoms:
            allow_preferred = len(umls_atoms) == 0
            write2conso(mrconso_writer, concept, atom,
                        allow_preferred=allow_preferred)
        for atom in umls_atoms:
            # write2conso(mrconso_writer, concept, atom)
            mrconso_writer.writerow(atom)

    concept_count = int(concept.ui.replace("DC", ''))

    mrsty_handle.close()

    with open(umls_mrconso_path, 'r') as inF:
        umls_mrconso_reader = csv.reader(inF, delimiter='|')
        for row in tqdm(umls_mrconso_reader):
            if row[0] in cuis_to_rm:
                continue
            mrconso_writer.writerow(row)
    mrconso_handle.close()

    # MRSAB
    umls_mrsab_path = os.path.join(args.umls_mth_dir, "META/MRSAB.RRF")
    shutil.copy2(umls_mrsab_path, args.outdir)
    mrsab_path = os.path.join(args.outdir, "MRSAB.RRF")
    add_idisk_to_mrsab(mrsab_path, cuis_per_sab, terms_per_sab, concept_count)

    # MRRANK
    umls_mrrank_path = os.path.join(args.umls_mth_dir, "META/MRRANK.RRF")
    shutil.copy2(umls_mrrank_path, args.outdir)
    mrrank_path = os.path.join(args.outdir, "MRRANK.RRF")
    add_idisk_to_mrrank(mrrank_path, idlib.config.SOURCES,
                        idlib.config.TERM_TYPES)

    # SM.DB: Just copy the metathesaurus one, as iDISK makes no modifications.
    umls_sm_path = os.path.join(args.umls_mth_dir, "LEX/LEX_DB/SM.DB")
    shutil.copy2(umls_sm_path, args.outdir)


def get_umls_atoms_from_concept(cui, mrconso):
    rows = mrconso[cui]
    atoms = []
    for row in rows:
        is_pref = True if row[2] == 'P' else False
        atom = idlib.data_elements.Atom(
                term=row[14], src="UMLS", src_id=row[7],
                term_type="SY", is_preferred=is_pref)
        atoms.append(atom)
    return atoms


def get_umls_atoms_from_concept_raw(cui, mrconso, new_cui=None):
    """
    As opposed to the above, which uses the idlib API
    and thus loses information, this function returns atoms
    as a list of fields corresponding to their rows in MRCONSO.
    """
    rows = mrconso[cui][:]
    if new_cui is not None:
        for row in tqdm(rows):
            row[0] = new_cui
    return rows


def get_sty_data(srdef_df, keep_semtypes=None):
    STY = namedtuple("STY", ["code", "treecode", "longform"])
    sty2data = {}
    for (i, row) in srdef_df.drop_duplicates(1).iterrows():
        abbrev = row[8]  # orgm
        code = row[1]  # T001
        treecode = row[3]  # A1.1
        longform = row[2]  # Organism
        if keep_semtypes is not None:
            if longform not in keep_semtypes:
                continue
        sty = STY(code=code, treecode=treecode, longform=longform)
        sty2data[abbrev] = sty
    return sty2data


def get_sty_abbreviations(st_mapping_file):
    mapping = pd.read_csv(st_mapping_file, sep='|', header=None)
    return dict(zip(mapping[1], mapping[0]))


def write2sty(csvwriter, concept, sty2data, count):
    seen_stys = set()
    for atr in concept.get_attributes(atr_name="umls_semantic_type"):
        sty = atr.atr_value
        count += 1
        seen_stys.add(sty)
        try:
            sty_data = sty2data[sty]
        except KeyError:  # Not in keep_semtypes
            warnings.warn(f"Skipping semtype '{sty}' for {concept.ui}")
            continue
        row = [concept.ui, sty_data.code, sty_data.treecode,
               sty_data.longform, f"DAT{count:>07}", "111"]
        csvwriter.writerow(row)

    # If this is an ingredient, we want it to at least be a
    # Pharmacologic Substance so that SemRep treats it as a
    # possible substance interactions entity.
    if concept.concept_type == "SDSI":
        if "phsu" not in seen_stys:
            count += 1
            sty_data = sty2data["phsu"]
            row = [concept.ui, sty_data.code, sty_data.treecode,
                   sty_data.longform, f"DAT{count:>07}", "111"]
            csvwriter.writerow(row)
    return count


def write2conso(csvwriter, concept, atom, allow_preferred=True):
    aui = atom.ui
    lui = atom.ui.replace("DA", "DL")
    sui = atom.ui.replace("DA", "DS")
    if allow_preferred is True:
        term_status = 'P' if atom.is_preferred is True else 'S'
        pref_atom = concept.preferred_atom
        ispref = 'Y' if atom.ui == pref_atom.ui else 'N'
    else:
        term_status = 'S'
        ispref = 'N'
    # MetaMap is ASCII only.
    if atom.term.isascii() is False:
        return
    row = [concept.ui, "ENG", term_status, lui, "PF",
           sui, ispref, aui, '', '', '', atom.src,
           atom.term_type, atom.src_id, atom.term,
           0, 'N', 111, '']
    csvwriter.writerow(row)


def add_idisk_to_mrrank(mrrank_path, sources, term_types):
    """iDISK sources are the highest ranked."""
    ranked = []  # iDISK sources ranked from lowest to highest.
    for src in sources:
        for tty in term_types:
            ranked.append((src, tty))
    ranked = list(reversed(ranked))

    start_rank = pd.read_csv(mrrank_path, sep='|', header=None)[0].max()
    with open(mrrank_path, 'a') as outF:
        writer = csv.writer(outF, delimiter='|')
        for (i, (src, tty)) in enumerate(ranked):
            rank = i + 1 + start_rank
            rank_str = f"{rank:>04}"
            writer.writerow([rank_str, src, tty, 'N'])


def add_idisk_to_mrsab(mrsab_path, cuis_per_sab, terms_per_sab, concept_count):
    longname_map = {"UMLS": "Unified Medical Language System",
                    "MEDDRA": "Medical Dictionary of Regulatory Activities",
                    "NMCD": "Natural Medicines Comprehensive Database",
                    "MSKCC": "Memorial Sloan Kettering Cancer Center",
                    "DSLD": "Dietary Supplement Label Database",
                    "NHPID": "Natural Health Products Ingredient Database",
                    }
    count = concept_count
    with open(mrsab_path, 'a') as outF:
        writer = csv.writer(outF, delimiter='|')
        for sab in cuis_per_sab.keys():
            count += 1
            sab_cui = f"DC{count:>07}"
            sab_versioned = sab + "-1"
            longname = longname_map[sab]
            version = 1
            start_date = "2018_01_01"
            end_date = ''
            meta_insert_date = ''
            meta_remove_date = ''
            contact_info = ''
            source_restriction_level = 0
            term_freq = len(terms_per_sab[sab])
            cui_freq = len(cuis_per_sab[sab])
            context_type = "FULL"
            tty_list = "SN,CN,SY"
            atr_list = ''
            lang = "ENG"
            encoding = ''
            curver = 'Y'
            source_in_subset = 'Y'
            row = [sab_cui, sab_cui, sab_versioned, sab, longname, sab,
                   version, start_date, end_date, meta_insert_date,
                   meta_remove_date, contact_info, contact_info,
                   source_restriction_level, term_freq, cui_freq,
                   context_type, tty_list, atr_list, lang, encoding,
                   curver, source_in_subset]
            writer.writerow(row)


if __name__ == "__main__":
    args = parse_args()
    main(args)
