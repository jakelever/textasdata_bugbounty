#!/bin/bash
set -euxo pipefail

git pull

python bountybot.py | tee bounty_output.txt

TOTALPOINTS=$(cat bounty_output.txt | grep "Total Points" | cut -f 4 -d ' ')

git add README.md

git commit -m "Update leaderboard with $TOTALPOINTS total points"

git push

