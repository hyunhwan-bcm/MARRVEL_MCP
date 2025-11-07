# PubMed and PMC Tools Documentation

This document provides detailed information about the PubMed and PMC (PubMed Central) tools available in MARRVEL-MCP.

## Overview

MARRVEL-MCP provides 11 tools for searching and extracting content from PubMed and PubMed Central (PMC) articles:

1. **search_pubmed** - Search PubMed by keyword
2. **get_pubmed_article** - Get article details by PMID
3. **pmid_to_pmcid** - Convert PMID to PMCID
4. **get_pmc_abstract_by_pmcid** - Get abstract from PMC by PMCID
5. **get_pmc_abstract_by_pmid** - Get abstract from PMC by PMID
6. **get_pmc_fulltext_by_pmcid** - Get full text from PMC by PMCID
7. **get_pmc_fulltext_by_pmid** - Get full text from PMC by PMID
8. **get_pmc_tables_by_pmcid** - Extract tables with captions by PMCID
9. **get_pmc_tables_by_pmid** - Extract tables with captions by PMID
10. **get_pmc_figure_captions_by_pmcid** - Extract figure captions by PMCID
11. **get_pmc_figure_captions_by_pmid** - Extract figure captions by PMID

## Tool Details

### search_pubmed

Search PubMed for biomedical literature.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum number of results (1-100, default: 50)
- `email` (string, optional): Email for NCBI API (default: "marrvel@example.com")

**Returns:**
```json
{
  "query": "BRCA1 breast cancer",
  "total_results": 12543,
  "returned_results": 50,
  "max_results": 50,
  "articles": [
    {
      "pubmed_id": "12345678",
      "title": "Article title",
      "abstract": "Article abstract...",
      "authors": ["Author1", "Author2"],
      "journal": "Journal name",
      "publication_date": "2023-01-15",
      "doi": "10.1234/example",
      "keywords": ["keyword1", "keyword2"]
    }
  ]
}
```

**Example queries:**
- "BRCA1 breast cancer"
- "Rett syndrome MECP2"
- "TP53 therapy"

---

### get_pubmed_article

Retrieve detailed information for a specific PubMed article by PMID.

**Parameters:**
- `pubmed_id` (string, required): PubMed ID
- `email` (string, optional): Email for NCBI API

**Returns:**
Article metadata including title, abstract, authors, journal, DOI, keywords, methods, results, and conclusions.

---

### pmid_to_pmcid

Convert a PubMed ID (PMID) to a PMC ID (PMCID) for full-text access.

**Parameters:**
- `pmid` (string, required): PubMed ID

**Returns:**
```json
{
  "pmid": "23251661",
  "pmcid": "PMC3518823"
}
```

**Note:** Not all PubMed articles are available in PMC. If an article is not open access, the `pmcid` field will be empty.

---

### get_pmc_abstract_by_pmcid

Retrieve abstract only from a PMC article by PMC ID.

**Parameters:**
- `pmcid` (string, required): PMC ID (must start with "PMC")

**Returns:**
```json
{
  "pmcid": "PMC3518823",
  "abstract": "Abstract text..."
}
```

**Use case:** When you only need a quick summary without downloading the full article.

---

### get_pmc_abstract_by_pmid

Retrieve abstract from a PMC article by PubMed ID.

**Parameters:**
- `pmid` (string, required): PubMed ID

**Returns:**
```json
{
  "pmid": "23251661",
  "pmcid": "PMC3518823",
  "abstract": "Abstract text..."
}
```

**Note:** This tool first converts the PMID to PMCID, then retrieves the abstract.

---

### get_pmc_fulltext_by_pmcid

Retrieve full text of a PMC open-access article by PMC ID.

**Parameters:**
- `pmcid` (string, required): PMC ID (must start with "PMC")

**Returns:**
```json
{
  "pmcid": "PMC3518823",
  "fulltext": "Complete article text including introduction, methods, results, discussion..."
}
```

**Use case:** When you need the complete article content for detailed analysis.

**Note:** This extracts all text from the article body, including sections like Introduction, Methods, Results, Discussion, and Conclusions.

---

### get_pmc_fulltext_by_pmid

Retrieve full text of a PMC article by PubMed ID.

**Parameters:**
- `pmid` (string, required): PubMed ID

**Returns:**
```json
{
  "pmid": "23251661",
  "pmcid": "PMC3518823",
  "fulltext": "Complete article text..."
}
```

---

### get_pmc_tables_by_pmcid

