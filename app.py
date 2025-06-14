from flask import Flask, request, jsonify
import json
import base64
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

class VirtualTA:
    def __init__(self):
        self.knowledge_base = self.load_knowledge_base()
        # Set your OpenAI API key in .env file
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 
    
    def load_knowledge_base(self):
        """Load scraped discourse data"""
        try:
            with open('discourse_data.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def search_relevant_content(self, question):
        """Find relevant content from knowledge base"""
        relevant_posts = []
        question_lower = question.lower()
        
        for topic in self.knowledge_base:
            # Simple keyword matching (you can improve this)
            if any(word in topic['title'].lower() for word in question_lower.split()):
                for post in topic['posts'][:3]:  # Take first 3 posts
                    relevant_posts.append({
                        'content': post['content'],
                        'topic_title': topic['title'],
                        'topic_id': topic['id']
                    })
        
        return relevant_posts[:5]  # Return top 5 relevant posts
    
    def generate_answer(self, question, image=None):
        """Generate answer using OpenAI and knowledge base"""
        relevant_content = self.search_relevant_content(question)
        
        # Create context from relevant posts
        context = "\n\n".join([
            f"Topic: {post['topic_title']}\nContent: {post['content']}"
            for post in relevant_content
        ])
        
        prompt = f"""
        You are a Teaching Assistant for the Tools in Data Science course at IIT Madras.
        
        Context from course discussions:
        {context}
        
        Student Question: {question}
        
        Please provide a helpful answer based on the context. If the context doesn't contain enough information, use your knowledge about data science tools.
        Keep the answer concise and practical.
        """
        
        try:
            # Use OpenAI to generate answer
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            answer = response.choices[0].message.content
            
            # Create links from relevant content
            links = []
            for post in relevant_content[:2]:
                links.append({
                    "url": f"https://discourse.onlinedegree.iitm.ac.in/t/{post['topic_id']}",
                    "text": post['topic_title'][:100]
                })
            
            return {
                "answer": answer,
                "links": links
            }
            
        except Exception as e:
            return {
                "answer": "I'm sorry, I couldn't generate an answer at the moment. Please try again later.",
                "links": []
            }

# Initialize the Virtual TA
virtual_ta = VirtualTA()

@app.route('/api/', methods=['POST'])
def answer_question():
    try:
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({"error": "Question is required"}), 400
        
        question = data['question']
        image = data.get('image', None)  # Base64 encoded image
        
        # Generate answer
        result = virtual_ta.generate_answer(question, image)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "error": "Internal server error",
            "answer": "I'm sorry, I encountered an error processing your question.",
            "links": []
        }), 500

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "TDS Virtual TA is running!"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
