"""
listen for github webhook and send commit body to discord webhook
"""


import os



# settings

# server settings -> integrations -> webhooks -> new webhook -> copy webhook url
discord_webhook_url =  os.environ['DISCORD_WEBHOOK_URL']

# Webhooks -> add webhook -> 
#	Payload URL: <your server>/discord_fulltext
#	Content type: application/json
#	Secret: GITHUB_SECRET
github_secret = os.environ['GITHUB_SECRET']


from flask import Flask, request
from hmac import HMAC, compare_digest
from hashlib import sha256
import requests


def verify_signature(req):
	received_sign = req.headers.get('X_Hub_Signature_256').split('sha256=')[-1].strip()
	expected_sign = HMAC(key=github_secret.encode(), msg=req.data, digestmod=sha256).hexdigest()
	return compare_digest(received_sign, expected_sign)


app = Flask(__name__)

@app.route('/discord/<mode>', methods=['POST'])
def webhook(mode):
	if not verify_signature(request):
		return 'Forbidden', 403
	#if urlencoded: #print(request.get_data())
	r = request.get_json()
	print(r)
	
	pushed_commits_diff_url = r['compare'] # || die
	
	message = '<' + pushed_commits_diff_url + '>'
	if mode == 'fulltext':
		message += '\n```' + requests.get(pushed_commits_diff_url + '.diff').text + '```'
	print(f'sending: {message}')
	send_message(message)
	return 'OK'


def send_message(message):
	payload = {'content': message}
	requests.post(discord_webhook_url, json=payload)


