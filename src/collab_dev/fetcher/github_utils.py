import logging
import re
from typing import Any, Dict, List

import requests

from .api_client import get_api_token

logger = logging.getLogger(__name__)

GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"


def get_github_headers() -> Dict:
    """Get GitHub API headers with authentication token"""
    token = get_api_token()

    if not token:
        logger.error("No GitHub token available")
        raise Exception("No GitHub token available")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    return headers


def github_request(method: str, url: str, **kwargs) -> Dict:
    """Make a GitHub API request"""
    # Get headers with a token
    headers = get_github_headers()
    kwargs_headers = kwargs.get("headers", {})

    # Merge headers
    full_headers = {**kwargs_headers, **headers}
    kwargs["headers"] = full_headers

    # Make the request
    response = requests.request(method, url, **kwargs)

    # Raise exceptions for error status codes
    response.raise_for_status()

    return response.json()


def github_graphql_request(query: str, variables: Dict, timeout=30) -> Dict:
    """Make a GitHub GraphQL API request"""
    url = "https://api.github.com/graphql"
    headers = get_github_headers()

    # Create the request payload
    payload = {"query": query, "variables": variables}

    # Make the request
    response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    # Check for HTTP errors
    response.raise_for_status()

    # Get the response data
    result = response.json()

    # Check for GraphQL-specific errors
    if "errors" in result:
        logger.error(f"GraphQL errors: {result['errors']}")
        raise Exception(f"GraphQL errors: {result['errors']}")

    return result


def make_graphql_request(query: str, variables: dict, oauth_token: str = None) -> dict:
    """Make a GraphQL request"""
    try:
        token = oauth_token or get_api_token()

        if not token:
            raise Exception("No GitHub token available")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        response = requests.post(GITHUB_GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})

        if response.status_code == 200:
            result = response.json()

            if "errors" in result:
                logger.error(f"GraphQL Errors: {result['errors']}")
                raise Exception(f"GraphQL errors: {result['errors']}")

            return result
        else:
            logger.error(f"GraphQL request failed with status {response.status_code}")
            raise Exception(f"GraphQL request failed: {response.text}")

    except Exception as e:
        logger.error(f"Error making GraphQL request: {str(e)}")
        raise


def get_user_association(owner: str, repo: str, username: str, oauth_token: str = None) -> str:
    """
    Get a user's association with a repository
    Returns: Role as string ('owner', 'member', 'collaborator', or 'none')
    """
    if not username:
        return "none"

    token = oauth_token or get_api_token()

    if not token:
        return "none"

    query = """
    query($owner: String!, $repo: String!) {
      repository(owner: $owner, name: $repo) {
        viewerPermission
        owner {
          login
        }
      }
      viewer {
        login
      }
    }
    """

    try:
        result = make_graphql_request(query, {"owner": owner, "repo": repo}, oauth_token=token)
        logger.info(f"GitHub API response for user association: {result}")

        data = result.get("data", {})
        viewer_login = data.get("viewer", {}).get("login")
        logger.info(f"Viewer login: {viewer_login}, checking against username: {username}")

        # If we're not checking the authenticated user, return none
        if viewer_login != username:
            logger.info(f"Username mismatch: viewer {viewer_login} != requested {username}")
            return "none"

        repository = data.get("repository", {})
        logger.info(f"Repository data: {repository}")

        # Check if user is the repository owner
        repo_owner = repository.get("owner", {}).get("login")
        logger.info(f"Repository owner: {repo_owner}")
        if repo_owner == username:
            logger.info(f"User {username} is the repository owner")
            return "owner"

        # Map GitHub permissions to our roles
        permission = repository.get("viewerPermission")
        logger.info(f"User permission level: {permission}")
        if permission == "ADMIN":
            logger.info(f"User {username} has ADMIN permission -> collaborator role")
            return "collaborator"  # Admin gets collaborator role
        elif permission == "MAINTAIN":
            logger.info(f"User {username} has MAINTAIN permission -> member role")
            return "member"  # Maintain gets member role
        elif permission == "WRITE":
            logger.info(f"User {username} has WRITE permission -> collaborator role")
            return "collaborator"  # Write access gets collaborator role

        logger.info(f"User {username} has insufficient permissions: {permission}")
        return "none"

    except Exception as e:
        logger.error(f"Error checking user association for {username}: {str(e)}")
        return "none"


