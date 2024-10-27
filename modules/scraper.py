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

def fetch_song_data(driver, song_url):
    """Fetches song data from the song page."""
    driver.get(song_url)
    time.sleep(5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
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

    def scrape_playlists(self, stop_event, log_queue):
        playlists = load_json(SCRAPED_PLAYLISTS_FILE)
        total_songs = 0
        
        self.init_driver()
        try:
            self.emit_log("Öffne die Webseite suno.com...")
            self.driver.get("https://suno.com")
            time.sleep(5)

            self.emit_log("Suche nach Playlist-Links...")
            playlist_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/playlist/')]")
            playlist_urls = list(set([link.get_attribute("href") for link in playlist_links]))
            self.emit_log(f"Gefundene Playlist-Links: {len(playlist_urls)}")

            for i, playlist_url in enumerate(playlist_urls):
                if stop_event.is_set():
                    break
                    
                self.driver.get(playlist_url)
                time.sleep(5)

                song_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '/song/')]")
                song_urls = list(set([link.get_attribute("href") for link in song_links]))

                total_songs += len(song_urls)
                playlists[playlist_url] = {"song_urls": song_urls}
                
                self.emit_log(f"Playlist gescrapt: {playlist_url} mit {len(song_urls)} Songs.")
                self.emit_progress('playlist', i + 1, len(playlist_urls))

            save_json(playlists, SCRAPED_PLAYLISTS_FILE)
            self.emit_log(f"Scraping abgeschlossen: {len(playlists)} Playlists und {total_songs} Songs gefunden.")
            
        finally:
            self.driver.quit()

    def scrape_songs(self, stop_event, log_queue):
        self.init_driver()
        try:
            playlists = load_json(SCRAPED_PLAYLISTS_FILE)
            processed_song_ids = get_processed_song_ids()
            total_songs = sum(len(playlist['song_urls']) for playlist in playlists.values())
            processed_songs = 0

            self.emit_log("Starting song scraping process...")
            self.emit_progress('overall', 0, total_songs)

            for playlist_url, playlist_data in playlists.items():
                if stop_event.is_set():
                    break

                for song_url in playlist_data['song_urls']:
                    if stop_event.is_set():
                        break

                    song_id = extract_song_id_from_url(song_url)
                    if song_id in processed_song_ids:
                        processed_songs += 1
                        continue

                    song_data = fetch_song_data(self.driver, song_url)
                    if song_data:
                        self.emit_song_info(song_data, playlist_url)
                        self.save_song_data(song_data)
                        processed_songs += 1
                        self.emit_progress('overall', processed_songs, total_songs)
                        self.emit_log(f"Processed song {processed_songs}/{total_songs}: {song_data['title']}")

        finally:
            self.driver.quit()

    def save_song_data(self, song_data):
        song_id = extract_song_id_from_url(song_data['song_url'])
        filename = clean_filename(f"{song_data['title']}_{song_id}.json")
        
        with file_lock:
            # Save song file
            save_json(song_data, os.path.join(SONGS_DIR, filename))
            
            # Update metadata files
            all_styles = load_json(STYLES_FILE) or []
            song_styles_mapping = load_json(SONG_STYLES_MAPPING_FILE) or {}
            all_meta_tags = load_json(META_TAGS_FILE) or []
            song_meta_mapping = load_json(SONG_META_MAPPING_FILE) or {}
            
            # Update styles
            new_styles = [style for style in song_data['styles'] if style not in all_styles]
            if new_styles:
                all_styles.extend(new_styles)
                save_json(all_styles, STYLES_FILE)
            
            # Update style mapping
            song_styles_mapping[song_data['song_url']] = song_data['styles']
            save_json(song_styles_mapping, SONG_STYLES_MAPPING_FILE)
            
            # Update meta tags
            meta_tags = extract_meta_tags(song_data['lyrics'])
            new_meta_tags = [tag for tag in meta_tags if tag not in all_meta_tags]
            if new_meta_tags:
                all_meta_tags.extend(new_meta_tags)
                save_json(all_meta_tags, META_TAGS_FILE)
            
            # Update meta mapping
            song_meta_mapping[song_data['song_url']] = meta_tags
            save_json(song_meta_mapping, SONG_META_MAPPING_FILE)

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
