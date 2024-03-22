import requests
from datetime import datetime, timedelta
import os
from collections import defaultdict

# GitHub personal access token
access_token = os.environ.get("GITHUB_ACCESS_TOKEN")

# List of GitHub organizations to search
organizations = ["TBD54566975"]

# Number of days the pull request should be open
days_open = 1

# Number of top users to display
top_n_users = 10

# GitHub API endpoint for searching issues and pull requests
search_url = "https://api.github.com/search/issues"

# Headers for authentication
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.github.v3+json",
}

# Dictionary to store user comment counts
user_comment_counts = defaultdict(int)

# List to store all pull requests
all_prs = []

# Iterate over each organization
for org in organizations:
    print(f"Searching pull requests in organization: {org}")

    # Calculate the date threshold (1 day ago)
    date_threshold = (datetime.now() - timedelta(days=days_open)).strftime("%Y-%m-%d")

    # Search query parameters
    params = {
        "q": f"is:pr is:open org:{org} created:<={date_threshold}",
        "sort": "comments",
        "order": "desc",
        "per_page": 100,
    }

    # Send a GET request to the GitHub API
    response = requests.get(search_url, headers=headers, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()

        # Filter out pull requests made by GitHub Actions and Dependabot
        filtered_prs = [pr for pr in data["items"] if not pr["user"]["login"].endswith("[bot]")]

        # Add the filtered pull requests to the list of all pull requests
        all_prs.extend(filtered_prs)
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Filter out pull requests with only 1 comment
filtered_prs = [pr for pr in all_prs if pr["comments"] > 1]

# Sort the filtered pull requests based on the number of comments
sorted_prs = sorted(filtered_prs, key=lambda pr: pr["comments"], reverse=True)

# Get the top 10 pull requests
top_prs = sorted_prs[:10]

print("\nTop 10 Pull Requests:")
for pr in top_prs:
    print(f"Pull Request: {pr['html_url']}")
    print(f"Title: {pr['title']}")
    print(f"Comments: {pr['comments']}")
    print("---")

    # Get the list of commenters for each pull request
    comments_url = pr["comments_url"]
    comments_response = requests.get(comments_url, headers=headers)
    if comments_response.status_code == 200:
        comments_data = comments_response.json()
        commenters = [comment["user"]["login"] for comment in comments_data if not comment["user"]["login"].endswith("[bot]")]
        for commenter in commenters:
            user_comment_counts[commenter] += 1
    else:
        print(f"Error retrieving comments: {comments_response.status_code} - {comments_response.text}")

print("\nTop Users by Comment Count:")
top_users = sorted(user_comment_counts.items(), key=lambda x: x[1], reverse=True)[:top_n_users]
for user, count in top_users:
    print(f"{user}: {count} comments")