def is_bot_actor(actor_name: str) -> bool:
    """Check if an actor is a bot based on name patterns"""
    if not actor_name:
        return False

    actor_name = actor_name.lower()

    # Common bot suffixes and patterns
    bot_patterns = [r"bot$", r"\[bot\]$", r"app$", r"-bot$", r"bot-"]

    # Known bot names
    known_bots = {
        "dependabot",
        "renovate",
        "github-actions",
        "semantic-release",
        "codecov",
        "sonarcloud",
        "snyk-bot",
        "imgbot",
        "deepsource-autofix",
        "stale",
        "allcontributors",
        "prettier",
        "vercel",
        "mergify",
        "probot",
        "goreleaserbot",
        "greenkeeper",
        "lgtm-com",
        "circleci",
        "travis-ci",
        "gitter-badger",
        "whitesource-bolt-for-github",
        "dependabot-preview",
        "semantic-release-bot",
    }

    # Check if actor name contains any known bot name
    for bot_name in known_bots:
        if bot_name in actor_name:
            return True

    # Check if actor name matches any bot pattern
    for pattern in bot_patterns:
        if re.search(pattern, actor_name):
            return True

    return False


def process_timeline_events(pr_data: Dict, repo_url: str, repo_name: str) -> list:
    """Convert GraphQL timeline data into database-compatible format"""
    owner, repo = repo_name.split("/")

    pr_author = pr_data["author"]["login"] if pr_data["author"] else None
    author_association = pr_data.get("authorAssociation", "")
    is_author_core = author_association in ["OWNER", "MEMBER", "COLLABORATOR"]

    events = []

    # Add PR creation event
    events.append(
        {
            "time": pr_data["createdAt"],
            "pr_number": pr_data["number"],
            "repository_slug": repo_name,
            "pr_title": pr_data["title"],
            "pr_url": pr_data["url"],
            "event_type": "pr_created",
            "actor": pr_author,
            "target_user": None,
            "files_changed": pr_data["changedFiles"],
            "lines_added": pr_data["additions"],
            "lines_deleted": pr_data["deletions"],
            "is_core_team": is_author_core,
            "source_branch": pr_data["headRefName"],
            "target_branch": pr_data["baseRefName"],
            "was_draft": pr_data["isDraft"],
            "is_bot": is_bot_actor(pr_author),
        }
    )

    # Process timeline items
    logger.info(f"Processing {len(pr_data['timelineItems']['nodes'])} timeline events for PR #{pr_data['number']}")

    for item in pr_data["timelineItems"]["nodes"]:
        if "__typename" not in item:
            continue

        base_event = {
            "pr_number": pr_data["number"],
            "pr_title": pr_data["title"],
            "repository_slug": repo_name,
            "pr_url": pr_data["url"],
            "files_changed": pr_data["changedFiles"],
            "lines_added": pr_data["additions"],
            "lines_deleted": pr_data["deletions"],
            "is_core_team": is_author_core,
            "source_branch": pr_data["headRefName"],
            "target_branch": pr_data["baseRefName"],
            "was_draft": pr_data["isDraft"],
        }

        if item["__typename"] == "PullRequestCommit":
            actor = item["commit"]["author"]["user"]["login"] if item["commit"]["author"]["user"] else None
            events.append(
                {
                    **base_event,
                    "time": item["commit"]["committedDate"],
                    "event_type": "commit_pushed",
                    "actor": actor,
                    "target_user": None,
                    "is_bot": is_bot_actor(actor),
                }
            )

        elif item["__typename"] == "ReviewRequestedEvent":
            actor = item["actor"]["login"] if item["actor"] else None
            target_user = item["requestedReviewer"]["login"] if item["requestedReviewer"] else None
            events.append(
                {
                    **base_event,
                    "time": item["createdAt"],
                    "event_type": "review_requested",
                    "actor": actor,
                    "target_user": target_user,
                    "is_bot": is_bot_actor(actor),
                }
            )

        elif item["__typename"] == "PullRequestReview":
            actor = item["author"]["login"] if item["author"] else None
            events.append(
                {
                    **base_event,
                    "time": item["createdAt"],
                    "event_type": f"review_{item['state'].lower()}",
                    "actor": actor,
                    "target_user": None,
                    "is_bot": is_bot_actor(actor),
                }
            )

        elif item["__typename"] == "MergedEvent":
            actor = item["actor"]["login"] if item["actor"] else None
            events.append(
                {
                    **base_event,
                    "time": item["createdAt"],
                    "event_type": "pr_merged",
                    "actor": actor,
                    "target_user": None,
                    "is_bot": is_bot_actor(actor),
                }
            )

        elif item["__typename"] == "IssueComment":
            actor = item["author"]["login"] if item["author"] else None
            events.append(
                {
                    **base_event,
                    "time": item["createdAt"],
                    "event_type": "comment_added",
                    "actor": actor,
                    "target_user": None,
                    "is_bot": is_bot_actor(actor),
                }
            )

    logger.info(f"Processed {len(events)} total events for PR #{pr_data['number']}")
    return events


