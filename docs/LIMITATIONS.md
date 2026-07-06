# Limitations & Responsible Use

Confluex is an **analytic aid**, not an autonomous decision-maker.

## Scope
- Extraction is regex + gazetteer based: excellent on structured indicators and
  known named entities, but it will miss novel entities not in the gazetteer and
  can over-match ambiguous aliases. Curate gazetteers per mission.
- The default reasoning provider is **extractive** (selects existing sentences);
  it does not generate new prose. Generative summarization requires the optional
  local Ollama backend, whose quality depends on the model you host.
- Retrieval is lexical TF-IDF, not semantic embeddings — strong for keyword and
  indicator queries, weaker for purely conceptual paraphrase.
- Correlation is co-occurrence within reports; it indicates association, not
  causation or confirmed relationship.

## Responsible use
Process only data you are authorized to handle, under all applicable laws and
intelligence-oversight rules. The optional model backend runs on infrastructure
you control; the platform performs no third-party data egress. Outputs are
leads for analyst corroboration. You are solely responsible for your use
(LICENSE §9, NOTICE).

Bundled sample data is synthetic and fictitious (RFC 5737 IP ranges).