Extract tables with captions from a PMC article by PMC ID.

**Parameters:**
- `pmcid` (string, required): PMC ID (must start with "PMC")

**Returns:**
```json
{
  "pmcid": "PMC3518823",
  "table_count": 3,
  "tables": [
    {
      "table_number": 1,
      "caption": "Table 1. Patient demographics and clinical characteristics.",
      "table_markdown": "| Variable | Value |\n| --- | --- |\n| Age | 45.2±12.3 |\n| Gender (M/F) | 120/80 |"
    }
  ]
}
```

**Use case:** Extract tabular data from research articles for analysis or comparison.

**Format:** Tables are returned in markdown format for easy parsing and display.

---

### get_pmc_tables_by_pmid

Extract tables with captions from a PMC article by PubMed ID.

**Parameters:**
- `pmid` (string, required): PubMed ID

**Returns:**
Same as `get_pmc_tables_by_pmcid` but includes `pmid` field.

---

### get_pmc_figure_captions_by_pmcid

Extract figure captions from a PMC article by PMC ID.

**Parameters:**
- `pmcid` (string, required): PMC ID (must start with "PMC")

**Returns:**
```json
{
  "pmcid": "PMC3518823",
  "figure_count": 5,
  "figures": [
    {
      "figure_number": 1,
      "figure_id": "fig1",
      "label": "Figure 1",
      "caption": "Expression patterns of BRCA1 in breast tissue. (A) Normal tissue. (B) Tumor tissue."
    }
  ]
}
```

**Use case:** Understand visual content and experimental design without viewing the actual images.

---

### get_pmc_figure_captions_by_pmid

Extract figure captions from a PMC article by PubMed ID.

**Parameters:**
- `pmid` (string, required): PubMed ID

**Returns:**
Same as `get_pmc_figure_captions_by_pmcid` but includes `pmid` field.

---

## Workflow Examples

### Example 1: Search and Read Full Article

```
1. Search: search_pubmed(query="BRCA1 therapy", max_results=5)
2. Convert: pmid_to_pmcid(pmid="12345678")
3. Read: get_pmc_fulltext_by_pmcid(pmcid="PMC1234567")
```

### Example 2: Extract Tables from Article

```
1. Search: search_pubmed(query="TP53 clinical trials", max_results=3)
2. Get tables: get_pmc_tables_by_pmid(pmid="12345678")
3. Analyze table data
```

### Example 3: Quick Literature Review

```
1. Search: search_pubmed(query="Rett syndrome treatment", max_results=10)
2. For each article:
   - Get abstract: get_pmc_abstract_by_pmid(pmid="...")
   - Extract figures: get_pmc_figure_captions_by_pmid(pmid="...")
```

## Error Handling

All tools return JSON with error information when issues occur:

```json
{
  "error": "Error description",
  "pmcid": "PMC1234567"
}
```

Common errors:
- "Invalid PMCID" - PMCID must start with "PMC"
- "Invalid PMID" - PMID must be numeric
- "Could not convert PMID to PMCID" - Article not available in PMC (not open access)
- "No abstract found" - Article doesn't have an abstract
- "No full text body found" - Full text not available
- HTTP errors - Network or API issues

## Important Notes

1. **Open Access Only**: PMC tools only work with open-access articles. Not all PubMed articles are available in PMC.

2. **PMID vs PMCID**:
   - PMID (PubMed ID): All PubMed articles have a PMID
   - PMCID (PMC ID): Only open-access articles in PMC have a PMCID
   - Use `pmid_to_pmcid` to check if an article is available in PMC

3. **Rate Limiting**: NCBI APIs have rate limits. For production use, provide a valid email address.

4. **Content Quality**: The quality of extracted content depends on the XML structure of the original article. Some older articles may have incomplete metadata.

5. **Table Format**: Tables are converted to markdown format. Complex table structures (merged cells, nested tables) may not render perfectly.

## Best Practices

1. **Start with Search**: Use `search_pubmed` to find relevant articles before extracting details.

2. **Check Availability**: Use `pmid_to_pmcid` to verify an article is available in PMC before trying to extract full text.

3. **Use Abstracts First**: Get abstracts before full text to quickly filter relevant articles.

4. **Extract Specific Content**: Use table and figure tools to extract specific types of content rather than parsing full text.

5. **Handle Errors**: Always check for error fields in responses and handle cases where content is not available.

## Related Resources

- [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
- [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/)
- [NCBI E-utilities API](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [MARRVEL Website](https://marrvel.org)
