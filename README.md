# thumbnail_manager
A package to generate and manage thumbnails for images.
### Features:
- Generates thumbnail for an image url
- Supports thumbnail size customization
- Supports caching of thumbnails

### Installation:
```bash
git clone https://github.com/shadowfaxproject/thumbnail_manager.git
cd thumbnail_manager
pip install -r requirements.txt

# Add thumbnail_manager to your PYTHONPATH to make it accessible
export PYTHONPATH=$PYTHONPATH:/path/to/thumbnail_manager
```

### Usage:
```python
import os
from thumbnail_manager import ThumbnailManager

image_url = 'https://picsum.photos/600/200'
cache_dir = '/path/to/cache_dir'
tm = ThumbnailManager(cache_dir=cache_dir, thumbnail_size=(100, 100))
thumbnail_file = tm.generate_thumbnail(image_url=image_url)
thumbnail_file_path = os.path.join(cache_dir, thumbnail_file)
print(os.path.exists(thumbnail_file_path))
```
