import logging
import os

import pandas as pd


def load(org: str, repo: str) -> pd.DataFrame:
    """
    Load all events data for a given org/repo into a pandas dataframe

    Args:
        org: GitHub organization name
        repo: GitHub repository name

    Returns:
        DataFrame containing all events data
    """
    data_path = f"./data/{org}/{repo}/all_events.csv"

    if not os.path.exists(data_path):
        logging.warning(f"Data file not found: {data_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(data_path)

        # Log the shape
        logging.info(f"Loaded dataframe with shape: {df.shape}")

        return df
    except Exception as e:
        logging.error(f"Error reading file {data_path}: {e}")
        return pd.DataFrame()
