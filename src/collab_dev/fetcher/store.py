import csv
import logging
import os
import sys
from typing import Dict, List

# Configure logging
logger = logging.getLogger(__name__)

# Get root directory - set to './data' by default
DATA_DIR = "./data"

# Check if data directory exists
if not os.path.exists(DATA_DIR):
    logger.error(f"Data directory {DATA_DIR} does not exist. Please create it first.")
    sys.exit(1)


def ensure_directory(path: str) -> str:
    """Ensure the directory exists, creating it if necessary."""
    os.makedirs(path, exist_ok=True)
    return path


def get_repo_dir(owner: str, name: str) -> str:
    """Get the repository directory path."""
    return ensure_directory(os.path.join(DATA_DIR, owner, name))


def get_pr_dir(owner: str, name: str, pr_number: int) -> str:
    """Get the pull request directory path."""
    repo_dir = get_repo_dir(owner, name)
    return ensure_directory(os.path.join(repo_dir, f"pr_{pr_number}"))


def write_csv(filepath: str, data: List[Dict], headers: List[str]) -> None:
    """Write data to a CSV file."""
    mode = "w"
    file_exists = os.path.exists(filepath)

    with open(filepath, mode, newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        if not file_exists or mode == "w":
            writer.writeheader()

        for row in data:
            # Filter the row to only include fields in headers
            filtered_row = {k: v for k, v in row.items() if k in headers}
            writer.writerow(filtered_row)

    logger.info(f"Data written to {filepath}")


def save_repository_info(owner: str, name: str, repo_data: Dict, category=None) -> Dict:
    """Save repository information to CSV."""
    repo_dir = get_repo_dir(owner, name)

    # Write repository info to CSV
    write_csv(
        os.path.join(repo_dir, "repository.csv"),
        [repo_data],
        list(repo_data.keys()),
    )

    return {
        "status": "success",
        "repository_dir": repo_dir,
        "repository": repo_data,
    }


def save_pull_requests(owner: str, name: str, pull_requests_data: List[Dict]) -> Dict:
    """Save pull requests to CSV."""
    repo_dir = get_repo_dir(owner, name)

    write_csv(
        os.path.join(repo_dir, "pull_requests.csv"),
        pull_requests_data,
        list(pull_requests_data[0].keys()),
    )

    return {
        "status": "success",
        "prs_processed": len(pull_requests_data),
    }


def save_pr_events(owner: str, name: str, pr_number: int, events_data: List[Dict]) -> Dict:
    """Save pull request events to CSV."""
    # Create directory for PR events
    pr_dir = get_pr_dir(owner, name, pr_number)

    if not events_data:
        logger.info(f"No timeline events found for PR #{pr_number}")
        return {"status": "success", "events_processed": 0}

    # Get PR data to extract title, URL, etc.
    repo_dir = get_repo_dir(owner, name)
    pr_csv_path = os.path.join(repo_dir, "pull_requests.csv")
    if os.path.exists(pr_csv_path):
        with open(pr_csv_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for pr in reader:
                if int(pr["pr_number"]) == pr_number:
                    break

    # Write to CSV
    write_csv(
        os.path.join(pr_dir, "events.csv"),
        events_data,
        list(events_data[0].keys()),
    )

    return {
        "status": "success",
        "events_processed": len(events_data),
    }


def get_pr_numbers_from_csv(owner: str, name: str) -> List[int]:
    """Read PR numbers from pull_requests.csv."""
    repo_dir = get_repo_dir(owner, name)
    pr_csv_path = os.path.join(repo_dir, "pull_requests.csv")
    pr_numbers = []

    if os.path.exists(pr_csv_path):
        with open(pr_csv_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for pr in reader:
                pr_numbers.append(int(pr["pr_number"]))

    return pr_numbers


def get_existing_prs_map(owner: str, name: str) -> Dict[int, Dict]:
    """
    Get a dictionary of existing PRs from pull_requests.csv.

    Args:
        owner: GitHub repository owner
        name: GitHub repository name

    Returns:
        Dictionary mapping PR numbers to PR data
    """
    repo_dir = get_repo_dir(owner, name)
    pr_csv_path = os.path.join(repo_dir, "pull_requests.csv")
    pr_map = {}

    if os.path.exists(pr_csv_path):
        with open(pr_csv_path, "r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for pr in reader:
                pr_map[int(pr["pr_number"])] = pr

    return pr_map


def has_pr_events(owner: str, name: str, pr_number: int) -> bool:
    """
    Check if events for a specific PR have already been fetched.

    Args:
        owner: GitHub repository owner
        name: GitHub repository name
        pr_number: Pull request number

    Returns:
        True if events exist, False otherwise
    """
    pr_dir = get_pr_dir(owner, name, pr_number)
    events_csv_path = os.path.join(pr_dir, "events.csv")

    return os.path.exists(events_csv_path) and os.path.getsize(events_csv_path) > 0


def consolidate_all_events(owner: str, name: str) -> Dict:
    """
    Consolidate all PR events into a single all_events.csv file in the repo directory.

    Args:
        owner: GitHub repository owner
        name: GitHub repository name

    Returns:
        Dict with status and count of events consolidated
    """
    repo_dir = get_repo_dir(owner, name)
    pr_numbers = get_pr_numbers_from_csv(owner, name)

    all_events = []

    # Collect events from each PR
    for pr_number in pr_numbers:
        pr_dir = get_pr_dir(owner, name, pr_number)
        events_csv_path = os.path.join(pr_dir, "events.csv")

        if os.path.exists(events_csv_path) and os.path.getsize(events_csv_path) > 0:
            with open(events_csv_path, "r", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                all_events.extend(list(reader))

    # Write consolidated events to all_events.csv
    if all_events:
        all_events_path = os.path.join(repo_dir, "all_events.csv")
        write_csv(all_events_path, all_events, list(all_events[0].keys()))
        logger.info(f"Consolidated {len(all_events)} events into {all_events_path}")

    return {
        "status": "success",
        "events_consolidated": len(all_events),
    }


def get_all_repositories() -> List[str]:
    """
    Get a list of all repositories stored in the data directory.

    Returns:
        List of repositories in the format "owner/name"
    """
    repositories = []

    # Check if data directory exists
    if not os.path.exists(DATA_DIR):
        logger.warning(f"Data directory {DATA_DIR} does not exist.")
        return repositories

    # Walk through the data directory structure
    for owner in os.listdir(DATA_DIR):
        owner_path = os.path.join(DATA_DIR, owner)
        if os.path.isdir(owner_path):
            for repo in os.listdir(owner_path):
                repo_path = os.path.join(owner_path, repo)
                # Check if it's a directory and contains repository.csv
                if os.path.isdir(repo_path) and os.path.exists(os.path.join(repo_path, "repository.csv")):
                    repositories.append(f"{owner}/{repo}")

    return repositories
