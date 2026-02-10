import os
import re
import shutil
import hashlib
import requests
import frontmatter
from pathlib import Path

# ==========================================
# CONFIGURATION
# ==========================================

# Base directory (Project Root), relative to this script
BASE_DIR = Path(__file__).parent.parent.absolute()

# Source Configuration (Obsidian Vault)
SOURCE_CONFIG = {
    # Root path to your Obsidian vault or specific sync folder
    "root": Path("/home/christian/syncthing/Obsidian/Atlas"),
    
    # Subdirectories within the root to scan
    # Key: Valid 'type' in frontmatter or internal identifier
    # Value: Folder name relative to 'root'
    "folders": {
        "movie": "Media Tracker/Movies",
        "tv": "Media Tracker/TVs",
        "season": "Media Tracker/Seasons",
        "videogame": "Media Tracker/Juegos"
    },
    
    # Path to covers folder (if centralized)
    "covers_dir": "Media Tracker/Portadas"
}

# Destination Configuration (Hugo)
DEST_CONFIG = {
    "content_dir": BASE_DIR / "content",
    "static_images_dir": BASE_DIR / "static" / "images",
    "cache_dir": BASE_DIR / "static" / "images_cache",
    
    # Mapping Obsidian types to Hugo content sections
    "section_map": {
        "movie": "movies",
        "tv": "tv",
        "season": "seasons",
        "videogame": "games"
    }
}

# Frontmatter Fields to Clean/Process
# These keys contain wikilinks that need to be cleaned up
FRONTMATTER_LINKS = ["serie", "temporadas", "related"]

# ==========================================
# INITIALIZATION
# ==========================================

# Define full source paths
SOURCE_ROOT = SOURCE_CONFIG["root"]
SOURCE_DIRS = {k: SOURCE_ROOT / v for k, v in SOURCE_CONFIG["folders"].items()}
SOURCE_COVERS_DIR = SOURCE_ROOT / SOURCE_CONFIG["covers_dir"]

# Define full destination paths
COVERS_DIR = DEST_CONFIG["static_images_dir"] / "covers"
BANNERS_DIR = DEST_CONFIG["static_images_dir"] / "banners"

# Ensure directories exist
DEST_CONFIG["cache_dir"].mkdir(parents=True, exist_ok=True)
COVERS_DIR.mkdir(parents=True, exist_ok=True)
BANNERS_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def clean_wikilink(text):
    """
    Parses Obsidian wikilinks:
    [[Name]] -> Name
    [[Path/To/Name|Alias]] -> Alias
    """
    if not isinstance(text, str):
        return text
    
    # Regex to capture content inside [[...]]
    # It handles the pipe | separator for aliases
    match = re.search(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', text)
    if match:
        return match.group(1)
    return text

def convert_wikilinks(text, known_files):
    """
    Converts [[Path/To/Note|Alias]] to [Alias]({{< ref "Note" >}})
    Only if "Note" is in known_files.
    """
    def replacer(match):
        inner = match.group(1)
        alias = inner
        target = inner
        
        if '|' in inner:
            target, alias = inner.split('|', 1)
        
        # Extract filename (removing path)
        filename = target.split('/')[-1]
        if filename.endswith('.md'):
            filename = filename[:-3]
            
        if filename in known_files:
            return f'[{alias}]({{{{< ref "{filename}" >}}}})'
        else:
            # If valid note not found, just return the Alias text
            return alias

    # Negative lookbehind to avoid matching ![[...]] (images)
    return re.sub(r'(?<!\!)\[\[(.*?)\]\]', replacer, text)

def get_image_filename(source_str):
    """
    Generates a unique filename.
    PRIORITY 1: Image ID extracted from URL (TMDB/TVDB) to allow cover updates.
    PRIORITY 2: MD5 Hash of the full string (for local files or rare URLs).
    """
    source_str = str(source_str)
    
    # 1. TMDB Case (Extract unique Image ID)
    # URL ex: https://image.tmdb.org/t/p/original/1CfZCb56vWjq37uXtbKNMevMzwG.jpg
    if "tmdb.org" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-1] # 1CfZCb56vWjq37uXtbKNMevMzwG.jpg
            image_id = filename_with_ext.split('.')[0]    # 1CfZCb56vWjq37uXtbKNMevMzwG
            ext = filename_with_ext.split('.')[1]         # jpg
            return f"tmdb_{image_id}.{ext}"
        except:
            pass # If parse fails, fallback to hash

    # 2. TheTVDB Case (Extract filename)
    # URL ex: https://artworks.thetvdb.com/banners/movies/1234/posters/1234.jpg
    if "thetvdb.com" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-1]
            image_id = filename_with_ext.split('.')[0]
            ext = filename_with_ext.split('.')[1]
            return f"tvdb_{image_id}.{ext}"
        except:
            pass

    # 3. SteamGridDB Case
    if "steamgriddb" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-1]
            image_id = filename_with_ext.split('.')[0]
            ext = filename_with_ext.split('.')[1]
            return f"steamgriddb_{image_id}.{ext}"
        except:
            pass
    
    # 4. Steam Static Case
    if "steamstatic.com" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-2]
            image_id = filename_with_ext.split('.')[0]
            ext = "jpg"
            return f"steam_{image_id}.{ext}"
        except:
            pass

    # 5. Generic Case / Local Files / IGDB
    # Use MD5 of the string.
    # - Local: "[[Cover1.png]]" gives different hash than "[[Cover2.png]]".
    
    # Try to guess extension (useful for local pngs)
    ext = ".jpg"
    if "." in source_str:
        possible_ext = source_str.split(".")[-1].split("?")[0] # remove query params
        if len(possible_ext) <= 4: # avoid errors if not really an extension
            ext = "." + possible_ext

    hash_object = hashlib.md5(source_str.encode())
    return f"img_{hash_object.hexdigest()}{ext}"

