# Local data

This directory is intentionally kept in Git without bundling any datasets.

Place your local input files here when you want to reuse the example commands from the README.

Common filenames used by the docs:

- sample_sentences.json
- fiona_wrong_results_Training.sgml

All other files in this directory are ignored by Git.

## SGML annotation convention

Local `.sgml` correction datasets should follow the SIGHAN-style Chinese
spelling correction layout:

```xml
<ESSAY title="...">
<TEXT>
<PASSAGE id="case-1">含有錯字的句子</PASSAGE>
</TEXT>
<MISTAKE id="case-1" location="3">
<WRONG>錯字</WRONG>
<CORRECTION>正字</CORRECTION>
</MISTAKE>
</ESSAY>
```

- `ESSAY` may contain one or more `PASSAGE` elements under `TEXT`.
- `PASSAGE id` is the stable case id for that sentence or passage.
- `MISTAKE id` must reference an existing `PASSAGE id` in the same `ESSAY`.
- `location` is a 1-based character position of an erroneous character in the
  referenced `PASSAGE`. It is not necessarily the starting position of `WRONG`.
- `WRONG` is the text span in the passage that contains the erroneous character
  at `location`.
- `CORRECTION` is the corrected text for the `WRONG` span.
- For adjacent or multi-character spelling errors, a dataset may contain
  multiple `MISTAKE` entries with the same `WRONG` and `CORRECTION`, one for
  each erroneous character location.
- Current evaluation expects spelling-style replacements, so `WRONG` and
  `CORRECTION` should normally have the same character length.
