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

# Paths are relative to the script location (assuming scripts/migration.py)
BASE_DIR = Path(__file__).parent.parent.absolute()

# Source Directories (Obsidian Vault)
SOURCE_ROOT = Path("/home/christian/syncthing/Obsidian/Atlas")
SOURCE_PATH = SOURCE_ROOT / "Media Tracker"
SOURCE_DIRS = {
    "movie": SOURCE_PATH / "Movies",
    "tv": SOURCE_PATH / "TVs",
    "season": SOURCE_PATH / "Seasons",
    "videogame": SOURCE_PATH / "Juegos"
}
SOURCE_COVERS_DIR = SOURCE_PATH / "Portadas"

# Destination Directories (Hugo)
CONTENT_DIR = BASE_DIR / "content"
IMAGES_DIR = BASE_DIR / "static" / "images"
COVERS_DIR = IMAGES_DIR / "covers"
BANNERS_DIR = IMAGES_DIR / "banners"

# Mappings: Obsidian Type -> Hugo Section (Folder)
SECTION_MAP = {
    "movie": "movies",
    "tv": "tv",
    "season": "seasons",
    "videogame": "games"
}

# Ensure destination directories exist
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
    Genera un nombre de archivo único.
    PRIORIDAD 1: ID de la imagen extraído de la URL (TMDB/TVDB) para permitir cambios de portada.
    PRIORIDAD 2: Hash MD5 del string completo (para local files o URLs raras).
    """
    source_str = str(source_str)
    
    # 1. Caso TMDB (Extraer ID único de la imagen)
    # URL ej: https://image.tmdb.org/t/p/original/1CfZCb56vWjq37uXtbKNMevMzwG.jpg
    if "tmdb.org" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-1] # 1CfZCb56vWjq37uXtbKNMevMzwG.jpg
            image_id = filename_with_ext.split('.')[0]    # 1CfZCb56vWjq37uXtbKNMevMzwG
            ext = filename_with_ext.split('.')[1]         # jpg
            return f"tmdb_{image_id}.{ext}"
        except:
            pass # Si falla el parseo, saltamos al hash

    # 2. Caso TheTVDB (Extraer nombre de archivo)
    # URL ej: https://artworks.thetvdb.com/banners/movies/1234/posters/1234.jpg
    if "thetvdb.com" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-1]
            image_id = filename_with_ext.split('.')[0]
            ext = filename_with_ext.split('.')[1]
            return f"tvdb_{image_id}.{ext}"
        except:
            pass

    if "steamgriddb" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-1]
            image_id = filename_with_ext.split('.')[0]
            ext = filename_with_ext.split('.')[1]
            return f"steamgriddb_{image_id}.{ext}"
        except:
            pass
    
    if "steamstatic.com" in source_str:
        try:
            filename_with_ext = source_str.split('/')[-2]
            image_id = filename_with_ext.split('.')[0]
            ext = "jpg"
            return f"steam_{image_id}.{ext}"
        except:
            pass

    # 3. Caso Genérico / Archivos Locales / Steam / IGDB
    # Usamos MD5 del string.
    # - Si es local: "[[Cover1.png]]" da un hash distinto a "[[Cover2.png]]".
    
    # Intentar adivinar extensión (útil para png locales)
    ext = ".jpg"
    if "." in source_str:
        possible_ext = source_str.split(".")[-1].split("?")[0] # quitar query params
        if len(possible_ext) <= 4: # evitar errores si no es extensión
            ext = "." + possible_ext

    hash_object = hashlib.md5(source_str.encode())
    return f"img_{hash_object.hexdigest()}{ext}"

def process_image(source_str, note_src, type="cover"):
    """
    Downloads URL or Copies Local File. 
    Returns the relative path for Hugo frontmatter.
    """
    if not source_str:
        return None

    # Determine target filename
    if type == "cover":
        folder = "covers"
    elif type == "banner":
        folder = "banners"
    elif type == "content":
        folder = "content"

    filename = get_image_filename(source_str)

    if type == "content" and note_src:
        # note_src in this context will be the destination bundle directory when type="content"
        # We want to save to bundle_dir/images
        folder_dir = note_src / "images"
        folder_dir.mkdir(parents=True, exist_ok=True)
        dest_path = folder_dir / filename
        return_path = f"images/{filename}"
    else:
        dest_path = IMAGES_DIR / folder / filename
        return_path = f"images/{folder}/{filename}"
    
    is_local_image = "[[" in source_str
    
    # CHECK CACHE: If file exists, skip download.
    if not is_local_image and dest_path.exists():
        # print(f"  [Cache Hit] {filename}")
        return return_path

    # CASE A: Web URL (TMDB/TVDB)
    if str(source_str).startswith("http"):
        try:
            print(f"  [Downloading] {source_str} -> {filename}")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(source_str, stream=True, timeout=10, headers=headers)
            if response.status_code == 200:
                with open(dest_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                return return_path
        except Exception as e:
            print(f"  [Error] Failed to download {source_str}: {e}")
            return None

    # CASE B: Local Obsidian Link [[...]]
    elif is_local_image:
        # Extract the clean path from the wikilink
        # Example: "[[Media Tracker/Portadas/Img.png]]" -> "Media Tracker/Portadas/Img.png"
        raw_path = re.search(r'\[\[(.*?)(\|.*)?\]\]', source_str)
        if raw_path:
            clean_path = raw_path.group(1)
            
            # Resolve the path. It might be relative to Vault root or just a filename in "Portadas"
            # 1. Try absolute path from Vault Root
            local_file = BASE_DIR / clean_path
            
            # 2. If not found, try looking inside the "Portadas" folder directly
            if not local_file.exists():
                local_file = SOURCE_COVERS_DIR / os.path.basename(clean_path)
            
            # 3. If not found, try looking inside the root of the vault
            if not local_file.exists():
                local_file = SOURCE_ROOT / clean_path

            if local_file.exists():
                print(f"  [Copying] {local_file.name} -> {filename}")
                shutil.copy(local_file, dest_path)
                return return_path
            else:
                print(f"  [Warning] Local image not found: {clean_path}")

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

    # Get all covers and banners
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

        hugo_section = SECTION_MAP.get(obsidian_type, "others")
        target_dir = CONTENT_DIR / hugo_section
        shutil.rmtree(target_dir, ignore_errors=True)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing section: {obsidian_type.upper()} -> {hugo_section}/")

        for file_path in source_dir.glob("*.md"):
            try:
                post = frontmatter.load(file_path)
                
                # Verify type matches the folder (sanity check)
                if post.get('type') != obsidian_type:
                    print(f"  [Warning] Type mismatch: {file_path.name}")
                    pass

                print(f"Processing: {file_path.name}")

                # 1. PROCESS IMAGES (Cover & Banner)
                if post.get('cover'):
                    new_cover = process_image(post['cover'], file_path, type="cover")
                    if new_cover:
                        post['image'] = new_cover
                        cover_name = new_cover.split("/")[-1]
                        if cover_name in covers:
                            covers.remove(cover_name)
                    # Remove original obsidian field to keep frontmatter clean
                    del post['cover']

                if post.get('banner'):
                    new_banner = process_image(post['banner'], file_path, type="banner")
                    if new_banner:
                        post['banner_image'] = new_banner
                        banner_name = new_banner.split("/")[-1]
                        if banner_name in banners:
                            banners.remove(banner_name)
                    del post['banner']

                # 2. PROCESS RELATIONS (WikiLinks)
                
                # Handle 'serie' (Single link)
                if post.get('serie'):
                    post['serie'] = clean_wikilink(post['serie'])

                # Handle 'temporadas' (List of links)
                if post.get('temporadas') and isinstance(post['temporadas'], list):
                    clean_list = []
                    for temp in post['temporadas']:
                        clean_list.append(clean_wikilink(temp))
                    post['temporadas'] = clean_list

                # Handle 'related' (List of links)
                if post.get('related') and isinstance(post['related'], list):
                    clean_related = []
                    for rel in post['related']:
                        clean_related.append(clean_wikilink(rel))
                    post['related'] = clean_related

                # 3. DETECT CONTENT IMAGES
                has_content_images = False
                content_images = []
                if post.content:
                    content_images = re.findall(r'!\[\[(.*?)\]\]', post.content)
                    if content_images:
                        has_content_images = True

                # 4. PREPARE DESTINATION
                slug = file_path.stem
                
                if has_content_images:
                    # Leaf Bundle: folder/index.md
                    post_dir = target_dir / slug
                    post_dir.mkdir(parents=True, exist_ok=True)
                    destination_file = post_dir / "index.md"
                    image_target_dir = post_dir 
                else:
                    # Simple Page: filename.md
                    destination_file = target_dir / f"{slug}.md"
                    image_target_dir = None

                # 5. PROCESS CONTENT
                if post.content:
                    # A. Process Images
                    if has_content_images:
                        for image in content_images:
                            new_image = process_image(f"[[{image}]]", image_target_dir, type="content")
                            if new_image:
                                post.content = post.content.replace(f'![[{image}]]', f'![{os.path.basename(image)}]({new_image})')
                    
                    # B. Process Wikilinks
                    post.content = convert_wikilinks(post.content, known_files)

                    post.content = convert_youtube_links(post.content)

                # 6. WRITE FILE
                with open(destination_file, 'w', encoding='utf-8') as f:
                    f.write(frontmatter.dumps(post))

            except Exception as e:
                print(f"ERROR processing {file_path.name}: {e}")

    print("\n--- MIGRATION FINISHED ---")

    # Remove unused covers
    for cover in covers:
        os.remove(COVERS_DIR / cover)

    # Remove unused banners
    for banner in banners:
        os.remove(BANNERS_DIR / banner)

if __name__ == "__main__":
    migrate()