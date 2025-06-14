import requests
import json
import time
from bs4 import BeautifulSoup

class DiscourseScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.scraped_data = []
    
    def scrape_topics(self, category_id=5, max_pages=5):
        for page in range(1, max_pages+1):
            try:
                print(f"Scraping page {page}...")
                response = requests.get(f"{self.base_url}/c/{category_id}.json?page={page}")
                if response.status_code != 200:
                    break
                
                topics = response.json().get('topic_list', {}).get('topics', [])
                if not topics:
                    break
                
                for topic in topics:
                    posts = self.scrape_topic_posts(topic['id'])
                    self.scraped_data.append({
                        "id": topic['id'],
                        "title": topic['title'],
                        "posts": posts
                    })
                
                time.sleep(1)  # Be polite to the server
                
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
    
    def scrape_topic_posts(self, topic_id):
        try:
            response = requests.get(f"{self.base_url}/t/{topic_id}.json")
            return [
                {
                    "content": BeautifulSoup(post['cooked'], "html.parser").get_text(),
                    "author": post['username'],
                    "created_at": post['created_at']
                } for post in response.json().get('post_stream', {}).get('posts', [])
            ]
        except Exception as e:
            print(f"Error in topic {topic_id}: {e}")
            return []
    
    def save_data(self, filename='discourse_data.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Data saved to {filename}")

if __name__ == "__main__":
    scraper = DiscourseScraper("https://discourse.onlinedegree.iitm.ac.in")
    scraper.scrape_topics()
    scraper.save_data()
