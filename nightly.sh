#!/bin/bash
# Nightly: fetch next topic from topics.json (real Met data), rebuild, list files to push.
set -e; cd /workspace/art-site
python3 build.py next | tee /tmp/nightly.log
SLUG=$(grep '^NEW ' /tmp/nightly.log | cut -d' ' -f2)
N=$(python3 -c "import json;print(len(json.load(open('data/$SLUG.json'))['works']))")
[ "$N" -ge 8 ] || { echo "TOO_FEW_WORKS $SLUG ($N) - refine topic filters, do not publish"; exit 2; }
python3 build.py build
echo "PUSH (repo yoloboydelis/yoloboydelis.github.io, branch main, <=4 \$file args per push_files call):"
echo "  $SLUG/index.html  index.html  sitemap.xml"
