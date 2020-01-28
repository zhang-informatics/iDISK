import os
import argparse
import logging
import csv

# from idlib.data_elements import Concept
import idlib

logging.getLogger().setLevel(logging.INFO)

"""
Create UMLS Metathesaurus style RRF files for the specified concepts.
The files created are
  MRCONSO.RRF (Concepts and Atoms)
  MRSTY.RRF (Concept types)
  MRSAT.RRF (Concept and Relationship Attributes)
  MRREL.RRF (Relationships)
"""


def parse_args():
    parser = argparse.ArgumentParser()
    # parser.add_argument("--concepts_file", type=str, required=True,
    #                    help="JSON lines file containing concepts.")
    parser.add_argument("--idisk_version_dir", type=str, required=True,
                        help="iDISK version to load")
    parser.add_argument("--outdir", type=str, required=True,
                        help="Where to write the RRF files.")
    args = parser.parse_args()
    return args


def create_metathesaurus_files(concepts, output_dir):
    dssty_file = os.path.join(output_dir, "MRSTY.RRF")
    dssty_header = "CUI|STY\n"
    dssty_fp = open(dssty_file, 'w')
    dssty_fp.write(dssty_header)
    dssty_writer = csv.writer(dssty_fp, delimiter='|')

    dsconso_file = os.path.join(output_dir, "MRCONSO.RRF")
    dsconso_header = "CUI|AUI|STR|TTY|SAB|SCODE|ISPREF\n"
    dsconso_fp = open(dsconso_file, 'w')
    dsconso_fp.write(dsconso_header)
    dsconso_writer = csv.writer(dsconso_fp, delimiter='|')

    dssat_file = os.path.join(output_dir, "MRSAT.RRF")
    dssat_header = "ATUI|UI|STYPE|ATN|ATV|SAB\n"
    dssat_fp = open(dssat_file, 'w')
    dssat_fp.write(dssat_header)
    dssat_writer = csv.writer(dssat_fp, delimiter='|')

    dsrel_file = os.path.join(output_dir, "MRREL.RRF")
    dsrel_header = "RUI|CUI1|REL|CUI2|SAB\n"
    dsrel_fp = open(dsrel_file, 'w')
    dsrel_fp.write(dsrel_header)
    dsrel_writer = csv.writer(dsrel_fp, delimiter='|')

    for concept in concepts:
        concept._prefix = "DC"
        # MRSTY
        dssty_writer.writerow([concept.ui, concept.concept_type])

        # MRCONSO
        for atom in concept.get_atoms():
            atom._prefix = "DA"
            pref_code = 'Y' if atom.is_preferred is True else 'N'
            dsconso_line = [concept.ui, atom.ui, atom.term, atom.term_type,
                            atom.src, atom.src_id, pref_code]
            dsconso_writer.writerow(dsconso_line)

        # MRSAT Concepts
        for atr in concept.get_attributes():
            atr._prefix = "DAT"
            stype = "DSCUI"
            dssat_line = [atr.ui, atr.subject.ui, stype,
                          atr.atr_name, atr.atr_value, atr.src]
            dssat_writer.writerow(dssat_line)

        # MRREL
        for rel in concept.get_relationships():
            rel._prefix = "DR"
            try:
                rel.object._prefix = "DC"
            except AttributeError:
                continue
            dsrel_line = [rel.ui, rel.subject.ui, rel.rel_name,
                          rel.object.ui, rel.src]
            dsrel_writer.writerow(dsrel_line)

            # MRSAT Relationships
            for relatr in rel.get_attributes():
                relatr._prefix = "DAT"
                stype = "DSRUI"
                dssat_line = [relatr.ui, relatr.subject.ui, stype,
                              relatr.atr_name, relatr.atr_value, relatr.src]
                dssat_writer.writerow(dssat_line)

    dssty_fp.close()
    dsconso_fp.close()
    dssat_fp.close()
    dsrel_fp.close()


if __name__ == "__main__":
    args = parse_args()
    concepts = idlib.load_kb(args.idisk_version_dir)
    # concepts = Concept.read_jsonl_file(args.concepts_file)
    logging.info(f"<rrf> Populating Metathesaurus files.")
    create_metathesaurus_files(concepts, args.outdir)
    logging.info("<rrf> Complete")
