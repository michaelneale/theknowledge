import requests
from datetime import datetime, timedelta
import os

# GitHub personal access token
access_token = os.environ.get("GITHUB_READ_TOKEN")

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

def check_token_permissions():
    for org in organizations:
        # Test fetching repositories
        repo_response = requests.get(repos_url.format(org=org), headers=headers)
        if repo_response.status_code == 403:
            print(f"Error: Your token does not have permission to fetch repositories for organization '{org}'.")
            return False

        # Test searching for issues
        repos = repo_response.json()
        if repos:
            test_repo = repos[0]['name']
            search_params = {
                "q": f"repo:{org}/{test_repo} is:issue is:closed",
                "per_page": 1,
            }
            search_response = requests.get(search_url, headers=headers, params=search_params)
            if search_response.status_code == 403:
                print(f"Error: Your token does not have permission to search for issues in organization '{org}'.")
                return False
        else:
            print(f"Warning: No repositories found for organization '{org}'. Skipping issue search test.")

    return True

if not check_token_permissions():
    print("Token does not have the necessary permissions. Exiting.")
    exit(1)

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
                                body_summary = item['body'][:500] if item['body'] else "No description provided."
                                file.write(f"  - {item['title']}: {body_summary}...\n")
                        else:
                            file.write(f"  No closed {item_type}s in the past week.\n")
                    elif items_response.status_code == 403:
                        file.write(f"  No recent activity found for {item_type}s in repository {repo_name}.\n")
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