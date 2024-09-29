# NepaliCorpusCrawler

A Python crawler to collect Nepali news from Nepali News Websites. 

**Supports**:
- **Pause/Resume:** Save and continue crawling seamlessly.
- **Language Detection:** Extracts and saves only Nepali text.
- **Data Cleaning:** Cleans extracted text to retain relevant characters.
- **Text Files:** Creates a new `.txt` file for each crawled page, which can be merged or used individually.


## Installation

1. **Clone the Repository:**
   `git clone https://github.com/bibekplus/NepaliCorpusCrawler.git`
   `cd NepaliCorpusCrawler`

2. **Create a Virtual Environment:**
   `python3 -m venv .venv`

3. **Activate the Virtual Environment:**
   - On Unix or MacOS:
     `source .venv/bin/activate`
   - On Windows:
     `.venv\Scripts\activate`

4. **Install Dependencies:**
   `pip install -r requirements.txt`

## Usage

- **Start a New Crawl:**
  `python nepali-news-downloader.py`

- **Resume a Paused Crawl:**
  `python nepali-news-downloader.py --resume`

- **Specify a Custom State File:**
  `python nepali-news-downloader.py --resume --state-file my_state.pkl`

- **Enable Verbose Logging:**
  Modify the `VERBOSE` variable in the script to `True` for detailed logs.

- **Adjust Crawling Parameters:**
  Edit `MAX_PAGES` and `MAX_DEPTH` in the script to control the crawl scope.

## Understanding Crawled vs. Saved Pages

- **Crawled Pages:** These are the total number of pages the crawler visits during its operation. Not all crawled pages contain Nepali text.

- **Saved Pages:** These are the pages from which Nepali text has been successfully extracted and saved as `.txt` files.

- **`MAX_PAGES`:** This parameter sets the maximum number of **saved pages**. The crawler may crawl more pages to find the required number of pages with Nepali content.


## Disclaimer


**WARNING**: This script is intended for educational and research purposes only.
I do not own any news websites used in the examples. Please ensure you have permission to crawl and scrape data from the website. Always respect the website's robots.txt and adhere to their crawling policies.