def process_image(source_str, note_dest_dir, type="cover"):
    """
    Downloads URL or Copies Local File. 
    1. Checks/Saves to CACHE_DIR.
    2. Copies from CACHE_DIR to valid destination (bundle or static).
    Returns the relative path for Hugo frontmatter.
    """
    if not source_str:
        return None

    filename = get_image_filename(source_str)
    
    # 1. DEFINE DESTINATIONS
    # Cache location (Always shared)
    cache_path = DEST_CONFIG["cache_dir"] / filename
    
    # Final Destination
    if type == "content" or type == "cover" or type == "banner":
        # Ensure we are in a bundle structure: note_dest_dir should be the bundle directory
        if note_dest_dir:
            dest_dir = note_dest_dir # e.g. content/movies/avatar/
            dest_path = dest_dir / filename
            # Return relative path for Page Resources (just filename)
            return_path = filename 
        else:
            # Fallback (shouldn't happen with new logic)
            dest_dir = COVERS_DIR 
            dest_path = dest_dir / filename
            return_path = f"/images/covers/{filename}"
    else:
        # Fallback for misc types
        dest_path = DEST_CONFIG["static_images_dir"] / "misc" / filename
        return_path = f"/images/misc/{filename}"

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    is_local_image = "[[" in source_str
    
    # 2. POPULATE CACHE (If missing)
    if not cache_path.exists():
        # CASE A: Web URL (TMDB/TVDB/Etc)
        if str(source_str).startswith("http"):
            try:
                print(f"  [Downloading] {source_str} -> {filename}")
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(source_str, stream=True, timeout=10, headers=headers)
                if response.status_code == 200:
                    with open(cache_path, 'wb') as f:
                        shutil.copyfileobj(response.raw, f)
            except Exception as e:
                print(f"  [Error] Failed to download {source_str}: {e}")
                return None

        # CASE B: Local Obsidian Link [[...]]
        elif is_local_image:
            # Extract the clean path from the wikilink
            raw_path = re.search(r'\[\[(.*?)(\|.*)?\]\]', source_str)
            if raw_path:
                clean_path = raw_path.group(1)
                
                # Resolve the path
                local_file = BASE_DIR / clean_path
                # Search strategies
                if not local_file.exists():
                    local_file = SOURCE_COVERS_DIR / os.path.basename(clean_path)
                if not local_file.exists():
                    local_file = SOURCE_ROOT / clean_path

                if local_file.exists():
                    print(f"  [Caching] {local_file.name}")
                    shutil.copy(local_file, cache_path)
                else:
                    print(f"  [Warning] Local image not found: {clean_path}")
                    return None
    
    # 3. COPY FROM CACHE TO DESTINATION
    if cache_path.exists():
        if not dest_path.exists():
             shutil.copy(cache_path, dest_path)
        return return_path

    return None

