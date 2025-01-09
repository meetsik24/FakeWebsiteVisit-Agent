import requests
import time
import random
from datetime import datetime
import logging
from fake_useragent import UserAgent
import concurrent.futures
from logging.handlers import RotatingFileHandler

# Configure logging with rotation
logging.basicConfig(
    handlers=[RotatingFileHandler('web_visits.log', maxBytes=5 * 1024 * 1024, backupCount=3)],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class WebsiteVisitor:
    def __init__(self, url, visit_interval=(30, 120), max_concurrent=3):
        """
        Initialize the WebsiteVisitor class.

        :param url: The URL to visit.
        :param visit_interval: Tuple of (min, max) seconds between visits.
        :param max_concurrent: Maximum number of concurrent visits.
        """
        self.url = url
        self.visit_interval = visit_interval
        self.max_concurrent = max_concurrent
        self.user_agent = UserAgent()
        self.session = requests.Session()

    def _get_headers(self):
        """Generate random headers to simulate different browsers."""
        try:
            user_agent = self.user_agent.random
        except Exception:
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " \
                         "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        return {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def single_visit(self):
        """Make a single visit to the website."""
        try:
            response = self.session.get(self.url, headers=self._get_headers(), timeout=10)
            if response.status_code == 200:
                logging.info(f"Successfully visited {self.url}")
                return True
            elif response.status_code == 429:
                logging.warning("429 Too Many Requests. Backing off for 5 minutes.")
                time.sleep(300)
                return False
            else:
                logging.warning(f"Failed to visit {self.url}. Status code: {response.status_code}")
                return False
        except requests.RequestException as e:
            logging.error(f"Error visiting {self.url}: {e}")
            return False

    def _visit_batch(self):
        """
        Visit the website in a batch using concurrent threads.
        :return: Tuple of (successful_visits, failed_visits).
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            results = list(executor.map(lambda _: self.single_visit(), range(self.max_concurrent)))
        return results.count(True), results.count(False)

    def run_visitor(self, max_visits=None):
        """
        Run the visitor continuously with optional maximum visits.
        
        :param max_visits: Maximum number of visits to make. If None, runs indefinitely.
        :return: Tuple of (total successful visits, total errors).
        """
        visit_count = 0
        error_count = 0

        while max_visits is None or visit_count < max_visits:
            try:
                successes, errors = self._visit_batch()
                visit_count += successes
                error_count += errors
                delay = random.uniform(*self.visit_interval)
                logging.info(f"Waiting for {delay:.2f} seconds before the next batch.")
                time.sleep(delay)
            except Exception as e:
                logging.error(f"Error in visitor loop: {e}")
                time.sleep(60)

            if visit_count > 0 and visit_count % 100 == 0:
                logging.info(f"Progress: {visit_count} visits completed with {error_count} errors.")

        logging.info(f"Completed {visit_count} visits with {error_count} errors.")
        return visit_count, error_count


# Example usage
if __name__ == "__main__":
    visitor = WebsiteVisitor(
        url="https://www.meetpay.africa",
        visit_interval=(45, 180),  # Random interval between 45 and 180 seconds
        max_concurrent=3  # Maximum concurrent visits
    )
    
    # Run the visitor with a limit of 500 visits
    total_visits, total_errors = visitor.run_visitor(max_visits=500)
    print(f"Completed {total_visits} visits with {total_errors} errors.")