"""
Generate thumbnail for a given image url and returns the thumbnail file.
"""
import hashlib
import logging
import urllib
from urllib import request, error
from typing import Optional, Tuple
from PIL import Image, ImageOps
import os

USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
DEFAULT_SIZE = (200, 200)
FILL_COLOR = "#34495e"


class ThumbnailManager:
    def __init__(self, thumbnail_size: Optional[Tuple[int, int]] = DEFAULT_SIZE, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir
        self.thumbnail_size = thumbnail_size

    def generate_thumbnail(self, image_url: str) -> str:
        headers = {'User-Agent': USER_AGENT}

        hash_id = hashlib.md5(image_url.encode("utf-8")).hexdigest()

        # List files that match the hash_id regardless of the extension in the cache directory
        matching_files = [f for f in os.listdir(self.cache_dir) if f.startswith(hash_id)]
        if matching_files:
            logging.debug(f"Thumbnail already exists for the image: {image_url}: {matching_files[0]}")
            return matching_files[0]

        try:
            img_request = urllib.request.Request(image_url, None, headers)
            img_response = urllib.request.urlopen(img_request)
        except urllib.error.HTTPError as e:
            logging.error(f"HTTP Error: {e.code}"
                          f"Unable to download image from the URL: {image_url}")
            return None

        try:
            data = img_response.read()
            tmp_file = '/tmp/tmp_' + hash_id
            with open(tmp_file, 'wb') as f:
                f.write(data)
            f.close()
        except FileExistsError as e:
            logging.error(f"File exists error: {e}"
                          f"Unable to write image data to a temporary file.")
            return None

        try:
            image = Image.open(tmp_file)
        except FileNotFoundError as e:
            logging.error(f"File not found error: {e}"
                          f"Unable to open the temporary image file.")
            return None

        try:
            thumbnail_file_name = hash_id + '.' + image.format.lower()
            ImageOps.pad(image, self.thumbnail_size, color=FILL_COLOR).save(fp=os.path.join(self.cache_dir,
                                                                                            thumbnail_file_name))

            # Delete the temporary file
            os.remove(tmp_file)
        except Exception as e:
            logging.error(f"Error while generating thumbnail: {e}"
                          f"Unable to generate thumbnail for the image.")
            return None

        return thumbnail_file_name
