import logging
import os
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GitHub API base URL
BASE_URL = "https://api.github.com"


def get_api_token() -> Optional[str]:
    """Get GitHub API token from environment variable."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.warning("GITHUB_TOKEN environment variable not set. API rate limits may apply.")
    return token


def get(
    path: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict:
    """
    Make a GET request to GitHub API.

    Args:
        path: The API endpoint path (without the base URL)
        params: Optional query parameters
        headers: Optional additional headers

    Returns:
        The JSON response as a dictionary
    """
    url = f"{BASE_URL}/{path.lstrip('/')}"

    # Initialize headers if None
    if headers is None:
        headers = {}

    # Use GitHub token if available
    token = get_api_token()
    if token:
        headers["Authorization"] = f"token {token}"

    # Make the request
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()

    return response.json()
