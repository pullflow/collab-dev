import logging
import os
import re
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from . import store
from .github_utils import (
    github_graphql_get_merged_pull_requests,
    github_graphql_get_pull_request_events,
    github_graphql_get_repository,
    process_timeline_events,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_repo_parts(repo_url: str) -> Tuple[str, str]:
    """Extract owner and name from a GitHub repository URL."""
    # Match patterns like https://github.com/owner/repo or owner/repo
    pattern = r"(?:https?://github\.com/)?([^/]+)/([^/]+)"
    match = re.match(pattern, repo_url)

    if not match:
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")

    return match.group(1), match.group(2)


def process_repository(owner: str, name: str, max_prs: Optional[int] = None, category: str = None) -> dict:
    """Process a repository - main entry point function

    Args:
        owner: GitHub repository owner
        name: GitHub repository name
        max_prs: Maximum number of pull requests to fetch (None for no limit)
        category: Optional category to classify the repository

    Returns:
        Dictionary with repository processing results
    """
    return fetch_repository_info(owner, name, max_prs=max_prs, category=category)


def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import traceback

            logger.error(f"Error in {func.__name__}: {e}")
            logger.error(f"Stack trace: {traceback.format_exc()}")
            raise e

    return wrapper


def get_repository_info(owner: str, name: str) -> Dict:
    """Fetch repository information from GitHub using GraphQL."""
    return github_graphql_get_repository(owner, name)


def get_pull_requests(owner: str, name: str, max_prs: Optional[int] = None) -> List[Dict]:
    """Fetch merged pull requests from GitHub using GraphQL API."""
    pull_requests = github_graphql_get_merged_pull_requests(owner, name)

    if max_prs:
        pull_requests = pull_requests[:max_prs]

    return pull_requests


def get_pull_request_events(owner: str, name: str, pr_number: int) -> List[Dict]:
    """Fetch timeline events for a pull request using GraphQL."""
    timeline_data = github_graphql_get_pull_request_events(owner, name, pr_number)

    if not timeline_data:
        return []

    repo_url = f"https://github.com/{owner}/{name}"
    repository_slug = f"{owner}/{name}"

    return process_timeline_events(timeline_data, repo_url, repository_slug)


def check_existing_repository(owner: str, name: str) -> Optional[Dict]:
    """Check if repository already exists in the file system."""
    repo_url = f"https://github.com/{owner}/{name}"
    repo_dir = store.get_repo_dir(owner, name)
    repo_file = os.path.join(repo_dir, "repository.csv")

    if os.path.exists(repo_file):
        # Simple representation of repository ID using owner/name
        return {"id": f"{owner}/{name}", "url": repo_url}

    return None


@error_handler
def fetch_repository_info(owner: str, name: str, max_prs: Optional[int] = None, category: str = None) -> dict:
    """Fetch repository information."""
    # Check if repository already exists
    existing_repo = check_existing_repository(owner, name)

    if existing_repo:
        # Process pull requests for existing repository
        result = fetch_pull_requests(owner, name, max_prs=max_prs)
        return {"status": "success", "repository_id": existing_repo["id"], **result}

    # Fetch repository information using GraphQL
    repo_data = get_repository_info(owner, name)

    if not repo_data:
        raise ValueError(f"Could not fetch data for repository: {owner}/{name}")

    # Save repository information
    save_result = store.save_repository_info(owner, name, repo_data, category)

    # Next stage - fetch pull requests
    result = fetch_pull_requests(owner, name, max_prs=max_prs)

    return {
        "status": "success",
        "repository_id": f"{owner}/{name}",
        "repository": save_result.get("repository", {}),
        **result,
    }


@error_handler
def fetch_pull_requests(owner: str, name: str, max_prs: Optional[int] = None) -> dict:
    """Fetch pull requests."""
    repository_slug = f"{owner}/{name}"

    # Get existing PR numbers
    existing_prs = store.get_existing_prs_map(owner, name)
    logger.info(f"Found {len(existing_prs)} existing pull requests for {repository_slug}")

    # Count PRs that already have events saved
    existing_prs_with_events = 0
    for pr_number in existing_prs:
        if store.has_pr_events(owner, name, pr_number):
            existing_prs_with_events += 1

    logger.info(f"Found {existing_prs_with_events} existing pull requests with events for {repository_slug}")

    # Adjust max_prs for new PRs to fetch based on what we already have
    remaining_prs_to_fetch = None
    if max_prs is not None:
        remaining_prs_to_fetch = max(0, max_prs - existing_prs_with_events)
        logger.info(f"Will fetch up to {remaining_prs_to_fetch} new pull requests to reach the limit of {max_prs}")

        # If we already have enough PRs with events, no need to fetch more
        if remaining_prs_to_fetch == 0:
            logger.info(
                f"Already have {existing_prs_with_events} PRs with events, "
                f"which meets or exceeds the requested {max_prs}"
            )
            return {
                "status": "success",
                "prs_processed": 0,
                "new_prs": 0,
                "message": f"No new PRs needed, already have {existing_prs_with_events} PRs with events",
            }

    # Get merged pull requests from GitHub API using GraphQL
    pull_requests_data = get_pull_requests(owner, name, max_prs=remaining_prs_to_fetch)
    logger.info(f"Fetched {len(pull_requests_data)} pull requests from GitHub API for {repository_slug}")

    # Filter out PRs that we already have
    new_pull_requests = [pr for pr in pull_requests_data if pr["number"] not in existing_prs]
    logger.info(f"Found {len(new_pull_requests)} new pull requests for {repository_slug}")

    # Save new pull requests if we have any
    result = {"status": "success", "prs_processed": 0, "new_prs": 0}
    if new_pull_requests:
        # Transform the PRs to the format expected by the store module
        transformed_prs = [
            {
                "repository_slug": repository_slug,
                "pr_number": pr["number"],
                "title": pr["title"],
                "url": pr["url"],
                "author_login": pr["author"]["login"] if pr["author"] else None,
                "created_at": pr["createdAt"],
                "merged_at": pr["mergedAt"],
                "additions": pr["additions"],
                "deletions": pr["deletions"],
                "files_changed": pr["changedFiles"],
            }
            for pr in new_pull_requests
        ]

        save_result = store.save_pull_requests(owner, name, transformed_prs)
        result["prs_processed"] = save_result.get("prs_processed", 0)
        result["new_prs"] = len(new_pull_requests)

        # Process events for new PRs
        for pr in new_pull_requests:
            fetch_pull_request_events(owner, name, pr["number"])

    # Also check if we need to update events for existing PRs that don't have events yet
    missing_events_prs = [
        pr_number for pr_number in existing_prs.keys() if not store.has_pr_events(owner, name, pr_number)
    ]

    if missing_events_prs:
        logger.info(f"Fetching events for {len(missing_events_prs)} existing pull requests that are missing events")
        for pr_number in missing_events_prs:
            fetch_pull_request_events(owner, name, pr_number)

    # Consolidate all events into a single file
    store.consolidate_all_events(owner, name)

    return result


@error_handler
def fetch_pull_request_events(owner: str, name: str, pr_number: int) -> dict:
    """Fetch pull request events."""
    # Check if events already exist for this PR
    if store.has_pr_events(owner, name, pr_number):
        logger.info(f"Events for PR #{pr_number} already fetched, skipping")
        return {"status": "skipped", "events_processed": 0}

    # Fetch timeline events using GraphQL
    events_data = get_pull_request_events(owner, name, pr_number)

    if not events_data:
        logger.warning(f"No timeline events found for PR #{pr_number}")
        return {"status": "empty", "events_processed": 0}

    # Save events using store module
    return store.save_pr_events(owner, name, pr_number, events_data)
