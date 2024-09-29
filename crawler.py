import argparse
import os
import pickle
import re
import signal
import sys
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from langdetect import detect
from tqdm import tqdm


# -----------------------------------------------------------------------------
# WARNING:
# This script is intended for educational and research purposes only.
# I do not own https://www.nepalpress.com/ or any news websites used in the 
# examples. Please ensure you have permission to crawl and scrape data from
#  the website. Always respect the website's robots.txt and adhere to their 
# crawling policies.
# -----------------------------------------------------------------------------



# Configuration Variables
TARGET_URL = 'https://www.nepalpress.com/' #this is an example, can replace it with ekantipur, onlinekhabar, etc.
FOLDER_PATH = 'nepali_corpus_nepalpress'
MAX_PAGES = 150
MAX_DEPTH = 10  # Prevent infinite loops
VERBOSE = False  # Set to True for detailed logs

STATE_FILE_DEFAULT = 'crawler_state.pkl'
SAVE_INTERVAL = 100  # Save state every 100 pages

URL_PATTERNS = [r'https://www\.nepalpress\.com/(2023|2024)'] #this is an example

TARGET_DOMAIN = urlparse(TARGET_URL).netloc

# Initialize a session for persistent connections
session = requests.Session()
session.headers.update({'User-Agent': 'Mozilla/5.0 (compatible; NepaliCrawler/1.0)'})

# Global variable to handle graceful shutdown
shutdown_flag = False


def parse_arguments():
    parser = argparse.ArgumentParser(description="Nepali Corpus Crawler with Pause and Resume Capability")
    parser.add_argument('--resume', action='store_true', help='Resume crawling from a saved state')
    parser.add_argument('--state-file', type=str, default=STATE_FILE_DEFAULT, help='Path to the state file')
    return parser.parse_args()


def is_nepali(text):
    try:
        return detect(text) == 'ne'
    except:
        return False  # Not Nepali or undetectable


def clean_text(text):
    # Retain Nepali Unicode characters and common punctuation
    cleaned_text = re.sub(r'[^\u0900-\u097F\s।?!]', '', text)
    return cleaned_text


def normalize_url(url):
    """
    Fixes common URL formatting issues.
    """
    if re.match(r'^https?:/[^/]', url):
        # Replace 'http:/' with 'http://' or 'https:/' with 'https://'
        url = re.sub(r'^(https?:)/([^/])', r'\1//\2', url)
    return url


def matches_pattern(url, patterns):
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


def get_internal_links(current_url, base_url):
    """
    Extracts internal links from a live webpage.
    """
    try:
        response = session.get(current_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = set()

        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if not href:
                continue  # Skip empty hrefs

            # Resolve relative URLs using the base URL
            full_url = urljoin(base_url, href)
            full_url = normalize_url(full_url)
            parsed_url = urlparse(full_url)
            link_domain = parsed_url.netloc

            # Skip if the link points back to the crawler's domain
            if 'web.archive.org' in parsed_url.netloc:
                continue

            if link_domain == TARGET_DOMAIN:
                # Ensure the URL matches the desired patterns
                if matches_pattern(full_url, URL_PATTERNS):
                    links.add(full_url)

        if VERBOSE:
            print(f"Found {len(links)} internal links at {current_url}")

        return links
    except Exception as e:
        if VERBOSE:
            print(f"Error retrieving links from {current_url}: {e}")
        return set()


def extract_nepali_text_from_url(current_url):
    try:
        response = session.get(current_url, timeout=10)
        response.raise_for_status()

        # Decode response content with proper encoding
        response.encoding = response.apparent_encoding  # Guess encoding if not UTF-8
        soup = BeautifulSoup(response.content, 'html.parser')

        paragraphs = soup.find_all('p')
        nepali_texts = []

        for paragraph in paragraphs:
            text = paragraph.get_text().strip()
            if text and is_nepali(text):
                cleaned_text = clean_text(text)
                nepali_texts.append(cleaned_text)

        return " ".join(nepali_texts) if nepali_texts else None
    except Exception as e:
        if VERBOSE:
            print(f"Error processing {current_url}: {e}")
        return None


def save_text_to_file(text, folder_path, file_name):
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text)
        if VERBOSE:
            print(f"Saved: {file_path}")
    except Exception as e:
        if VERBOSE:
            print(f"Error saving file {file_path}: {e}")


