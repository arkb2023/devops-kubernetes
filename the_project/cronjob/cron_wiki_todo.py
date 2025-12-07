import requests
import os

url = "https://en.wikipedia.org/wiki/Special:Random"
headers = {
    "User-Agent": "Mozilla/5.0 (compatible; MyCronJob/1.0; +http://yourdomain.com)"
}

response = requests.get(url, headers=headers, allow_redirects=False)

if "Location" in response.headers:
    wiki_url = response.headers["Location"]
    todo_text = f"Read {wiki_url}"
    print(f"todo text: {todo_text}")
    # fix: FQDN with project name wont work in multi branch deployment setup!
    #TODO_API_URL = os.getenv("TODO_API_URL", "http://todo-backend-svc.project.svc.cluster.local:4567/todos/")
    TODO_API_URL = os.getenv("TODO_API_URL", "http://todo-backend-svc:4567/todos/")
    
    post_response = requests.post(TODO_API_URL, json={"text": todo_text})
    
    print(f"Created todo: Read {wiki_url}, Response status: {post_response.status_code}")
else:
    print(f"No redirect Location header, status code: {response.status_code}")
