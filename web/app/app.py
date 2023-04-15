"""
listen for github webhook and send commit body to discord webhook

secrets/DISCORD_WEBHOOK_URL :
server settings -> integrations -> webhooks -> new webhook -> webhook url

secrets/GITHUB_SECRET :
Webhooks -> add webhook -> 
Payload URL: <your server>/discord_fulltext
Content type: application/json
Secret: GITHUB_SECRET



"""




from typing import Union
from fastapi import FastAPI, Header, Request, HTTPException
from hmac import HMAC, compare_digest
from hashlib import sha256
import requests, json
from enum import auto
from fastapi_utils.enums import StrEnum
import os, logging


def secret(name):
	fn = os.environ.get('SECRETS_DIR','/run/secrets') + '/' + name
	with open(fn, 'r') as x:
		return x.read()


class Mode(StrEnum):
	link = auto()
	fulltext = auto()







# really curious if this will work
#os.environ['SENTRY_DSN'] = secret('SENTRY_DSN')
#import sentry_sdk
#sentry_sdk.init(
#	traces_sample_rate=1.0,
#)







app = FastAPI(debug=True)

#gunicorn_logger = logging.getLogger('gunicorn.error')
#app.logger.handlers = gunicorn_logger.handlers

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
	expected_sign = HMAC(key=secret('GITHUB_SECRET').encode(), msg=body, digestmod=sha256).hexdigest()
	if not compare_digest(received_sign, expected_sign):
		raise HTTPException(403, 'X-Hub-Signature-256 invalid')


@app.post('/discord/{mode}')
async def webhook(mode:Mode, request: Request, x_hub_signature_256: Union[str, None] = Header(default=None)):

	verify_signature(x_hub_signature_256, memoryview(await request.body()))
	r = await request.json()
	print(json.dumps(r, sort_keys=True, indent=4))
	
	pushed_commits_diff_url = r['compare'] # || die	
	message = '\n'#'<' + pushed_commits_diff_url + '>'

	if True:#mode == 'fulltext':
		diff = requests.get(pushed_commits_diff_url + '.diff').text
		diff2 = '\n'.join([l for l in diff.splitlines() if (l.startswith('-') or l.startswith('+'))])
		msgs = '\n'.join(['<'+c['url']+'>' + '\n' + c['message'] for c in r['commits']])
		message += '\n' + msgs + '\n\n```' + diff2 + '```'

	print(f'sending: {message}')
	send_message(message)
	return 'OK'


@app.get('/spam/{secret_token}/{message:path}')
async def webhook(secret_token: str, message: str):
#	print((secret('SPAM_SECRET'), secret_token))
	if secret('SPAM_SECRET') == secret_token:
		print(f'sending: {message}')
		send_message(message)
		return 'OK'

@app.get('/spam2/{message:path}')
async def webhook2(message: str):
	print(f'{message}')
	return 'OK'


@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0


def send_message(message):
	payload = {'content': message}
	requests.post(secret('DISCORD_WEBHOOK_URL'), json=payload)

