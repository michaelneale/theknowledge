import requests
from datetime import datetime, timedelta
import os

# GitHub personal access token
access_token = os.environ.get("GITHUB_ACCESS_TOKEN")

# List of GitHub organizations to search
organizations = ["TBD54566975"]

# Number of days for closed pull requests
days_closed = 30

# GitHub API endpoint for searching issues and pull requests
search_url = "https://api.github.com/search/issues"

# Headers for authentication
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.github.v3+json",
}

# List to store all pull requests
all_prs = []

# Iterate over each organization
for org in organizations:
    print(f"Searching pull requests in organization: {org}")

    # Calculate the date threshold for closed pull requests (2 weeks ago)
    closed_date_threshold = (datetime.now() - timedelta(days=days_closed)).strftime("%Y-%m-%d")

    # Search query parameters for open pull requests
    open_params = {
        "q": f"is:pr is:open org:{org}",
        "sort": "comments",
        "order": "desc",
        "per_page": 100,
    }

    # Search query parameters for closed pull requests
    closed_params = {
        "q": f"is:pr is:closed org:{org} closed:>={closed_date_threshold}",
        "sort": "comments",
        "order": "desc",
        "per_page": 100,
    }

    # Send GET requests to the GitHub API for open and closed pull requests
    open_response = requests.get(search_url, headers=headers, params=open_params)
    closed_response = requests.get(search_url, headers=headers, params=closed_params)

    # Check if the requests were successful
    if open_response.status_code == 200 and closed_response.status_code == 200:
        # Parse the JSON responses
        open_data = open_response.json()
        closed_data = closed_response.json()

        # Filter out pull requests made by GitHub Actions and Dependabot
        filtered_open_prs = [pr for pr in open_data["items"] if not pr["user"]["login"].endswith("[bot]")]
        filtered_closed_prs = [pr for pr in closed_data["items"] if not pr["user"]["login"].endswith("[bot]")]

        # Add the filtered pull requests to the list of all pull requests
        all_prs.extend(filtered_open_prs)
        all_prs.extend(filtered_closed_prs)
    else:
        print(f"Error: Open - {open_response.status_code}, Closed - {closed_response.status_code}")

# Sort the pull requests based on the number of comments
sorted_prs = sorted(all_prs, key=lambda pr: pr["comments"], reverse=True)

# Output pull request information and comments to a plain text file
with open("prs.txt", "w") as file:
    for pr in sorted_prs:
        file.write(f"Pull Request: {pr['html_url']}\n")
        file.write(f"Title: {pr['title']}\n")
        file.write(f"Description: {pr['body']}\n")
        file.write(f"Created At: {pr['created_at']}\n")
        file.write(f"Comments: {pr['comments']}\n")
        file.write("\n")

        # Get the list of comments for each pull request
        comments_url = pr["comments_url"]
        comments_response = requests.get(comments_url, headers=headers)
        if comments_response.status_code == 200:
            comments_data = comments_response.json()
            for comment in comments_data:
                if not comment["user"]["login"].endswith("[bot]"):
                    file.write("===========================================\n")
                    file.write(f"Comment by {comment['user']['login']}:\n")
                    file.write("===========================================\n")
                    file.write(f"{comment['body']}\n")
                    file.write("\n")
        else:
            print(f"Error retrieving comments: {comments_response.status_code} - {comments_response.text}")

        file.write("---\n")

print("Pull request information and comments saved to prs.txt")