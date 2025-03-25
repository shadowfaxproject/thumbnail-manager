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
ORIGINALS_DIR = 'originals'  # Directory-name to save the original images
THUMBNAILS_DIR = 'thumbnails'  # Directory-name to save the generated thumbnails


class ThumbnailManager:
    def __init__(self, thumbnail_size: Optional[Tuple[int, int]] = DEFAULT_SIZE, cache_dir: Optional[str] = None,
                 save_original: bool = False, fill_color: str = FILL_COLOR):
        """
        Initialize the ThumbnailManager object with the given thumbnail size and cache directory.
        :param thumbnail_size: size of the thumbnail in pixels :param cache_dir: directory to save the generated
        thumbnails
        :param save_original: option to save original image in the cache directory. If True, the original image is
        saved under /original/ directory.
        :param fill_color: color to fill the background with the thumbnail
        """
        self.thumbnail_size = thumbnail_size
        self.save_original = save_original
        self.fill_color = fill_color

        self.thumbnails_dir = os.path.join(cache_dir, THUMBNAILS_DIR) if cache_dir else None
        self.originals_dir = os.path.join(cache_dir, ORIGINALS_DIR) if cache_dir else None
        self.file_names = {}

        if self.thumbnails_dir:
            try:
                os.makedirs(self.thumbnails_dir, exist_ok=True)
                if self.save_original:
                    os.makedirs(self.originals_dir, exist_ok=True)
            except Exception as e:
                raise Exception(f"ThumbnailManager: Error while creating cache directory: {e}. Unable to create cache "
                                f"directory for saving thumbnails.")

            # load all file-names-hashids in hashmap
            for filename in os.listdir(self.thumbnails_dir):
                try:
                    (hash_id, size, ext) = filename.split('.')
                    self.file_names[hash_id] = filename
                except ValueError as e:
                    logging.error(f"ThumbnailManager: Error while reading thumbnail file: {e}. Unable to read the "
                                  f"thumbnail file: {filename}")
            logging.info(f"ThumbnailManager: Cache directory: {self.thumbnails_dir}, "
                         f"Originals directory: {self.originals_dir}")

    def generate_thumbnail(self, image_url: str) -> Optional[str]:
        """
        Generate thumbnail for the given image URL. If cache_dir is provided, then the generated thumbnail is saved
        in the cache directory for future retrieval.
        :param image_url:
        :return: absolute path of the generated thumbnail file
        """
        headers = {'User-Agent': USER_AGENT}

        # Check if the thumbnail already exists in the cache directory
        path = self.has_thumbnail(image_url)
        if path:
            return path

        hash_id = hashlib.md5(image_url.encode("utf-8")).hexdigest()
        size = 'x'.join(map(str, self.thumbnail_size))
        # Fetch image from image_url
        try:
            img_request = urllib.request.Request(image_url, None, headers)
            img_response = urllib.request.urlopen(img_request)
        except urllib.error.HTTPError as e:
            logging.error(f"HTTP Error: {e.code}. Unable to download image from the URL: {image_url}")
            return None

        # Save the image data to a temporary file
        data = img_response.read()
        image_file = os.path.join(self.originals_dir, hash_id) if self.save_original else (
            os.path.join(TMP_DIR, 'tmp_' + hash_id))
        try:
            with open(image_file, 'wb') as f:
                f.write(data)
                f.close()
        except FileExistsError as e:
            logging.error(f"File exists error: {e}. Unable to write image data to a file {image_file}.")
            return None

        # Open the saved image file
        try:
            image = Image.open(image_file)
        except FileNotFoundError as e:
            logging.error(f"File not found error: {e}"
                          f"Unable to open the temporary image file.")
            return None
        except Exception as e:
            logging.error(f"Error while opening the image file: {e}. Unable to open the image file.")
            return None

        # Generate thumbnail
        try:
            image_format = image.format.lower()
            thumbnail_file_name = '.'.join([hash_id, size, image_format])

            if not self.thumbnails_dir:
                # If cache directory is not provided then return the thumbnail saved as a temporary file in the TMP_DIR
                thumbnail_file = os.path.join(TMP_DIR, thumbnail_file_name)
                ImageOps.pad(image, self.thumbnail_size, color=self.fill_color).save(fp=thumbnail_file)
                return thumbnail_file

            ImageOps.pad(image, self.thumbnail_size, color=self.fill_color).save(
                    fp=os.path.join(self.thumbnails_dir, thumbnail_file_name))
            # Delete if the original image is not required to be saved
            if not self.save_original:
                os.remove(image_file)
            else:
                # Rename the original image file to the hash_id.format
                os.rename(image_file, '.'.join([image_file, image_format]))

            return os.path.join(self.thumbnails_dir, thumbnail_file_name)
        except Exception as e:
            logging.error(f"Error while generating thumbnail: {e}. Unable to generate thumbnail for the image.")
            return None

    def get_original_image_file(self, image_url: str) -> Optional[str]:
        """
        Get the original image file saved in the cache directory for the given image URL.
        :param image_url:
        :return: absolute path of the original image file
        """
        hash_id = hashlib.md5(image_url.encode("utf-8")).hexdigest()
        filename = self.file_names[hash_id]
        (hash_id, size, ext) = filename.split('.')
        orig_filename = os.path.join(self.originals_dir, '.'.join([hash_id, ext]))
        if os.path.exists(orig_filename):
            return orig_filename
        return None

    def remove_thumbnail(self, image_url: str, keep_orig: Optional[bool] = False) -> None:
        """
        Remove the thumbnail for the given image URL from the cache directory.
        :param keep_orig: whether to keep the original image file. If True, the original image file is not removed.
        Default is False.
        :param image_url:
        """
        hash_id = hashlib.md5(image_url.encode("utf-8")).hexdigest()
        if hash_id in self.file_names:
            try:
                thumbnail_file = os.path.join(self.thumbnails_dir, self.file_names[hash_id])
                logging.debug(f"Removing thumbnail: {thumbnail_file}")
                # os.remove(thumbnail_file)
                if not keep_orig:
                    (hash_id, size, ext) = self.file_names[hash_id].split('.')
                    orig_file = os.path.join(self.originals_dir, '.'.join([hash_id, ext]))
                    logging.debug(f"Removing original image: {orig_file}")
                    # os.remove(orig_file)
                del self.file_names[hash_id]
            except FileNotFoundError as e:
                logging.warning(f"File not found error: {e}. Unable to remove the thumbnail file.")
            except Exception as e:
                logging.error(f"Error while removing thumbnail: {e}. Unable to remove the thumbnail file.")

    def has_thumbnail(self, image_url: str) -> str | None:
        """
        Check if the thumbnail exists for the given image URL in the cache directory.
        :param image_url:
        :return: True if the thumbnail exists, False otherwise
        """
        hash_id = hashlib.md5(image_url.encode("utf-8")).hexdigest()
        if hash_id in self.file_names:
            logging.debug(f"Thumbnail already exists for the image: {image_url}: {self.file_names[hash_id]}")
            return os.path.join(self.thumbnails_dir, self.file_names[hash_id])
        return None
