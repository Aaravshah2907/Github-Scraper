import requests
from bs4 import BeautifulSoup
import time
import os
from headers import HEADERS

def get_page_content(url):
    try:
        time.sleep(1)  # Respect GitHub's rate limits
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def scrape_all_repos(username):
    all_repos = []
    page = 1
    
    base_url = f"https://github.com/{username}?tab=repositories&page="
    
    print(f"Starting repository scraping for @{username}...")

    while True:
        url = base_url + str(page)
        html_content = get_page_content(url)
        
        if not html_content:
            print(f"Stopping scan: Failed to fetch page {page}.")
            break

        soup = BeautifulSoup(html_content, 'html.parser')
        
        repo_tags = soup.select('h3 a[itemprop="name codeRepository"]')

        if not repo_tags:
            if page == 1:
                user_check = soup.select_one('h1.vcard-names span.p-name')
                if user_check and user_check.text.strip().lower() == username.lower():
                    print("Found user profile, but no repository links found. The HTML structure might have changed again.")
                else:
                    print(f"User '{username}' not found on GitHub or profile is inaccessible.")
            break
            
        print(f"Processing Page {page}: Found {len(repo_tags)} repositories.")
        
        for tag in repo_tags:
            repo_path = tag.get('href') # e.g., /Aaravshah2907/repo-name
            
            if repo_path and repo_path.startswith(f"/{username}/"):
                full_name = repo_path.lstrip('/')
                repo_name = full_name.split('/')[-1].strip()
                repo_url = f"https://github.com{repo_path}"
                all_repos.append({'name': repo_name, 'url': repo_url, 'full_name': full_name})
            
        next_button = soup.select_one('.next_page')
        
        is_disabled = next_button and ('disabled' in next_button.get('class', []) or next_button.has_attr('disabled'))

        if is_disabled or not next_button:
            break

        page += 1

    print(f"Repository collection complete. Total found: {len(all_repos)}")
    return all_repos

def fetch_readme_content(repo_full_name, default_branch='main'):
    raw_url = f"https://raw.githubusercontent.com/{repo_full_name}/{default_branch}/README.md"
    
    print(f"  -> Attempting README fetch for {repo_full_name}...")
    
    try:
        time.sleep(0.5) 
        response = requests.get(raw_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 200:
            return response.text.strip()
        
        if response.status_code == 404 and default_branch == 'main':
            return fetch_readme_content(repo_full_name, default_branch='master')
            
        return "README not found or inaccessible."

    except requests.exceptions.RequestException:
        return "README fetch failed due to connectivity error."

def export_to_markdown(username, repositories):
    filename = f"{username}_github_projects_data.md"
    
    markdown_output = f"# GitHub Project Summary for @{username}\n\n"
    markdown_output += f"Total Public Repositories Scraped: {len(repositories)}\n\n"
    markdown_output += "---\n\n"
    
    if not repositories:
        markdown_output += "No projects were found to summarize."
        return

    print("\nStarting README fetching and Markdown export...")
    
    for i, repo in enumerate(repositories):
        readme_content = fetch_readme_content(repo['full_name'])
        
        markdown_output += f"## {i+1}. Project: {repo['name']}\n"
        markdown_output += f"**URL:** {repo['url']}\n\n"
        
        markdown_output += "### README Content\n"
        markdown_output += f"```markdown\n{readme_content}\n```\n\n"
        markdown_output += "---\n\n"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(markdown_output)
    
    print(f"\nSuccessfully exported all project data to: {filename}")
    print("This file is now ready to be used as context for an LLM analysis.")


if __name__ == "__main__":
    github_username = "username_here" 
    
    all_repositories = scrape_all_repos(github_username)
    
    if all_repositories:
        export_to_markdown(github_username, all_repositories)
    else:
        print("Script finished without finding any repositories to process.")