def collect_initial_links(url):
    if VERBOSE:
        print(f"Getting initial links from: {url}")
    return get_internal_links(url, url)


def save_state(state_file, state):
    try:
        with open(state_file, 'wb') as f:
            pickle.dump(state, f)
        if VERBOSE:
            print(f"State saved to {state_file}")
    except Exception as e:
        print(f"Error saving state to {state_file}: {e}")


def load_state(state_file):
    try:
        with open(state_file, 'rb') as f:
            state = pickle.load(f)
        if VERBOSE:
            print(f"State loaded from {state_file}")
        return state
    except Exception as e:
        print(f"Error loading state from {state_file}: {e}")
        return None


def handle_shutdown(signum, frame):
    global shutdown_flag
    if not shutdown_flag:
        print("\nShutdown signal received. Saving state and exiting gracefully...")
        shutdown_flag = True
    else:
        print("\nAlready shutting down. Please wait...")


def create_nepali_corpus(url, folder_path, max_pages, max_depth, state_file, resume=False):
    if resume and os.path.exists(state_file):
        state = load_state(state_file)
        if state:
            queue = state['queue']
            visited = state['visited']
            page_count = state['page_count']
            crawled_pages = state['crawled_pages']
            save_progress_bar = tqdm(total=max_pages, desc="Saving", unit="page")
            save_progress_bar.update(page_count)
        else:
            print("Failed to load state. Starting fresh.")
            initial_links = collect_initial_links(url)
            queue = [(link, 1) for link in initial_links]
            visited = set()
            page_count = 0
            crawled_pages = 0
            save_progress_bar = tqdm(total=max_pages, desc="Saving", unit="page")
    else:
        initial_links = collect_initial_links(url)
        queue = [(link, 1) for link in initial_links]
        visited = set()
        page_count = 0
        crawled_pages = 0
        save_progress_bar = tqdm(total=max_pages, desc="Saving", unit="page")

    # Time tracking for crawling stats
    start_time = time.time()

    try:
        # Main crawling loop
        while page_count < max_pages and queue and not shutdown_flag:
            current_url, current_depth = queue.pop(0)

            if current_url in visited or current_depth > max_depth:
                continue

            visited.add(current_url)
            crawled_pages += 1

            elapsed_time = time.time() - start_time
            pages_per_second = crawled_pages / elapsed_time if elapsed_time > 0 else 0

            # Update progress bar description with stats
            save_progress_bar.set_postfix({
                'Crawled': f"{crawled_pages}",
                'Depth': f"{current_depth}",
                'Speed': f"{pages_per_second:.2f} p/s"
            })

            nepali_text = extract_nepali_text_from_url(current_url)

            if nepali_text and len(nepali_text.splitlines()) > 1:
                file_name = f'page_{page_count + 1}.txt'
                save_text_to_file(nepali_text, folder_path, file_name)
                page_count += 1
                save_progress_bar.update(1)

                # Save state periodically
                if page_count % SAVE_INTERVAL == 0:
                    state = {
                        'queue': queue,
                        'visited': visited,
                        'page_count': page_count,
                        'crawled_pages': crawled_pages
                    }
                    save_state(state_file, state)

            # Collect internal links for next depth
            if current_depth < max_depth:
                internal_links = get_internal_links(current_url, url)
                for link in internal_links:
                    if link not in visited:
                        queue.append((link, current_depth + 1))

            # Optional: Prevent being too aggressive
            # time.sleep(0.1)  # Sleep for 100ms between requests

    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Saving state and exiting...")
    finally:
        # Save state upon shutdown
        state = {
            'queue': queue,
            'visited': visited,
            'page_count': page_count,
            'crawled_pages': crawled_pages
        }
        save_state(state_file, state)
        save_progress_bar.close()
        total_time = time.time() - start_time
        print(f"\nSaved pages: {page_count}/{max_pages} | Crawled {crawled_pages} pages in total.")
        print(f"Total time: {total_time:.2f} seconds.")


def main():
    args = parse_arguments()
    state_file = args.state_file

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_shutdown)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, handle_shutdown)  # Handle termination

    create_nepali_corpus(
        url=TARGET_URL,
        folder_path=FOLDER_PATH,
        max_pages=MAX_PAGES,
        max_depth=MAX_DEPTH,
        state_file=state_file,
        resume=args.resume
    )


if __name__ == "__main__":
    main()
