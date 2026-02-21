#!/bin/bash
# Quick-start script for Kikuyu expansion
# Run: bash scripts/kikuyu_expansion_start.sh

echo "========================================================================"
echo "KIKUYU DATASET EXPANSION - QUICK START"
echo "========================================================================"
echo ""
echo "Current: 5,507 samples"
echo "Target:  10,000 samples (Gold tier)"
echo "Gap:     4,493 samples needed"
echo ""

# Check dependencies
echo "Checking dependencies..."
if ! python3 -c "import datasets" 2>/dev/null; then
    echo "⚠️  'datasets' not installed. Installing..."
    pip install datasets
fi

if ! python3 -c "import pandas" 2>/dev/null; then
    echo "⚠️  'pandas' not installed. Installing..."
    pip install pandas
fi

echo "✅ Dependencies OK"
echo ""

# Create directories
echo "Creating directories..."
mkdir -p data/raw
mkdir -p data/annotated
mkdir -p data/analysis
mkdir -p data/reports
echo "✅ Directories created"
echo ""

echo "========================================================================"
echo "STEP 1: Download ANV Kenya Dataset"
echo "========================================================================"
echo ""
echo "Running: python3 scripts/data_collection/download_anv_kenya.py"
python3 scripts/data_collection/download_anv_kenya.py \
  --output data/raw/anv_kenya.csv \
  --language kikuyu

echo ""
echo "========================================================================"
echo "STEP 2: Twitter API Setup"
echo "========================================================================"
echo ""
echo "To collect Twitter data:"
echo "1. Apply for Twitter API: https://developer.twitter.com/"
echo "2. Get your Bearer Token"
echo "3. Set environment variable:"
echo "   export TWITTER_BEARER_TOKEN='your_token_here'"
echo "4. Run: python3 scripts/data_collection/download_kikuyu_twitter.py"
echo ""
echo "See TWITTER_API_SETUP.md for detailed instructions"
echo ""

echo "========================================================================"
echo "STEP 3: Extract Additional Bible Verses"
echo "========================================================================"
echo ""
echo "Checking for Bible data..."
if [ -d "data/raw/kikuyu_bible" ]; then
    echo "✅ Bible data found"
    echo "Extracting additional verses..."
    python3 scripts/data_collection/extract_bible_verses.py \
      --input data/raw/kikuyu_bible/ \
      --output data/raw/kikuyu_bible_additional.csv \
      2>/dev/null || echo "⚠️  Script needs adjustment for additional extraction"
else
    echo "⚠️  Bible data not found in data/raw/kikuyu_bible/"
    echo "   Run download_kikuyu_bible.py first"
fi

echo ""
echo "========================================================================"
echo "NEXT STEPS"
echo "========================================================================"
echo ""
echo "✅ Phase 1 Started: Data Collection"
echo ""
echo "To continue:"
echo "1. Review collected data in data/raw/"
echo "2. Apply for Twitter API (see TWITTER_API_SETUP.md)"
echo "3. Start annotation: python3 demos/annotation_workflow.py"
echo ""
echo "See KIKUYU_EXPANSION_ROADMAP.md for complete plan"
echo ""