PULL_REQUESTS_PER_PAGE = 100


def github_graphql_get_merged_pull_requests(owner: str, name: str) -> List[Dict]:
    """Get merged pull requests using GraphQL API"""
    query = (
        """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        pullRequests(first: %d, states: [MERGED], orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            number
            title
            url
            createdAt
            mergedAt
            changedFiles
            additions
            deletions
            author {
              login
            }
          }
        }
      }
    }
    """
        % PULL_REQUESTS_PER_PAGE
    )

    try:
        result = github_graphql_request(query, {"owner": owner, "name": name})
        if result.get("data") and result["data"].get("repository"):
            return result["data"]["repository"]["pullRequests"]["nodes"]
        return []
    except Exception as e:
        logger.error(f"Error fetching pull requests: {str(e)}")
        raise


def github_graphql_get_pull_request_events(owner: str, name: str, pr_number: int) -> Dict[str, Any]:
    """Get PR timeline data using GraphQL API"""
    query = """
    query($owner: String!, $name: String!, $pr_number: Int!) {
      repository(owner: $owner, name: $name) {
        pullRequest(number: $pr_number) {
          number
          title
          url
          createdAt
          mergedAt
          changedFiles
          additions
          deletions
          headRefName
          baseRefName
          isDraft
          author {
            login
          }
          authorAssociation
          timelineItems(first: 100) {
            pageInfo {
              hasNextPage
              endCursor
            }
            nodes {
              __typename
              ... on PullRequestCommit {
                commit {
                  committedDate
                  author {
                    user {
                      login
                    }
                  }
                }
              }
              ... on ReviewRequestedEvent {
                createdAt
                actor {
                  login
                }
                requestedReviewer {
                  ... on User {
                    login
                  }
                }
              }
              ... on PullRequestReview {
                createdAt
                author {
                  login
                }
                state
              }
              ... on MergedEvent {
                createdAt
                actor {
                  login
                }
              }
              ... on IssueComment {
                createdAt
                author {
                  login
                }
              }
            }
          }
        }
      }
    }
    """

    try:
        result = github_graphql_request(query, {"owner": owner, "name": name, "pr_number": pr_number})
        if result.get("data") and result["data"].get("repository"):
            return result["data"]["repository"]["pullRequest"]
        return None
    except Exception as e:
        logger.error(f"Error fetching PR timeline: {str(e)}")
        raise


def github_graphql_get_repository(owner: str, name: str) -> Dict:
    """Get repository data using GraphQL"""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        name
        description
        url
        owner {
          avatarUrl
          ... on Organization {
            avatarUrl
          }
        }
      }
    }
    """

    try:
        result = github_graphql_request(query, {"owner": owner, "name": name})

        if result.get("data") and result["data"].get("repository"):
            repo = result["data"]["repository"]
            # Return a flat dictionary with string values
            return {
                "url": f"https://github.com/{owner}/{name}",
                "name": repo["name"],
                "organization": owner,
                "description": repo["description"],
                "logo_url": repo["owner"]["avatarUrl"],
                "category": "Newly Added",
                "repository_slug": f"{owner}/{name}",
                "status": "updating",
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching repository data: {str(e)}")
        raise