def convert_youtube_links(text):
    """
    Converts YouTube links in the content to Hugo shortcodes.
    Example:
    https://www.youtube.com/watch?v=VIDEO_ID
    https://youtu.be/VIDEO_ID
    Becomes:
    {{< youtube VIDEO_ID >}}
    """
    def replacer(match):
        url = match.group(0)
        video_id = None
        
        if "youtube.com/watch?v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        
        if video_id:
            return f'{{{{< youtube {video_id} >}}}}'
        return url 

    youtube_pattern = r'(https?://(?:www\.)?youtube\.com/watch\?v=[\w-]+|https?://youtu\.be/[\w-]+)'
    return re.sub(youtube_pattern, replacer, text)

# ==========================================
# MAIN MIGRATION LOGIC
# ==========================================

def migrate():
    print("--- STARTING MIGRATION ---")

    # Tracking old covers/banners to clean up if needed (optional)
    covers = []
    banners = []

    for cover in COVERS_DIR.glob("*"):
        covers.append(cover.name)
    for banner in BANNERS_DIR.glob("*"):
        banners.append(banner.name)

    # 0. PRE-SCAN: Gather all valid files to validate WikiLinks
    known_files = set()
    for _, source_dir in SOURCE_DIRS.items():
        if source_dir.exists():
            for f in source_dir.glob("*.md"):
                known_files.add(f.stem)


    for obsidian_type, source_dir in SOURCE_DIRS.items():
        if not source_dir.exists():
            print(f"Skipping {obsidian_type}: Directory not found ({source_dir})")
            continue

        hugo_section = DEST_CONFIG["section_map"].get(obsidian_type, "others")
        target_dir = DEST_CONFIG["content_dir"] / hugo_section
        
        # Clean destination section (Danger: Removes existing files!)
        shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing section: {obsidian_type.upper()} -> {hugo_section}/")

        for file_path in source_dir.glob("*.md"):
            try:
                post = frontmatter.load(file_path)
                
                # Verify type matches the folder (sanity check)
                if post.get('type') != obsidian_type:
                    print(f"  [Warning] Type mismatch: {file_path.name} (Expected {obsidian_type}, got {post.get('type')})")
                    # We continue anyway, trusting folder structure over metadata for placement

                print(f"Processing: {file_path.name}")

                # 1. PROCESS RELATIONS (WikiLinks)
                for key in FRONTMATTER_LINKS:
                    if post.get(key):
                        if isinstance(post[key], list):
                            clean_list = []
                            for item in post[key]:
                                clean_list.append(clean_wikilink(item))
                            post[key] = clean_list
                        else:
                            post[key] = clean_wikilink(post[key])

                # 2. DETECT CONTENT IMAGES
                has_content_images = False
                content_images = []
                if post.content:
                    # Regex to find embedded images ![[image.png]]
                    content_images = re.findall(r'!\[\[(.*?)\]\]', post.content)
                    if content_images:
                        has_content_images = True

                # 3. PREPARE DESTINATION (Force Leaf Bundle)
                slug = file_path.stem
                
                # Always create a leaf bundle for consistent image resources
                post_dir = target_dir / slug
                post_dir.mkdir(parents=True, exist_ok=True)
                destination_file = post_dir / "index.md"
                image_target_dir = post_dir
                
                # 4. PROCESS IMAGES (Cover & Banner)
                if post.get('cover'):
                    new_cover = process_image(post['cover'], image_target_dir, type="cover")
                    if new_cover:
                        post['image'] = new_cover
                    del post['cover']

                if post.get('banner'):
                    new_banner = process_image(post['banner'], image_target_dir, type="banner")
                    if new_banner:
                        post['banner_image'] = new_banner
                    del post['banner']

                # 5. PROCESS CONTENT
                if post.content:
                    # A. Process Content Images
                    if has_content_images and content_images:
                        for image in content_images:
                            # Replicate wikilink format for handler
                            new_image = process_image(f"[[{image}]]", image_target_dir, type="content")
                            if new_image:
                                post.content = post.content.replace(f'![[{image}]]', f'![{os.path.basename(image)}]({new_image})')
                    
                    # B. Process Wikilinks
                    post.content = convert_wikilinks(post.content, known_files)

                    # C. Process YouTube Links
                    post.content = convert_youtube_links(post.content)

                # 6. WRITE FILE
                with open(destination_file, 'w', encoding='utf-8') as f:
                    f.write(frontmatter.dumps(post))

            except Exception as e:
                print(f"ERROR processing {file_path.name}: {e}")

    print("\n--- MIGRATION FINISHED ---")

    # Cleanup unused covers/banners if desired
    # (Commented out safety measure, enable if you want strict cleanup)
    # for cover in covers:
    #     if os.path.exists(COVERS_DIR / cover):
    #         os.remove(COVERS_DIR / cover)

if __name__ == "__main__":
    migrate()