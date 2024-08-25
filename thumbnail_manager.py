"""
Generate thumbnail for a given image-url and returns the thumbnail file.
Supports caching of the generated thumbnails.
"""
import hashlib
import logging
import urllib
from urllib import request, error
from typing import Optional, Tuple
from PIL import Image, ImageOps
import os

USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
DEFAULT_SIZE = (200, 200)  # Default size of the thumbnail in pixels
FILL_COLOR = "#34495e"
TMP_DIR = '/tmp/'


class ThumbnailManager:
    def __init__(self, thumbnail_size: Optional[Tuple[int, int]] = DEFAULT_SIZE, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir
        self.thumbnail_size = thumbnail_size

    def generate_thumbnail(self, image_url: str) -> Optional[str]:
        """
        Generate thumbnail for the given image URL. If cache_dir is provided, then the generated thumbnail is saved
        in the cache directory for future retrieval.
        :param image_url:
        :return: absolute path of the generated thumbnail file
        """
        headers = {'User-Agent': USER_AGENT}

        hash_id = hashlib.md5(image_url.encode("utf-8")).hexdigest()
        size = 'x'.join(map(str, self.thumbnail_size))
        if self.cache_dir:
            # Check if the thumbnail already exists in the cache directory
            matching_files = [f for f in os.listdir(self.cache_dir) if f.startswith('.'.join([hash_id, size]))]
            if matching_files:
                logging.debug(f"Thumbnail already exists for the image: {image_url}: {matching_files[0]}")
                return os.path.join(self.cache_dir, matching_files[0])

            # Check if the thumbnail already exists in the cache directory regardless of the size
            matching_files = [f for f in os.listdir(self.cache_dir) if f.startswith(hash_id)]
            if matching_files:
                logging.debug(f"Thumbnail already exists for the image: {image_url}: {matching_files[0]}")
                return os.path.join(self.cache_dir, matching_files[0])

        # Fetch image from image_url
        try:
            img_request = urllib.request.Request(image_url, None, headers)
            img_response = urllib.request.urlopen(img_request)
        except urllib.error.HTTPError as e:
            logging.error(f"HTTP Error: {e.code}. Unable to download image from the URL: {image_url}")
            return None

        # Save the image data to a temporary file
        try:
            data = img_response.read()
            tmp_file_name = 'tmp_' + hash_id
            tmp_file = os.path.join(TMP_DIR, tmp_file_name)
            with open(tmp_file, 'wb') as f:
                f.write(data)
            f.close()
        except FileExistsError as e:
            logging.error(f"File exists error: {e}. Unable to write image data to a temporary file.")
            return None

        # Open the temporary image file
        try:
            image = Image.open(tmp_file)
        except FileNotFoundError as e:
            logging.error(f"File not found error: {e}"
                          f"Unable to open the temporary image file.")
            return None

        # Generate thumbnail
        try:
            thumbnail_file_name = '.'.join([hash_id, size, image.format.lower()])

            if not self.cache_dir:
                # If cache directory is not provided then return the thumbnail saved as a temporary file in the TMP_DIR
                thumbnail_file = os.path.join(TMP_DIR, thumbnail_file_name)
                ImageOps.pad(image, self.thumbnail_size, color=FILL_COLOR).save(fp=thumbnail_file)
                return thumbnail_file

            ImageOps.pad(image, self.thumbnail_size, color=FILL_COLOR).save(fp=os.path.join(self.cache_dir,
                                                                                            thumbnail_file_name))
            # Delete the temporary file
            os.remove(tmp_file)
            return os.path.join(self.cache_dir, thumbnail_file_name)
        except Exception as e:
            logging.error(f"Error while generating thumbnail: {e}. Unable to generate thumbnail for the image.")
            return None
