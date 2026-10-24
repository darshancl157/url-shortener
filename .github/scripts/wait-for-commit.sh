#!/usr/bin/env bash
# Poll a URL that returns JSON like {"commit": "<sha>"} until it reports $GITHUB_SHA.
# Usage: bash .github/scripts/wait-for-commit.sh <url>
set -u
url="$1"
for i in $(seq 1 40); do
  commit=$(curl -s --max-time 30 -H "Cache-Control: no-cache" "$url?check=$i" \
    | jq -r '.commit // empty' 2>/dev/null || true)
  echo "attempt $i: $url reports '${commit:-nothing yet}', want $GITHUB_SHA"
  if [ ${#commit} -ge 7 ] && [[ "$GITHUB_SHA" == "$commit"* ]]; then
    echo "serving this commit"
    exit 0
  fi
  sleep 15
done
echo "$url did not report $GITHUB_SHA within 10 minutes"
exit 1