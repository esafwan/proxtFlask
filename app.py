from flask import Flask, request, send_file, jsonify
import requests
import os
import random
import tldextract
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup

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
    live = request.args.get('live', 'false').lower() == 'true'

    if not target_url:
        return "Missing URL", 400

    headers = {'User-Agent': random.choice(user_agents)}
    response = requests.get(target_url, headers=headers)

    if not live:
        # Parse the HTML content and extract the body tag
        soup = BeautifulSoup(response.content, 'html.parser')
        body_content = soup.find('body')

        if body_content:
            return body_content.get_text(), {'Content-Type': 'text/plain'}
        else:
            return "No body tag found", 400

    # The rest of the code is executed if live is true
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



@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json
    sender = data.get('sender')
    recipient = data.get('recipient')
    subject = data.get('subject')
    body = data.get('body')

    message = Mail(
        from_email=sender,
        to_emails=recipient,
        subject=subject,
        html_content=body
    )

    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return jsonify({'status_code': response.status_code, 'body': response.body, 'headers': response.headers})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/send-smtp-email', methods=['POST'])
def send_smtp_email():
    data = request.json
    sender = data.get('sender')
    recipient = data.get('recipient')
    subject = data.get('subject')
    body = data.get('body')

    # Set up the MIME
    message = MIMEMultipart()
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # SMTP details
    # SMTP details for SendGrid
    smtp_server = "smtp.sendgrid.net"
    smtp_port = 587  # You can also use 25 for unencrypted/TLS connections or 465 for SSL connections
    smtp_username = "apikey"
    smtp_password = os.environ.get('SENDGRID_API_KEY')


    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender, recipient, message.as_string())
        return jsonify({'message': 'Email sent successfully'})
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)
