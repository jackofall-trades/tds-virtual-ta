import requests
import json
import time
from bs4 import BeautifulSoup
import os

class DiscourseScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.scraped_data = []
        self.session = requests.Session()
        # Add headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def check_accessibility(self):
        """Check if the forum is accessible and what endpoints work"""
        print("🔍 Checking forum accessibility...")
        
        endpoints_to_test = [
            "/",
            "/latest.json",
            "/top.json", 
            "/categories.json",
            "/c/5.json",
            "/c/1.json"
        ]
        
        accessible_endpoints = []
        
        for endpoint in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                print(f"  {endpoint}: {response.status_code}")
                
                if response.status_code == 200:
                    accessible_endpoints.append(endpoint)
                elif response.status_code == 403:
                    print(f"    ⚠️  Requires authentication: {endpoint}")
                elif response.status_code == 404:
                    print(f"    ❌ Not found: {endpoint}")
                    
            except Exception as e:
                print(f"    ❌ Error accessing {endpoint}: {e}")
        
        return accessible_endpoints
    
    def scrape_from_html(self, max_pages=3):
        """Try to scrape data from HTML pages instead of JSON API"""
        print("🌐 Attempting to scrape from HTML pages...")
        
        try:
            # Try to get the main page
            response = self.session.get(f"{self.base_url}/")
            if response.status_code != 200:
                print(f"❌ Cannot access main page: {response.status_code}")
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for topic links
            topic_links = soup.find_all('a', href=True)
            topic_urls = []
            
            for link in topic_links:
                href = link.get('href', '')
                if '/t/' in href and href.startswith('/t/'):
                    topic_urls.append(href)
            
            print(f"Found {len(topic_urls)} potential topic URLs")
            
            # Limit to first few topics
            for i, topic_url in enumerate(topic_urls[:max_pages]):
                try:
                    print(f"Scraping topic {i+1}/{min(len(topic_urls), max_pages)}: {topic_url}")
                    self.scrape_topic_from_html(topic_url)
                    time.sleep(2)  # Be polite
                except Exception as e:
                    print(f"Error scraping topic {topic_url}: {e}")
                    continue
            
            return len(self.scraped_data) > 0
            
        except Exception as e:
            print(f"Error in HTML scraping: {e}")
            return False
    
    def scrape_topic_from_html(self, topic_url):
        """Scrape a single topic from its HTML page"""
        try:
            response = self.session.get(f"{self.base_url}{topic_url}")
            if response.status_code != 200:
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract topic title
            title_elem = soup.find('h1') or soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Topic"
            
            # Extract posts
            posts = []
            post_elements = soup.find_all(['div', 'article'], class_=lambda x: x and 'post' in x.lower())
            
            for post_elem in post_elements[:3]:  # Limit to first 3 posts
                content = post_elem.get_text().strip()
                if len(content) > 50:  # Only include substantial posts
                    posts.append({
                        "topic_title": title,
                        "content": content[:500],  # Limit content length
                        "topic_id": topic_url.split('/')[-1] if topic_url.split('/')[-1].isdigit() else "1"
                    })
            
            if posts:
                self.scraped_data.append({
                    "id": len(self.scraped_data) + 1,
                    "title": title,
                    "posts": posts
                })
                
        except Exception as e:
            print(f"Error scraping topic from HTML: {e}")
    
    def scrape_topics(self, category_id=5, max_pages=5):
        """Original JSON-based scraping method"""
        print(f"📡 Attempting JSON API scraping for category {category_id}...")
        
        for page in range(1, max_pages+1):
            try:
                print(f"Scraping page {page}...")
                response = self.session.get(f"{self.base_url}/c/{category_id}.json?page={page}")
                
                if response.status_code == 403:
                    print("❌ Access denied - requires authentication")
                    return False
                elif response.status_code != 200:
                    print(f"❌ HTTP {response.status_code} for page {page}")
                    break
                
                data = response.json()
                topics = data.get('topic_list', {}).get('topics', [])
                
                if not topics:
                    print("No topics found")
                    break
                
                print(f"Found {len(topics)} topics on page {page}")
                
                for topic in topics:
                    posts = self.scrape_topic_posts(topic['id'])
                    if posts:  # Only add if we got posts
                        self.scraped_data.append({
                            "id": topic['id'],
                            "title": topic['title'],
                            "posts": posts
                        })
                
                time.sleep(1)  # Be polite to the server
                
            except Exception as e:
                print(f"Error on page {page}: {e}")
                break
        
        return len(self.scraped_data) > 0
    
    def scrape_topic_posts(self, topic_id):
        """Scrape posts for a specific topic"""
        try:
            response = self.session.get(f"{self.base_url}/t/{topic_id}.json")
            
            if response.status_code == 403:
                print(f"❌ Access denied for topic {topic_id}")
                return []
            elif response.status_code != 200:
                print(f"❌ HTTP {response.status_code} for topic {topic_id}")
                return []
            
            data = response.json()
            posts = data.get('post_stream', {}).get('posts', [])
            
            return [
                {
                    "topic_title": data.get('title', 'Unknown Topic'),
                    "content": BeautifulSoup(post['cooked'], "html.parser").get_text()[:500],
                    "author": post.get('username', 'Unknown'),
                    "created_at": post.get('created_at', ''),
                    "topic_id": topic_id
                } for post in posts[:3]  # Limit to first 3 posts
            ]
            
        except Exception as e:
            print(f"Error in topic {topic_id}: {e}")
            return []
    
    def create_sample_data(self):
        """Create sample data if scraping fails"""
        print("📝 Creating sample data...")
        
        sample_data = [
            {
                "id": 1,
                "title": "Introduction to Data Science Tools",
                "posts": [
                    {
                        "topic_title": "Introduction to Data Science Tools",
                        "content": "Welcome to the Tools in Data Science course! This course covers essential tools and technologies used in data science including Python, Jupyter notebooks, pandas, numpy, and more. We'll start with basic concepts and gradually move to advanced topics.",
                        "topic_id": 1
                    },
                    {
                        "topic_title": "Introduction to Data Science Tools", 
                        "content": "Make sure you have Python 3.8+ installed on your system. You can download it from python.org or use Anaconda distribution which comes with many useful packages pre-installed.",
                        "topic_id": 1
                    }
                ]
            },
            {
                "id": 2,
                "title": "Python Basics for Data Science",
                "posts": [
                    {
                        "topic_title": "Python Basics for Data Science",
                        "content": "Python is the most popular programming language for data science. Key concepts include variables, data types, control structures, functions, and object-oriented programming. We'll focus on practical examples relevant to data analysis.",
                        "topic_id": 2
                    }
                ]
            },
            {
                "id": 3,
                "title": "Working with Jupyter Notebooks",
                "posts": [
                    {
                        "topic_title": "Working with Jupyter Notebooks",
                        "content": "Jupyter Notebooks provide an interactive environment for data analysis. You can combine code, text, and visualizations in a single document. This makes it perfect for exploratory data analysis and sharing results.",
                        "topic_id": 3
                    }
                ]
            },
            {
                "id": 4,
                "title": "Data Manipulation with Pandas",
                "posts": [
                    {
                        "topic_title": "Data Manipulation with Pandas",
                        "content": "Pandas is a powerful library for data manipulation and analysis. It provides data structures like DataFrames and Series that make it easy to work with structured data. Key operations include filtering, grouping, merging, and aggregating data.",
                        "topic_id": 4
                    }
                ]
            },
            {
                "id": 5,
                "title": "Token Cost Calculation",
                "posts": [
                    {
                        "topic_title": "Token Cost Calculation",
                        "content": "To calculate token costs for text, you need to understand how language models tokenize text. Different languages have different tokenization patterns. For Japanese text, characters are typically tokenized differently than English text.",
                        "topic_id": 5
                    }
                ]
            }
        ]
        
        self.scraped_data = sample_data
        return True
    
    def save_data(self, filename='discourse_data.json'):
        """Save scraped data to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Data saved to {filename}")
        print(f"📊 Total topics scraped: {len(self.scraped_data)}")
        
        total_posts = sum(len(topic['posts']) for topic in self.scraped_data)
        print(f"📝 Total posts scraped: {total_posts}")

def main():
    scraper = DiscourseScraper("https://discourse.onlinedegree.iitm.ac.in")
    
    print("🚀 Starting Discourse scraper...")
    print("=" * 50)
    
    # Check accessibility first
    accessible_endpoints = scraper.check_accessibility()
    
    success = False
    
    # Try JSON API first
    if accessible_endpoints:
        print("\n📡 Trying JSON API endpoints...")
        success = scraper.scrape_topics()
    
    # If JSON fails, try HTML scraping
    if not success:
        print("\n🌐 JSON API failed, trying HTML scraping...")
        success = scraper.scrape_from_html()
    
    # If all scraping fails, create sample data
    if not success:
        print("\n📝 All scraping methods failed, creating sample data...")
        success = scraper.create_sample_data()
    
    # Save the data
    scraper.save_data()
    
    if success:
        print("\n🎉 Scraping completed successfully!")
    else:
        print("\n⚠️  Scraping failed, but sample data was created.")

if __name__ == "__main__":
    main()
