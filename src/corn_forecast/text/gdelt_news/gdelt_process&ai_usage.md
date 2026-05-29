# GDELT news data process & Score with OpenAI API

This folder contains scripts for turning GDELT corn-related news
titles into weekly news features for the CORN ETF / corn futures research
pipeline.

01 - fetch news titles by months from GDELT (201502 - 202603) using BigQuery
02 - for test use, since OpenAI API needed, first scoring with 1-month news titles
03 - after testing, let OpenAI to score every lines of news
04 - combined all the news with scores
05 - aggregate the scores by weekly

# AI Usage 

AI assistance was used in the GDELT news-processing:

- BigQuery GDELT title extraction:
 - Used to pull corn-related news titles from `gdelt-bq.gdeltv2.gkg_partitioned`.
 - Included PAGE_TITLE extraction and URL slug fallback for older GDELT records.
- OpenAI title scoring:
  - Used the OpenAI API to score each title on structured corn-market dimensions.
- Monthly batch scoring:
  - Used to score all monthly GDELT title files and skip already-completed months.
- Weekly aggregation:
  - Aggregated article-level scores into weekly features using `relevance_score` weighting.
- Help with expanding more CLI arguments

Human Review and Improvement:
1. Reviewed the filted news titles (random) and updated the filtered conditions 
    (such as, initially considered both indluding corn and weather news, but too noisy)
2. Reviewed the LLM prompts, and try different ones to balance both the scoring quality and running time,
    and decide which score might need and which way to feed to LLM
    (although still need more than 6-7 hours to go through all the )
3. Reviewed the aggregated weekly scores logic


