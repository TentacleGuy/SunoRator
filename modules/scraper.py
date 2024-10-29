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
            'max': max_value,
            'label': {
                'overall': f'Gesamtfortschritt {value} / {max_value}',
                'playlist': f'Playlists {value} / {max_value}',
                'song': f'Songs in Playlist {value} / {max_value}'
            }[progress_type]
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

    def scrape_playlists(self, stop_event, log_queue, pause_event):
        playlists = load_json(SCRAPED_PLAYLISTS_FILE)
        total_songs = 0
        
        self.init_driver()

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
                    
                while pause_event.is_set():
                    time.sleep(0.1)
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

        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None  
        

    def scrape_songs(self, stop_event, log_queue, pause_event):
        self.init_driver()
        try:
            processed_song_ids = get_processed_song_ids()
            playlists = load_json(SCRAPED_PLAYLISTS_FILE)
            
            total_songs = sum(len(playlist['song_urls']) for playlist in playlists.values())
            total_playlists = len(playlists)
            
            processed_songs = 0
            current_playlist = 0

            self.emit_log(f"Found {total_songs} total songs in {total_playlists} playlists")
            self.emit_progress('overall', 0, total_songs)
            self.emit_progress('playlist', 0, total_playlists)

            for playlist_url, playlist_data in playlists.items():
                if stop_event.is_set():
                    self.emit_log("Stopping song scraping...")
                    break

                current_playlist += 1
                songs_in_playlist = len(playlist_data['song_urls'])
                current_song_in_playlist = 0
                
                self.emit_log(f"\nProcessing playlist {playlist_url} - {current_playlist}/{total_playlists}")
                self.emit_progress('playlist', current_playlist, total_playlists)
                
                for song_url in playlist_data['song_urls']:
                    if stop_event.is_set():
                        self.emit_log("Stopping song scraping...")
                        break

                    while pause_event.is_set():
                        time.sleep(0.1)
                        if stop_event.is_set():
                            break

                    current_song_in_playlist += 1
                    self.emit_progress('song', current_song_in_playlist, songs_in_playlist)

                    song_id = extract_song_id_from_url(song_url)
                    if song_id in processed_song_ids:
                        self.emit_log(f"Song {song_id} already exists -> skipping")
                        processed_songs += 1
                        self.emit_progress('overall', processed_songs, total_songs)
                        continue

                    try:
                        self.emit_log(f"Processing song {song_id}")
                        self.driver.get(song_url)
                        time.sleep(2)

                        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                        song_container = soup.find('div', class_='bg-vinylBlack-darker w-full h-full flex flex-col sm:flex-col md:flex-col lg:flex-row xl:flex-row lg:mt-8 xl:mt-8 lg:ml-32 xl:ml-32 overflow-y-scroll items-center sm:items-center md:items-center lg:items-start xl:items-start')
                        
                        if song_container:
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

                            self.save_song_data(song_data)
                            self.emit_song_info(song_data, playlist_url)
                            processed_songs += 1
                            
                            self.emit_progress('overall', processed_songs, total_songs)
                            self.emit_log(f"Successfully processed song {title}")

                    except Exception as e:
                        self.emit_log(f"Error: {str(e)}")
                        continue

                self.emit_log(f"Completed {playlist_url} {current_playlist}/{total_playlists}")

            self.emit_log("Song scraping completed")
            
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
