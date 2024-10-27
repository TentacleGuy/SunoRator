from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from utils.utils import *
from config.vars import *
from utils.socket_manager import socketio

class WebScraper:
    def __init__(self, log_queue):
        self.log_queue = log_queue
        self.driver = None

    def emit_log(self, message):
        self.log_queue.put(message)
        socketio.emit('log_update', {'data': message})

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
        chrome_options.add_argument("--headless")
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

    def scrape_playlists(self, stop_event, log_queue):
        playlists = load_json(SCRAPED_PLAYLISTS_FILE)
        total_songs = 0
        
        self.init_driver()  # Initialize driver at start of function

        try:
            self.emit_log("Opening suno.com...")
            self.driver.get("https://suno.com")
            time.sleep(5)

            self.emit_log("Searching for playlist links...")
            playlist_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/playlist/')]")
            playlist_urls = list(set([link.get_attribute("href") for link in playlist_links]))
            self.emit_log(f"Found playlist links: {len(playlist_urls)}")

            for i, playlist_url in enumerate(playlist_urls):
                if stop_event.is_set():
                    break
                    
                self.driver.get(playlist_url)
                time.sleep(5)

                song_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/song/')]")
                song_urls = list(set([link.get_attribute("href") for link in song_links]))

                total_songs += len(song_urls)
                playlists[playlist_url] = {"song_urls": song_urls}
                
                save_json(playlists, SCRAPED_PLAYLISTS_FILE)
                
                self.emit_log(f"Playlist scraped: {playlist_url} with {len(song_urls)} songs")
                self.emit_progress('playlist', i + 1, len(playlist_urls))

            self.emit_log(f"Scraping completed: {len(playlists)} playlists and {total_songs} songs found")
            
        except Exception as e:
            self.emit_log(f"Error during playlist scraping: {str(e)}")
            raise

    def scrape_songs(self, stop_event, log_queue):
        self.init_driver()
        try:
            processed_song_ids = get_processed_song_ids()
            playlists = load_json(SCRAPED_PLAYLISTS_FILE)
            total_songs = sum(len(playlist['song_urls']) for playlist in playlists.values())
            processed_songs = 0

            self.emit_log(f"Found {total_songs} total songs to process")
            self.emit_progress('overall', 0, total_songs)

            for playlist_url, playlist_data in playlists.items():
                if stop_event.is_set():
                    break

                self.emit_log(f"\nStarting new playlist: {playlist_url}")
                
                for song_url in playlist_data['song_urls']:
                    if stop_event.is_set():
                        break

                    song_id = extract_song_id_from_url(song_url)
                    self.emit_log(f"\nProcessing song ID: {song_id}")
                    
                    if song_id in processed_song_ids:
                        self.emit_log("Song already exists, skipping")
                        processed_songs += 1
                        continue

                    try:
                        self.emit_log(f"Loading URL: {song_url}")
                        self.driver.get(song_url)
                        time.sleep(2)
                        self.emit_log("Page loaded")

                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        self.emit_log("HTML parsed")
                        
                        song_container = soup.find('div', class_='bg-vinylBlack-darker w-full h-full flex flex-col sm:flex-col md:flex-col lg:flex-row xl:flex-row lg:mt-8 xl:mt-8 lg:ml-32 xl:ml-32 overflow-y-scroll items-center sm:items-center md:items-center lg:items-start xl:items-start')
                        
                        if not song_container:
                            self.emit_log("No song container found, skipping")
                            continue

                        self.emit_log("Extracting song data")
                        title_input = song_container.find('input')
                        title = title_input['value'] if title_input else f"Unknown_{song_id}"

                        genres = [a.get_text(strip=True).replace(",", "").replace(" ", "") 
                                for a in song_container.find_all('a', href=lambda href: href and '/style/' in href)]
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

                        self.emit_log(f"Saving song: {title}")
                        self.save_song_data(song_data)
                        self.emit_song_info(song_data, playlist_url)
                        processed_songs += 1
                        
                        self.emit_progress('overall', processed_songs, total_songs)
                        self.emit_log(f"Successfully processed song {processed_songs}/{total_songs}")

                    except Exception as e:
                        self.emit_log(f"Error: {str(e)}")
                        continue

            self.emit_log("Song scraping completed")
            
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None


    def save_song_data(self, song_data):
        self.emit_log("Starting save process...")
        song_id = extract_song_id_from_url(song_data['song_url'])
        filename = clean_filename(f"{song_data['title']}_{song_id}.json")
        
        # Save main song file first
        self.emit_log(f"Saving main song file: {filename}")
        save_json(song_data, os.path.join(SONGS_DIR, filename))
        
        # Update styles
        self.emit_log("Updating styles...")
        all_styles = load_json(STYLES_FILE) or []
        new_styles = [s for s in song_data['styles'] if s not in all_styles]
        if new_styles:
            all_styles.extend(new_styles)
            save_json(all_styles, STYLES_FILE)
        
        # Update style mapping
        self.emit_log("Updating style mapping...")
        song_styles_mapping = load_json(SONG_STYLES_MAPPING_FILE) or {}
        song_styles_mapping[song_data['song_url']] = song_data['styles']
        save_json(song_styles_mapping, SONG_STYLES_MAPPING_FILE)
        
        # Update meta tags
        self.emit_log("Updating meta tags...")
        meta_tags = extract_meta_tags(song_data['lyrics'])
        all_meta_tags = load_json(META_TAGS_FILE) or []
        new_meta_tags = [t for t in meta_tags if t not in all_meta_tags]
        if new_meta_tags:
            all_meta_tags.extend(new_meta_tags)
            save_json(all_meta_tags, META_TAGS_FILE)
        
        # Update meta mapping
        self.emit_log("Updating meta mapping...")
        song_meta_mapping = load_json(SONG_META_MAPPING_FILE) or {}
        song_meta_mapping[song_data['song_url']] = meta_tags
        save_json(song_meta_mapping, SONG_META_MAPPING_FILE)
        
        self.emit_log("Save completed successfully")

            
    def update_song_data(self, song_data, song_url, all_styles, song_styles_mapping, 
                        all_meta_tags, song_meta_mapping):
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
