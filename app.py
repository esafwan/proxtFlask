from flask import Flask, request, send_file
import requests
import os
import random
import tldextract

app = Flask(__name__)

# List of user agents to randomize from
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    # Add more user agents as needed
]

@app.route('/')
def ping():
    return 'Hey!'


@app.route('/fetch')
def fetch_url():
    target_url = request.args.get('url')
    if not target_url:
        return "Missing URL", 400

    # Randomize user agent
    headers = {'User-Agent': random.choice(user_agents)}

    # Send request
    response = requests.get(target_url, headers=headers)

    # Extract base domain to name the folder
    ext = tldextract.extract(target_url)
    base_domain = "{}.{}".format(ext.domain, ext.suffix)

    # Ensure directory exists
    directory = os.path.join("cookies", base_domain)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Save cookies to a file
    with open(os.path.join(directory, "cookies.txt"), "w") as file:
        for cookie in response.cookies:
            file.write(f"{cookie.name}: {cookie.value}\n")

    # Return the content
    return response.content

if __name__ == '__main__':
    app.run(debug=True)
