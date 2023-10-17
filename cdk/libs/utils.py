# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""This module contains utility functions used for cdk stacks.
"""
import requests


def download_crowd_2d_skeleton():
    """
    Downloads the 'crowd-2d-skeleton.js' asset from the latest release of the crowd 2d skeleton component on GitHub.

    This function uses the GitHub API to fetch the latest release information, retrieves the download URL
    for the 'crowd-2d-skeleton.js' asset, and downloads it to a specified local file path.

    Returns:
        None: The function saves the asset to the local file path.

    Raises:
        Exception: If there is an issue with the HTTP requests or if the asset is not found in the release.
    """
    # Using the GitHub API we can get the latest release of the crowd 2d skeleton component
    url = "https://api.github.com/repos/aws-samples/sagemaker-ground-truth-crowd-2d-skeleton-component/releases/latest"

    response = requests.get(url)
    asset_url = None

    for asset in response.json().get("assets", []):
        if asset.get("name") == "crowd-2d-skeleton.js":
            asset_url = asset.get("browser_download_url")
            break

    if asset_url:
        response = requests.get(asset_url)

        # Specify the local file path where you want to save the downloaded file
        local_file_path = "cdk/ground_truth_templates/crowd-2d-skeleton.js"

        # Open the local file in binary write mode and write the content
        with open(local_file_path, "wb") as file:
            file.write(response.content)
    else:
        raise Exception(
            "The 'crowd-2d-skeleton.js' asset was not found in the release."
        )
