## This is an example source import

The purpose of this directory is to show the proper way to import
a new source into iDISK. This process is comprised of two steps:

1. Download the source data using the best available method into `download/`.
2. Convert the data into the iDISK JSON lines format and store it in `import/`.
   * Intermediate files between `download/` and `import/` are kept in `import/preprocess`.

All files are included in this example to show what the output should be. However,
please run through the examples if you are keen.


### 1. Downloading the source data

This example uses a subset of the Natural Health Products Ingredient Database (NHPID).
This data is freely available from the Natural Health Products Canada website: 
https://www.canada.ca/en/health-canada/services/drugs-health-products/natural-non-prescription/applications-submissions/product-licensing/licensed-natural-health-product-database-data-extract.html

You don't need to download the data to run this example, as a subset is already present at `download/NHP_MEDICINAL_INGREDIENTS.txt`.


### 2. Converting the source data into the iDISK format

#### Proprocessing

The purpose of this section is to merely give an example of why intermediate files may be necessary. Your file will probably not have
these issues. Maybe your data won't have issues at all and you'll be able to skip directly to conversion. Unfortunately there is no
standard way to determine if there are any issues with your data. The best method is usually just to iterate and manually check the
output (manually checking it is *very* important) at each step until you can't find anything wrong and it works.

We use the `NHP_MEDICINAL_INGREDIENTS.txt` file as downloaded from the above link. However, there are a few issues
with this file:

* It is not in a standard format. I.e. it is pipe (`|`) delimited and there are no column names.
* Even once converted to a standard format, the file contains ill-formatted lines that will cause downstream issues.
* The file is indexed by the ID of the product to which the given ingredient belongs. We need each ingredient to have its own ID.


To fix the first issue we need to find some column names. These can be found and manually extracted from the README.txt that
comes bundled with the data. We save this to `download/headers/NHP_MEDICINAL_INGREDIENTS.txt`.
We then run the following command.

```
# Convert to CSV and add headers.
# This will save the output as NHP_MEDICINAL_INGREDIENTS.csv
python scripts/flat_to_csv.py --headerfile download/headers/NHP_MEDICINAL_INGREDIENTS.txt \
                              --infile download/NHP_MEDICINAL_INGREDIENTS.txt \
                              --outdir import/preprocess/
```

The second issue involves random newlines inserted throughout the file, which break up the fields.
While this does not cause the CSV reader to fail, it will create some nonsense in the output if we're not careful.
Fixing this issue requires us to know the number of fields to expect. This can be found by `wc -l` on the header file. *Hint: its 23*.

```
python scripts/fix_csv.py --infile import/preprocess/NHP_MEDICINAL_INGREDIENTS.csv \
                          --numfields 23 \
                          > import/preprocess/NHP_MEDICINAL_INGREDIENTS_fixed.csv
```

We address the third issue by assigning a unique ID to each unique string in the `proper_name` field of the CSV file.
The following command does this, assigning the ID to the `ingredient_id` field.

```
python scripts/add_dummy_ids.py --incsv import/preprocess/NHP_MEDICINAL_INGREDIENTS_fixed.csv \
                                --outcsv import/preprocess/NHP_MEDICINAL_INGREDIENTS_fixed_ids.csv
```

We are finally ready to convert this data into the iDISK format!


#### Conversion

Conversion is simple enough: we just have to mash our data into the iDISK API helper classes, defined in the `idlib` package.
We should always take care to address any idiosyncracies in the data at this point, to make our lives easier
later on. For the NHP data, we have to:

* **Merge duplicate concepts**: Because the NHPID data was originally indexed by product, it contains many duplicate ingredients. We merge all lines in the input with the same `ingredient_id`.
* **Remove nonsense ingredients**: NHPID is a bit messy and contains ingredient names such as "8", etc. We have to filter these out.

These are taken care of in the conversion script, so check the source code for details.

Run the following command to do the conversion. Note that you'll need `idlib` installed first (`idlib` is bundled with the iDISK code under `lib/idlib`).

```
python scripts/extract_ingredients.py --incsv import/preprocess/NHP_MEDICINAL_INGREDIENTS_fixed_ids.csv \
                                      --outjsonl import/ingredients.jsonl
```


### Afterthoughts

It is a very good idea to write a similar file to this one for each new source import, to explain how to get
from `download/` to `import/` and why any intermediate step are necessary. As an alternative to Markdown, a Jupyter notebook
could potentially serve this purpose well.
