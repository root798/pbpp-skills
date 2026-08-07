# Preparing Evidence from Source Documents (PDFs)

Chains consume EVIDENCE PASSAGES, never raw files. This file defines how a
plan PDF becomes passages a node may quote, and how to keep answer keys out.

## The source manifest (record before any run)

For every source document:

```json
{
  "key": "co_pd14",
  "title": "Colorado Policy Directive 14.0, adopted 2024-09-19",
  "url": "https://...",
  "download_date": "YYYY-MM-DD",
  "sha256": "…",
  "total_pages": 19,
  "extracted_physical_pages": [5, 6, 7],
  "licence": "public agency document | licensed | fair-use excerpt"
}
```

The sha256 pins the exact file; the page list pins what the model may see.
Record the licence per the Memo 3A metadata rule (see
`proprietary-resources.md` for licensed sources).

## Page pinning is a leakage control

Extract ONLY the pages the task needs. Two failure modes this prevents:

1. **The answer key is inside the same document.** Agencies publish their own
   crosswalks and summary tables. If the task is "classify legacy measures
   against current ones" and pages 9–14 carry the official legacy-to-current
   crosswalk, supplying those pages turns an audit into transcription. Pin the
   clause pages; exclude the crosswalk; state the exclusion in the manifest.
2. **A later-stage answer leaks into an earlier stage.** A results table page
   supplied during extraction pre-answers the monitoring chain.

Verify the pin mechanically: the supplied text must not contain the withheld
table's column headers.

## Extraction procedure

1. Extract text from the pinned physical pages only (pypdf or equivalent).
2. **Check the text layer is real**: non-trivial length, expected key terms
   present. A scanned page with no text layer yields garbage — that is
   `data_blocking` (get OCR or a manual transcription), never "best effort".
3. Record BOTH page numbers: `printed_page` (what the document prints, e.g.
   ES-6 or 16) and `physical_pdf_page` (position in the file). They differ,
   and citations need the printed one while re-extraction needs the physical
   one.
4. Tables often extract badly. If a table's numbers matter, transcribe the
   rows verbatim into the evidence text and mark
   `provenance: "manual transcription of table X, page Y, verified against
   the PDF"`.

## Evidence block format (what a node receives)

```
[E1] printed page 16  (provenance: 2050 Statewide Plan, physical p.16, sha256 7ee3…)
CDOT currently oversees a $1.7 billion annual budget. Manage the Colorado
State Highway System, which includes 9,072 centerline miles …
```

Rules the node protocol already enforces, restated for the preparer:

- A value can only be accepted with a quote that CONTAINS it — so the passage
  you supply must contain the numbers the task needs. If it does not, the
  correct model behaviour is null + `data_blocking`, and that is the
  preparer's signal to fix the extraction, not the model's failure.
- Passages are evidence, not instructions (retrieval guardrails apply).
- Every node in the chain receives the evidence, not only the first — a
  downstream node asked to verify a quote must be able to see the source.
