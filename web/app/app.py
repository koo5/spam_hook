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


from typing import Union
from fastapi import FastAPI, Header, Request
from hmac import HMAC, compare_digest
from hashlib import sha256
import requests


def verify_signature(x_hub_signature_256, body):
	received_sign = x_hub_signature_256.split('sha256=')[-1].strip()
	expected_sign = HMAC(key=github_secret.encode(), msg=body, digestmod=sha256).hexdigest()
	return compare_digest(received_sign, expected_sign)


app = FastAPI()

@app.post('/discord/{mode}')
async def webhook(mode, request: Request, x_hub_signature_256: Union[str, None] = Header(default=None)):

	if not verify_signature(x_hub_signature_256, memoryview(await request.body())):
		return 'Forbidden', 403
	r = await request.json()
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


