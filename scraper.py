import requests
import json
import time
from bs4 import BeautifulSoup

class DiscourseScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.scraped_data = []
    
    def scrape_topics(self, category_id=5, max_pages=10):
        """Scrape topics from a Discourse category"""
        for page in range(max_pages):
            try:
                url = f"{self.base_url}/c/{category_id}.json?page={page}"
                response = requests.get(url)
                
                if response.status_code != 200:
                    break
                    
                data = response.json()
                topics = data.get('topic_list', {}).get('topics', [])
                
                if not topics:
                    break
                
                for topic in topics:
                    topic_data = self.scrape_topic_posts(topic['id'])
                    if topic_data:
                        self.scraped_data.append({
                            'id': topic['id'],
                            'title': topic['title'],
                            'posts': topic_data
                        })
                
                time.sleep(1)  # Be respectful to the server
                
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                break
    
    def scrape_topic_posts(self, topic_id):
        """Scrape all posts from a specific topic"""
        try:
            url = f"{self.base_url}/t/{topic_id}.json"
            response = requests.get(url)
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            posts = []
            
            for post in data.get('post_stream', {}).get('posts', []):
                posts.append({
                    'username': post.get('username', ''),
                    'content': post.get('cooked', ''),
                    'created_at': post.get('created_at', ''),
                    'post_number': post.get('post_number', 0)
                })
            
            return posts
            
        except Exception as e:
            print(f"Error scraping topic {topic_id}: {e}")
            return None
    
    def save_data(self, filename='discourse_data.json'):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename}")

# Usage
if __name__ == "__main__":
    scraper = DiscourseScraper("https://discourse.onlinedegree.iitm.ac.in")
    scraper.scrape_topics()
    scraper.save_data()
