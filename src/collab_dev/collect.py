"""
GitHub repository data collector for collab.dev

This module validates a GitHub repository URL provided as command line argument,
extracts the owner and repository name, and collects data from the repository.
"""

import argparse
import re
import sys
from typing import Optional, Tuple

from fetcher.fetch import process_repository


def parse_github_repo_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Parse and validate a GitHub repository URL.

    Args:
        url: A string representing a GitHub repository URL in one of these formats:
             - owner/repo_name
             - https://github.com/owner/repo_name

    Returns:
        A tuple of (owner, repo_name) if valid, None otherwise
    """
    # Pattern for simple format: owner/repo_name
    simple_pattern = r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$"

    # Pattern for https format: https://github.com/owner/repo_name
    https_pattern = r"^https?://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)/?$"

    # Try to match each pattern
    for pattern in [simple_pattern, https_pattern]:
        match = re.match(pattern, url)
        if match:
            return match.group(1), match.group(2)

    return None


def main():
    """
    Main function that validates GitHub repository URL from command line arguments
    and collects data from the specified repository.

    Parses command line arguments to get the repository URL and the number of PRs to fetch,
    validates the URL, and then processes the repository to collect and save data.
    """
    parser = argparse.ArgumentParser(description="Collect data from a GitHub repository")
    parser.add_argument("repo_url", help="GitHub repository URL (owner/repo_name)")
    parser.add_argument(
        "-n",
        "--num-prs",
        type=int,
        default=100,
        help="Number of PRs to fetch (default: 100)",
    )

    args = parser.parse_args()

    # Validate the repository URL
    result = parse_github_repo_url(args.repo_url)

    if result:
        owner, repo_name = result
        print(f"Fetching data from GitHub repository: {owner}/{repo_name}")
        try:
            # Process the repository to fetch and save all data
            result = process_repository(owner, repo_name, args.num_prs)
            print(f"Successfully collected data from {owner}/{repo_name}")
            print(f"Data saved to {result.get('path', 'output directory')}")
            print(
                f"You can view the report by running `pdm serve` and navigating to http://127.0.0.1:5000/{owner}/{repo_name}"
            )
        except Exception as e:
            print(f"Error fetching repository data: {e}")
            sys.exit(1)
    else:
        print(f"Error: '{args.repo_url}' is not a valid GitHub repository URL")
        print("Valid formats include: owner/repo_name, https://github.com/owner/repo_name")
        sys.exit(1)


if __name__ == "__main__":
    main()
