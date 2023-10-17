# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""This script downloads the example images used in the example labeling job."""
import csv
import os

import requests


def download_images_from_csv(csv_file: str, image_dir: str) -> None:
    """
    Downloads images from a CSV file containing a column named "OriginalURL"
    and saves them in the specified image directory.

    Args:
        csv_file: Path to the CSV file containing images to download. See
            scripts/image_details.csv for CSV fields and examples.
        image_dir: Directory to save the images.
    """
    # Create the image directory if it doesn't exist
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    # Read the CSV file and download the images
    with open(csv_file, "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            image_url = row["OriginalURL"]
            image_name = image_url.split("/")[-1]
            image_path = os.path.join(image_dir, image_name)

            try:
                response = requests.get(image_url, stream=True)
                response.raise_for_status()

                with open(image_path, "wb") as image_file:
                    for chunk in response.iter_content(chunk_size=8192):
                        image_file.write(chunk)

                print(f"Downloaded image: {image_name}")

            except requests.exceptions.RequestException as e:
                print(f"Error downloading image: {image_name}")
                print(e)


if __name__ == "__main__":
    # Directory to save the images
    image_dir = "scripts/images"
    csv_file = "scripts/image_details.csv"
    download_images_from_csv(csv_file, image_dir)
