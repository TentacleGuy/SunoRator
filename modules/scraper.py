from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from datetime import datetime
from utils.utils import *
from config.vars import *
from utils.socket_manager import socketio

class WebScraper:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.driver = None

    def emit_log(self, message):
        timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_queue.put(formatted_message)
        socketio.emit('log_update', {'data': formatted_message})

    def emit_progress(self, progress_type, value, max_value):
        socketio.emit('progress_update', {
            'type': progress_type,
            'value': value,
            'max': max_value
        })

    def emit_song_info(self, song_data, playlist_url):
        socketio.emit('song_info_update', {
            'song_url': song_data.get('song_url', ''),
            'playlist_url': playlist_url,
            'title': song_data.get('title', ''),
            'styles': song_data.get('styles', [])
        })

    def init_driver(self):
        self.emit_log("Initialisiere Webdriver...")
        chrome_options = Options()
        #chrome_options.add_argument("--headless")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.emit_log("Webdriver initialisiert.")

    def fetch_song_data(self, driver, song_url):
        """Fetches song data from the song page."""
        self.init_driver()
        try:
            self.driver.get(song_url)
            time.sleep(5)

            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            song_container = soup.find('div', class_='bg-vinylBlack-darker w-full h-full flex flex-col sm:flex-col md:flex-col lg:flex-row xl:flex-row lg:mt-8 xl:mt-8 lg:ml-32 xl:ml-32 overflow-y-scroll items-center sm:items-center md:items-center lg:items-start xl:items-start')

            if not song_container:
                return {}

            title_input = song_container.find('input')
            title = title_input['value'] if title_input else None

            genres = [a.get_text(strip=True).replace(",", "").replace(" ", "") 
                    for a in song_container.find_all('a', href=lambda href: href and '/style/' in href)]
            genres = genres or ["Keine Genres gefunden"]

            lyrics_textarea = song_container.find('textarea')
            lyrics = lyrics_textarea.get_text(strip=True) if lyrics_textarea else "Keine Lyrics gefunden"

            return {
                "song_url": song_url,
                "title": title,
                "styles": genres,
                "lyrics": lyrics
            }
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def scrape_collections(self, stop_event, log_queue, pause_event):
        self.init_driver()
        stats = {
            'playlist': {'found': 0, 'new': 0},
            'artist': {'found': 0, 'new': 0},
            'genre': {'found': 0, 'new': 0}
        }

        try:
            self.emit_log("Opening suno.com...")
            self.driver.get("https://suno.com")
            time.sleep(5)

            # Scrape playlists
            playlist_elements = self.driver.find_elements(By.XPATH, "//a[@title and contains(@href, '/playlist/')]")
            for elem in playlist_elements:
                url = elem.get_attribute("href")
                title = elem.get_attribute("title")
                stats['playlist']['found'] += 1
                if add_url_to_collection(url, "playlist", title):
                    stats['playlist']['new'] += 1
                self.emit_log(f"Found Playlist: {title} - {url}")

            # Scrape artists
            artist_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/@')]//span[@title]")
            for elem in artist_elements:
                url = elem.find_element(By.XPATH, "..").get_attribute("href")
                title = elem.get_attribute("title")
                stats['artist']['found'] += 1
                if add_url_to_collection(url, "artist", title):
                    stats['artist']['new'] += 1
                self.emit_log(f"Found Artist: {title} - {url}")

            # Scrape styles
            style_elements = self.driver.find_elements(By.XPATH, "//a[@title and contains(@href, '/style/')]")
            for elem in style_elements:
                url = elem.get_attribute("href")
                title = elem.get_attribute("title")
                stats['genre']['found'] += 1
                if add_url_to_collection(url, "genre", title):
                    stats['genre']['new'] += 1
                self.emit_log(f"Found Style: {title} - {url}")

            # Output final statistics
            self.emit_log("\nCollection URL Scraping Statistics:")
            self.emit_log(f"Playlists: {stats['playlist']['found']} found, {stats['playlist']['new']} new")
            self.emit_log(f"Artists: {stats['artist']['found']} found, {stats['artist']['new']} new")
            self.emit_log(f"Styles: {stats['genre']['found']} found, {stats['genre']['new']} new")
            self.emit_log("\nCollection URL scraping completed successfully!")

            socketio.emit('thread_status_changed')

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            if stop_event:
                stop_event.set()

    def scrape_song_urls(self, stop_event, log_queue, pause_event):
        self.init_driver()
        stats = {
            'homepage': {'songs_found': 0, 'new_songs': 0},
            'playlists': {'processed': 0, 'songs_found': 0, 'new_songs': 0},
            'artists': {'processed': 0, 'songs_found': 0, 'new_songs': 0},
            'genres': {'processed': 0, 'songs_found': 0, 'new_songs': 0}
        }

        try:
            playlists = get_playlist_data()
            self.emit_log("Starting song URL scraping...")

            # First scan homepage
            self.emit_log("\nScanning homepage for songs...")
            self.driver.get("https://suno.com")
            time.sleep(5)

            # Find all links containing '/song/'
            song_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/song/')]")

            for elem in song_elements:
                song_url = elem.get_attribute("href")
                # Try to get title from different possible sources
                title = elem.get_attribute("title")
                if not title:
                    try:
                        # Try to get text from inner span
                        title = elem.find_element(By.CSS_SELECTOR, "span").text
                    except:
                        try:
                            # Try direct text content
                            title = elem.text
                        except:
                            title = "Unknown"

                stats['homepage']['songs_found'] += 1
                if add_url_to_collection(song_url, "song", title):
                    stats['homepage']['new_songs'] += 1
                    self.emit_log(f"Found new song on homepage: {title} - {song_url}")

            save_playlist_data(playlists)
            # Then process collection URLs
            for collection_type in ['playlists', 'artists', 'genres']:
                if stop_event.is_set():
                    self.emit_log("Stopping song URL scraping...")
                    break

                enabled_collections = {url: data for url, data in playlists[collection_type].items()
                                       if data.get('enabled', True)}

                if enabled_collections:
                    self.emit_log(f"\nProcessing {collection_type}: {len(enabled_collections)} enabled items")

                for url, data in enabled_collections.items():
                    if stop_event.is_set():
                        break

                    while pause_event.is_set():
                        time.sleep(0.1)
                        if stop_event.is_set():
                            break

                    self.emit_log(f"\nProcessing {collection_type} URL: {url}")
                    self.driver.get(url)
                    time.sleep(5)

                    song_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/song/')]")
                    current_songs = set(song.get('url', '') for song in data.get('song_urls', []))
                    new_songs = []

                    for elem in song_elements:
                        song_url = elem.get_attribute("href")
                        title = elem.get_attribute("title")
                        if not title:
                            try:
                                title = elem.find_element(By.CSS_SELECTOR, "span").text
                            except:
                                try:
                                    title = elem.text
                                except:
                                    title = "Unknown"

                        stats[collection_type]['songs_found'] += 1

                        if song_url not in current_songs:
                            new_songs.append({"url": song_url, "title": title})
                            stats[collection_type]['new_songs'] += 1
                            self.emit_log(f"Found new song: {title}")

                    if new_songs:
                        data['song_urls'] = data.get('song_urls', []) + new_songs

                    data['processed'] = True
                    stats[collection_type]['processed'] += 1
                    self.emit_log(f"Found {len(new_songs)} new songs in this {collection_type}")

            save_playlist_data(playlists)

            # Output final statistics
            self.emit_log("\nSong URL Scraping Statistics:")
            self.emit_log(f"\nHomepage:")
            self.emit_log(f"Total songs found: {stats['homepage']['songs_found']}")
            self.emit_log(f"New songs: {stats['homepage']['new_songs']}")

            for ctype in ['playlists', 'artists', 'genres']:
                self.emit_log(f"\n{ctype.capitalize()}:")
                self.emit_log(f"Processed: {stats[ctype]['processed']}")
                self.emit_log(f"Total songs found: {stats[ctype]['songs_found']}")
                self.emit_log(f"New songs: {stats[ctype]['new_songs']}")

            self.emit_log("\nSong URL scraping completed successfully!")
            socketio.emit('thread_status_changed')

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
            if stop_event:
                stop_event.set()

    def scrape_single_url(self, stop_event, log_queue, pause_event, url):
        self.init_driver()
        try:
            self.emit_log(f"Starting to scrape URL: {url}")
            self.driver.get(url)
            time.sleep(5)

            song_elements = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/song/')]")
            song_urls = []

            for elem in song_elements:
                song_url = elem.get_attribute("href")
                title = elem.get_attribute("title")
                if not title:
                    try:
                        title = elem.find_element(By.CSS_SELECTOR, "span").text
                    except:
                        title = "Unknown"
                song_urls.append({"url": song_url, "title": title})
                self.emit_log(f"Found song: {title} - {song_url}")

            playlists = get_playlist_data()
            for collection_type in ['playlists', 'artists', 'genres']:
                if url in playlists[collection_type]:
                    playlists[collection_type][url]["song_urls"] = song_urls
                    playlists[collection_type][url]["processed"] = True
                    save_playlist_data(playlists)
                    self.emit_log(f"Updated {collection_type}: {url} with {len(song_urls)} songs")
                    break

            socketio.emit('playlists_updated')
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def add_manual_song(self, song_url):
        return add_url_to_collection(song_url, "songs", {
            "url": song_url,
            "enabled": True,
            "processed": False,
            "title": ""
        })

    def scrape_playlist_urls(self, urls, collection_type, stop_event, pause_event):
        self.init_driver()
        playlists = get_playlist_data()
        total_urls = len(urls)

        try:
            for i, url in enumerate(urls):
                if stop_event.is_set():
                    self.emit_log("Stopping URL scraping...")
                    break

                while pause_event.is_set():
                    time.sleep(0.1)
                    if stop_event.is_set():
                        break

                self.emit_log(f"Processing {collection_type} URL {i + 1}/{total_urls}: {url}")

                try:
                    self.driver.get(url)
                    time.sleep(5)

                    song_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/song/')]")
                    song_urls = list(set([link.get_attribute("href") for link in song_links]))

                    # Convert to objects with status attributes
                    song_objects = [{
                        "url": url,
                        "enabled": True,
                        "processed": False,
                        "title": ""
                    } for url in song_urls]

                    # Log each found song URL
                    for song_url in song_urls:
                        self.emit_log(f"Found song URL: {song_url}")

                    if url not in playlists[collection_type]:
                        playlists[collection_type][url] = {
                            "song_urls": [],
                            "processed": False
                        }

                    playlists[collection_type][url]["song_urls"] = song_objects
                    playlists[collection_type][url]["processed"] = True

                    save_playlist_data(playlists)
                    self.emit_log(f"Successfully scraped {collection_type}: {url} with {len(song_urls)} songs")
                    self.emit_progress('playlist', i + 1, total_urls)

                except Exception as e:
                    self.emit_log(f"Error processing {collection_type} {url}: {str(e)}")
                    continue

            socketio.emit('thread_status_changed')
            socketio.emit('playlists_updated')

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def scrape_songs(self, stop_event, log_queue, pause_event):
        self.init_driver()
        try:
            processed_song_ids = get_processed_song_ids()
            playlists = get_playlist_data()

            # Process individual songs
            single_songs = [(song['url'], None) for song in playlists['songs'].values()]

            # Process songs from all other collections
            collection_songs = []
            for collection_type in ['playlists', 'artists', 'genres']:
                for collection_url, data in playlists[collection_type].items():
                    if data.get('song_urls'):
                        collection_songs.extend([(song['url'], collection_url) for song in data['song_urls']])

            # Update overall progress
            total_songs = len(single_songs) + len(collection_songs)
            self.emit_log(f"Found {len(single_songs)} single songs and {len(collection_songs)} collection songs")
            self.emit_progress('overall', 0, total_songs)
            processed_count = 0

            # Process manual songs first
            if single_songs:
                self.emit_log("Processing manual songs...")
                for song_obj, _ in single_songs:
                    if stop_event.is_set():
                        self.emit_log("Stopping song scraping...")
                        break

                    while pause_event.is_set():
                        time.sleep(0.1)
                        if stop_event.is_set():
                            break

                    song_url = song_obj['url']
                    song_id = extract_song_id_from_url(song_url)

                    if song_id in processed_song_ids:
                        self.emit_log(f"Song {song_id} already exists -> skipping")
                        processed_count += 1
                        self.emit_progress('overall', processed_count, total_songs)
                        continue

                    try:
                        self.emit_log(f"Processing manual song {song_id}")
                        self.driver.get(song_url)
                        time.sleep(2)

                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        song_container = soup.find('div',
                                                   class_='bg-vinylBlack-darker w-full h-full flex flex-col sm:flex-col md:flex-col lg:flex-row xl:flex-row lg:mt-8 xl:mt-8 lg:ml-32 xl:ml-32 overflow-y-scroll items-center sm:items-center md:items-center lg:items-start xl:items-start')

                        if song_container:
                            title_input = song_container.find('input')
                            title = title_input['value'] if title_input else f"Unknown_{song_id}"

                            genres = [a.get_text(strip=True).replace(",", "").replace(" ", "")
                                      for a in
                                      song_container.find_all('a', href=lambda href: href and '/style/' in href)]
                            genres = genres or ["Unknown"]

                            lyrics_textarea = song_container.find('textarea')
                            lyrics = lyrics_textarea.get_text(strip=True) if lyrics_textarea else ""

                            song_data = {
                                "song_url": song_url,
                                "playlist_url": None,
                                "title": title,
                                "styles": genres,
                                "lyrics": lyrics
                            }

                            self.save_song_data(song_data)
                            self.emit_song_info(song_data, None)

                            # Update status in playlists data
                            playlists = get_playlist_data()  # Get fresh data
                            playlists['single_songs'][song_url]['processed'] = True
                            save_playlist_data(playlists)

                            processed_count += 1

                            self.emit_progress('overall', processed_count, total_songs)
                            self.emit_log(f"Successfully processed manual song {title}")

                    except Exception as e:
                        self.emit_log(f"Error processing manual song: {str(e)}")
                        continue

            # Process playlist songs
            if collection_songs:
                self.emit_log("Processing playlist songs...")
                current_playlist = None
                current_playlist_processed = 0
                total_playlists = len(set(playlist_url for _, playlist_url in collection_songs))
                current_playlist_count = 0

                self.emit_progress('playlist', 0, total_playlists)

                for song_url, playlist_url in collection_songs:
                    if stop_event.is_set():
                        self.emit_log("Stopping song scraping...")
                        break

                    while pause_event.is_set():
                        time.sleep(0.1)
                        if stop_event.is_set():
                            break

                    if current_playlist != playlist_url:
                        current_playlist = playlist_url
                        current_playlist_count += 1
                        current_playlist_processed = 0
                        playlist_song_count = len([s for s, p in collection_songs if p == playlist_url])
                        self.emit_progress('playlist', current_playlist_count, total_playlists)
                        self.emit_progress('song', 0, playlist_song_count)
                        self.emit_log(f"\nProcessing songs from playlist: {playlist_url}")

                    song_id = extract_song_id_from_url(song_url)
                    if song_id in processed_song_ids:
                        self.emit_log(f"Song {song_id} already exists -> skipping")
                        processed_count += 1
                        current_playlist_processed += 1
                        self.emit_progress('overall', processed_count, total_songs)
                        self.emit_progress('song', current_playlist_processed, playlist_song_count)
                        continue

                    try:
                        self.emit_log(f"Processing song {song_id}")
                        self.driver.get(song_url)
                        time.sleep(2)

                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        song_container = soup.find('div',
                                                   class_='bg-vinylBlack-darker w-full h-full flex flex-col sm:flex-col md:flex-col lg:flex-row xl:flex-row lg:mt-8 xl:mt-8 lg:ml-32 xl:ml-32 overflow-y-scroll items-center sm:items-center md:items-center lg:items-start xl:items-start')

                        if song_container:
                            title_input = song_container.find('input')
                            title = title_input['value'] if title_input else f"Unknown_{song_id}"

                            genres = [a.get_text(strip=True).replace(",", "").replace(" ", "")
                                      for a in
                                      song_container.find_all('a', href=lambda href: href and '/style/' in href)]
                            genres = genres or ["Unknown"]

                            lyrics_textarea = song_container.find('textarea')
                            lyrics = lyrics_textarea.get_text(strip=True) if lyrics_textarea else ""

                            song_data = {
                                "song_url": song_url,
                                "playlist_url": playlist_url,
                                "title": title,
                                "styles": genres,
                                "lyrics": lyrics
                            }

                            self.save_song_data(song_data)
                            self.emit_song_info(song_data, playlist_url)
                            processed_count += 1
                            current_playlist_processed += 1

                            self.emit_progress('overall', processed_count, total_songs)
                            self.emit_progress('song', current_playlist_processed, playlist_song_count)
                            self.emit_log(f"Successfully processed song {title}")

                    except Exception as e:
                        self.emit_log(f"Error processing song: {str(e)}")
                        continue

                self.emit_log("Song scraping completed")
                socketio.emit('thread_status_changed')
                socketio.emit('playlists_updated')

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

    def save_song_data(self, song_data):
        updated_files = []
        
        # Save song file and add to updated files
        filename = clean_filename(f"{song_data['title']}_{extract_song_id_from_url(song_data['song_url'])}.json")
        save_json(song_data, os.path.join(SONGS_DIR, filename))
        
        # Update styles
        all_styles = load_json(STYLES_FILE) or []
        if new_styles := [s for s in song_data['styles'] if s not in all_styles]:
            all_styles.extend(new_styles)
            save_json(all_styles, STYLES_FILE)
            updated_files.append('all_styles.json')
        
        # Update style mapping
        song_styles_mapping = load_json(SONG_STYLES_MAPPING_FILE) or {}
        song_styles_mapping[song_data['song_url']] = song_data['styles']
        save_json(song_styles_mapping, SONG_STYLES_MAPPING_FILE)
        updated_files.append('song_styles_mapping.json')
        
        # Update meta tags
        meta_tags = extract_meta_tags(song_data['lyrics'])
        all_meta_tags = load_json(META_TAGS_FILE) or []
        if new_meta_tags := [t for t in meta_tags if t not in all_meta_tags]:
            all_meta_tags.extend(new_meta_tags)
            save_json(all_meta_tags, META_TAGS_FILE)
            updated_files.append('all_meta_tags.json')
        
        # Update meta mapping
        song_meta_mapping = load_json(SONG_META_MAPPING_FILE) or {}
        song_meta_mapping[song_data['song_url']] = meta_tags
        save_json(song_meta_mapping, SONG_META_MAPPING_FILE)
        updated_files.append('song_meta_mapping.json')

        # Emit the file updates event
        socketio.emit('file_updates', {'updated_files': updated_files})

    def update_song_data(self, song_data, song_url, all_styles, song_styles_mapping, all_meta_tags, song_meta_mapping):
        # Update styles
        new_styles = [style for style in song_data['styles'] if style not in all_styles]
        if new_styles:
            all_styles.extend(new_styles)
            save_json(all_styles, STYLES_FILE)

        # Update song-styles mapping
        song_styles_mapping[song_url] = song_data['styles']
        save_json(song_styles_mapping, SONG_STYLES_MAPPING_FILE)

        # Update meta tags
        meta_tags = extract_meta_tags(song_data['lyrics'])
        new_meta_tags = [tag for tag in meta_tags if tag not in all_meta_tags]
        if new_meta_tags:
            all_meta_tags.extend(new_meta_tags)
            save_json(all_meta_tags, META_TAGS_FILE)

        # Update song-meta mapping
        song_meta_mapping[song_url] = meta_tags
        save_json(song_meta_mapping, SONG_META_MAPPING_FILE)

        # Save song data
        song_file_name = f"{song_data['title']}_{extract_song_id_from_url(song_url)}.json"
        song_file_path = os.path.join(SONGS_DIR, song_file_name)
        save_json(song_data, song_file_path)

    def scrape_url_metadata(self, url, url_type):
        self.driver.get(url)
        time.sleep(2)
        title = self.driver.find_element(By.TAG_NAME, 'h1').text
        return {
            'title': title,
            'type': url_type,
            'url': url,
            'enabled': True,
            'songs': []
        }
