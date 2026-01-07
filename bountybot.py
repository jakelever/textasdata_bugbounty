#!/usr/bin/env python
# coding: utf-8

import requests
from collections import Counter
import re
import pandas as pd

def getPagedGithubData(base_url):
    per_page = 30
    page = 1
    
    combiner = '&' if '?' in base_url else '?'
    
    results = []
    while True:
        issues_comments_url = f'{base_url}{combiner}per_page={per_page}&page={page}'
        r = requests.get(issues_comments_url)
        assert r.status_code == 200, f"Error ({r.status_code=}) with {issues_comments_url=}"
        results_on_page = r.json()
        results += results_on_page
        
        if len(results_on_page) < per_page:
            break
            
        page += 1
        
    return results

def getIssueWithComments(username,repo):
    # Fetch the issues and comments from the Github API
    issues = getPagedGithubData(f'https://api.github.com/repos/{username}/{repo}/issues?state=all')
    issues_comments = getPagedGithubData(f'https://api.github.com/repos/{username}/{repo}/issues/comments')
    
    # Pull out the issue details into a simpler data structure
    tidy_issues = {}
    for issue in issues:
        as_comment = {'user':issue['user']['login'],'created_at':issue['created_at'],'text':issue['body']}
        tidy_issue = {'title':issue['title'], 'user':issue['user']['login'], 'state':issue['state'], 'comments':[as_comment]}
        issue_id = issue['number']
        tidy_issues[issue_id] = tidy_issue
        
    # Attach the issue comments to the structure
    for issues_comment in issues_comments:
        issue_id = int(issues_comment['issue_url'].split('/')[-1])
        tidy_comment = {'user':issues_comment['user']['login'],'created_at':issues_comment['created_at'],'text':issues_comment['body']}
        tidy_issues[issue_id]['comments'].append(tidy_comment)
        
    # Sort the comments by date
    for issue_id in tidy_issues:
        tidy_issues[issue_id]['comments'] = sorted(tidy_issues[issue_id]['comments'], key=lambda x:x['created_at'])
    
    return tidy_issues

def createLeaderboard(issues_with_comments, scorer):
    scores = Counter()

    points_regex = re.compile(r'\b(\d+) points?\b', re.IGNORECASE)

    for issue_id in sorted(issues_with_comments):
        issue_with_comments = issues_with_comments[issue_id]

        if issue_with_comments['state'] == 'closed':
            user = issue_with_comments['user']
            points = 0

            scorer_comments = [ c for c in issues_with_comments[issue_id]['comments'] if c['user'] == scorer ]

            if len(scorer_comments) > 0:
                last_scorer_comment = scorer_comments[-1]

                points_mentions = points_regex.findall(last_scorer_comment['text'])
                assert len(points_mentions) <= 1, f"Found >1 points mentions for {issue_id=} in {last_scorer_comment['text']}"
                
                if len(points_mentions) == 1:
                    points = int(points_mentions[0])
                    scores[user] += points
            
            print(f"Issue {issue_id}: {points} to {user}")
        else:
            print(f"Issue {issue_id}: Not closed")
            
    leaderboard = pd.DataFrame(scores.most_common())
    leaderboard.columns = ['user','points']
    
    return leaderboard

def updateReadmeWithLeaderboard(leaderboard):
    with open('README.md') as f:
        readme = f.read()

    leaderboard_section = '## Leaderboard'
    leaderboard_location = readme.index(leaderboard_section)
    readme_without_leaderboard = readme[:(leaderboard_location + len(leaderboard_section))]

    leaderboard_markdown = leaderboard.to_markdown(index=False)

    readme_with_leaderboard = f"{readme_without_leaderboard}\n\n{leaderboard_markdown}\n"

    with open('README.md','w') as f:
        f.write(readme_with_leaderboard)
        
    print("\nREADME.md updated with leaderboard")

def main():
    print("   __                  __       __        __ ")
    print("  / /  ___  __ _____  / /___ __/ /  ___  / /_")
    print(" / _ \/ _ \/ // / _ \/ __/ // / _ \/ _ \/ __/")
    print("/_.__/\___/\_,_/_//_/\__/\_, /_.__/\___/\__/ ")
    print("                        /___/                ")
    
    scorer = 'jakelever'

    issues_with_comments = getIssueWithComments('jakelever','textasdata_bugbounty')

    leaderboard = createLeaderboard(issues_with_comments, scorer)

    updateReadmeWithLeaderboard(leaderboard)

    total_points = sum(leaderboard['points'])
    print(f"Total Points = {total_points}")

if __name__ == '__main__':
    main()
    
