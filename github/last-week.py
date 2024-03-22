import requests
from datetime import datetime, timedelta
import os

# GitHub personal access token
access_token = os.environ.get("GITHUB_ACCESS_TOKEN")

# List of GitHub organizations to search
organizations = ["TBD54566975", "tbdeng"]

# File to write the results
output_file = "github_summary_past_week.txt"

# GitHub API endpoints
repos_url = "https://api.github.com/orgs/{org}/repos"
search_url = "https://api.github.com/search/issues"

# Headers for authentication
headers = {
    "Authorization": f"Bearer {access_token}",
    "Accept": "application/vnd.github.v3+json",
}

# Calculate the date threshold (7 days ago)
date_threshold = (datetime.now() - timedelta(days=7)).isoformat()

def fetch_and_write_summary(organization):
    with open(output_file, "a") as file:
        file.write(f"Organization: {organization}\n")
        file.write("Summary of Closed PRs and Issues for the Past Week:\n\n")
        
        # Fetch repositories for the organization
        response = requests.get(repos_url.format(org=organization), headers=headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                repo_name = repo['name']
                # Write repository header
                file.write(f"Repository: {repo_name}\n")

                # Fetch and write PRs and issues for the repository
                for item_type in ["pr", "issue"]:
                    search_params = {
                        "q": f"repo:{organization}/{repo_name} is:{item_type} is:closed closed:>={date_threshold}",
                        "per_page": 100,
                    }
                    items_response = requests.get(search_url, headers=headers, params=search_params)
                    if items_response.status_code == 200:
                        items = items_response.json()["items"]
                        if items:
                            file.write(f"  {item_type.capitalize()}s:\n")
                            for item in items:
                                body_summary = item['body'][:100] if item['body'] else "No description provided."
                                file.write(f"  - {item['title']}: {body_summary}...\n")
                        else:
                            # Note if no PRs/issues found
                            file.write(f"  No closed {item_type}s in the past week.\n")
                    else:
                        file.write(f"Error fetching {item_type}s for repository {repo_name}: {items_response.status_code}\n")
                file.write("\n")  # Add space after each repo
        else:
            file.write(f"Error fetching repositories for organization {organization}: {response.status_code}\n")

# Clear the file before writing
open(output_file, "w").close()

# Fetch and write summaries for each organization
for org in organizations:
    fetch_and_write_summary(org)

print(f"Summary of closed PRs and issues from the past week has been written to {output_file}.")
