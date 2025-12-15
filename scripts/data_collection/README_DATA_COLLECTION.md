# Real Swahili Data Collection

Scripts for collecting real-world Swahili text containing occupation terms.

## Quick Start

```bash
# Run entire pipeline
./scripts/data_collection/collect_real_data.sh
```

## Individual Scripts

### 1. Swahili News Dataset (31K articles)

**Source**: Zenodo - Swahili News Dataset
**URL**: https://zenodo.org/record/5514203
**Size**: ~200MB
**Quality**: Professional journalism from Kenya (2015-2020)

```bash
# Download and mine
python3 scripts/data_collection/download_swahili_news.py

# Output: data/analysis/swahili_news_occupations.csv
```

**Expected yield**: 5,000-10,000 sentences with occupations

### 2. Kwici Wikipedia Corpus (151K sentences)

**Source**: GitHub - Kwici/Wiki-Corpus-Swahili
**URL**: https://github.com/Kwici/Wiki-Corpus-Swahili
**Size**: ~30MB
**Quality**: Clean Wikipedia extractions, encyclopedic

```bash
# Clone and mine
python3 scripts/data_collection/mine_kwici_corpus.py

# Output: data/analysis/kwici_occupations.csv
```

**Expected yield**: 2,000-5,000 sentences with occupations

### 3. Twitter Swahili Scraper (Natural language)

**Source**: Twitter/X
**Tool**: snscrape (no API key needed)
**Quality**: Conversational, diverse, natural

**Install snscrape first**:
```bash
pip install snscrape
# Or from GitHub
pip install git+https://github.com/JustAnotherArchivist/snscrape.git
```

**Run scraper**:
```bash
# Test with 5 terms, 100 tweets each
python3 scripts/data_collection/scrape_twitter_swahili.py \
  --max-per-term 100 \
  --limit-terms 5

# Full run (all 29 occupation terms)
python3 scripts/data_collection/scrape_twitter_swahili.py \
  --max-per-term 100

# Output: data/analysis/twitter_swahili_occupations.csv
```

**Expected yield**: 1,000-3,000 high-quality tweets

## Output Format

All scripts output CSV files with these fields:

**News & Kwici**:
```csv
text,source,file
"Daktari alipima mgonjwa...",swahili_news,article_123.json
```

**Twitter**:
```csv
text,source,term,date,username,likes,retweets
"Mwalimu wangu ni mzuri",twitter,mwalimu,2025-11-27,user123,15,3
```

## Data Quality Filters

All scripts apply quality filters:
- ✅ Length: 20-500 characters
- ✅ Contains occupation term (word boundary matching)
- ✅ Language indicators (Swahili patterns)
- ✅ No excessive URLs/hashtags (Twitter only)

## Expected Total Yield

| Source | Expected Sentences | Quality | Time to Collect |
|--------|-------------------|---------|-----------------|
| News Dataset | 5,000-10,000 | High (professional) | ~10 minutes |
| Kwici Corpus | 2,000-5,000 | High (encyclopedic) | ~5 minutes |
| Twitter | 1,000-3,000 | Medium (conversational) | ~30 minutes |
| **Total** | **8,000-18,000** | Mixed | **~45 minutes** |

## Next Steps After Collection

1. **Review collected data**:
   ```bash
   wc -l data/analysis/*.csv
   head -20 data/analysis/swahili_news_occupations.csv
   ```

2. **Sample for annotation** (recommend 1,000-2,000 sentences):
   ```bash
   # Random sample from each source
   shuf -n 300 data/analysis/swahili_news_occupations.csv > sample_news.csv
   shuf -n 300 data/analysis/kwici_occupations.csv > sample_kwici.csv
   shuf -n 400 data/analysis/twitter_swahili_occupations.csv > sample_twitter.csv
   ```

3. **Create annotation task**:
   - Use Google Sheets or Label Studio
   - Recruit 3+ Swahili native speakers (Kenya/Tanzania/Uganda)
   - Double-annotate for Cohen's Kappa
   - Labels: has_bias (true/false), bias_category, expected_correction

4. **Build ground truth**:
   ```bash
   # Merge annotated samples into ground_truth_sw.csv
   # Keep original 63 hand-curated + add 1,000+ annotated real data
   ```

5. **Evaluate real vs synthetic**:
   ```bash
   # Compare model performance on:
   # - Original 63 hand-curated (baseline)
   # - 1,000+ real annotated data
   # - 44K synthetic templates (previous)
   ```

## Troubleshooting

**News download fails**:
- Download manually from https://zenodo.org/record/5514203
- Save to `data/raw/swahili-news.zip`
- Run with `--skip-download`

**Kwici clone fails**:
- Clone manually: `git clone https://github.com/Kwici/Wiki-Corpus-Swahili data/raw/kwici-corpus`
- Run with `--skip-clone`

**Twitter scraping fails**:
- Install snscrape: `pip install snscrape`
- Check internet connection
- Twitter rate limits may apply (wait 15 minutes between runs)

## Notes

- **No API keys required** for any of these scripts
- **Respects rate limits** and website policies
- **Real data only** - no synthetic template generation
- **Designed for annotation** - outputs require human labeling before use

## License & Attribution

- **Swahili News Dataset**: Licensed under CC BY 4.0, cite original Zenodo record
- **Kwici Corpus**: MIT License, cite Kwici GitHub repository
- **Twitter data**: Follow Twitter TOS, use for research only
