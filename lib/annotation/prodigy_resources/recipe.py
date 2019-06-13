import prodigy
from prodigy.components.loaders import JSONL

"""
Prodigy recipe for annotating pairs of iDISK concepts.
"""


@prodigy.recipe("compare",
                dataset=prodigy.recipe_args['dataset'],
                input_file=("File containing input data.",
                            "positional", None, str),
                html_file=("File containing HTML template",
                           "positional", None, str))
def compare(dataset, input_file, html_file):
    """

    """
    stream = JSONL(input_file)
    html_template = open(html_file, 'r').read()
    stream = add_to_stream(stream, html_template)

    return {
            "dataset": dataset,
            "stream": stream,
            "view_id": "choice",
            "config": {"html_template": html_template}
            }


def set_hashes(task, i):
    """
    For some reason Prodigy was assigning the same hashes
    to every example in the data, which meant that when
    it looked at the saved annotations in the dataset to
    figure out which to exclude, it excluded all of them.

    Setting the _input_hash to the index of the candidate
    connection also makes lookup easier when we filter the
    candidates according to their annotation.
    """
    task["_input_hash"] = i
    task["_task_hash"] = -(i+1)
    return task


def add_to_stream(stream, html):
    for (i, task) in enumerate(stream):
        task["html"] = html
        task = set_hashes(task, i)
        task["options"] = [{"id": 1, "text": "Equal"},
                           {"id": 2, "text": "Not Equal"},
                           {"id": 3, "text": "Parent-Child"},
                           {"id": 4, "text": "Child-Parent"}]
        yield task
