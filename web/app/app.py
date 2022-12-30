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
from fastapi import FastAPI, Header, Request, HTTPException
from hmac import HMAC, compare_digest
from hashlib import sha256
import requests, json
from enum import auto
from fastapi_utils.enums import StrEnum


class Mode(StrEnum):
	link = auto()
	fulltext = auto()




import sentry_sdk


sentry_sdk.init(
	traces_sample_rate=1.0,
)


app = FastAPI()



from prometheus_fastapi_instrumentator import Instrumentator, metrics

instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=False,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=[".*admin.*", "/metrics"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app)
instrumentator.expose(app, include_in_schema=False, should_gzip=True)



def verify_signature(x_hub_signature_256, body):
	if x_hub_signature_256 is None: 
		raise HTTPException(403, 'X-Hub-Signature-256 missing')
	received_sign = x_hub_signature_256.split('sha256=')[-1].strip()
	expected_sign = HMAC(key=github_secret.encode(), msg=body, digestmod=sha256).hexdigest()
	if not compare_digest(received_sign, expected_sign):
		raise HTTPException(403, 'X-Hub-Signature-256 invalid')


@app.post('/discord/{mode}')
async def webhook(mode:Mode, request: Request, x_hub_signature_256: Union[str, None] = Header(default=None)):

	verify_signature(x_hub_signature_256, memoryview(await request.body()))
	r = await request.json()
	print(json.dumps(r, sort_keys=True, indent=4))
	
	pushed_commits_diff_url = r['compare'] # || die
	
	message = '<' + pushed_commits_diff_url + '>'
	if mode == 'fulltext':
		message += '\n```' + requests.get(pushed_commits_diff_url + '.diff').text + '```'
	print(f'sending: {message}')
	send_message(message)
	return 'OK'


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0


def send_message(message):
	payload = {'content': message}
	requests.post(discord_webhook_url, json=payload)

