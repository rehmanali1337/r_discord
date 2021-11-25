import aiohttp
import json
import pickle
import requests
import os
from .errors import *
from .http import json_or_text


def get_headers(cookies: str,
                token: str,
                path,
                referer: str = "https://discord.com/channels/@me",
                method="POST",
                user_agent=None,
                content_length=None, ):
    if user_agent is None:
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    _headers = {
        'authority': 'discord.com',
        'method': method,
        'path': path,
        'scheme': 'https',
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'en-US',
        'authorization': token,
        'content-length': str(content_length),
        'content-type': 'application/json',
        'cookie': cookies,
        'origin': 'https://discord.com',
        'referer': referer,
        'sec-ch-ua': '";Not A Brand";v="99", "Chromium";v="94"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': user_agent,
        # 'x-context-properties': default_x_context_properties,
        # 'x-fingerprint': self._fingerprint,
        'x-debug-options': 'bugReporterEnabled',
        'x-super-properties': 'eyJvcyI6IkxpbnV4IiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzk0LjAuNDYwNi44MSBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiOTQuMC40NjA2LjgxIiwib3NfdmVyc2lvbiI6IiIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoxMDIxMTMsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
    }
    if content_length is None:
        del _headers['content-length']

    return _headers


class Web:
    def __init__(self, token, proxy=None):
        self._session: aiohttp.ClisntSession = None
        assert not token is None
        self._token = token
        self._base_url = 'https://discord.com'
        self._proxy = proxy
        self._data_dir = "tokens_data"
        self._data_file = f"{self._data_dir}/{self._token}"
        os.makedirs(self._data_dir, exist_ok=True)
        self._fingerprint = self._get_fingerprint()
        self._cookies = self._get_cookies()

    def _dump_to_file(self, obj, file):
        with open(file, 'wb') as f:
            pickle.dump(obj, f)

    def _read_file(self, file):
        if os.path.exists(file):
            with open(file, 'rb') as f:
                return pickle.load(f)

    def _get_client_uuid(self):
        return "RnDCQ4iPjgzBjkP3QGqv3XwBAAACAAAA"

    def _get_fingerprint(self):
        fingerprint_file = f'{self._data_file}_fingerprint'
        fingerprint = self._read_file(fingerprint_file)
        if fingerprint is None:
            res = requests.get("https://discord.com/api/v9/experiments")
            try:
                fingerprint = res.json()["fingerprint"]
            except KeyError:
                print("Could not fetch fingerprint from network! Trying once again")
                return self._get_fingerprint()
            self._dump_to_file(fingerprint, fingerprint_file)
        return fingerprint

    def _get_cookies(self):
        cookies_file = f'{self._data_file}_cookies'
        cookies = self._read_file(cookies_file)
        if cookies is None:
            res = requests.get("https://discord.com/login")
            cookies = f"__dcfduid={res.cookies.get_dict()['__dcfduid']}; __sdcfduid={res.cookies.get_dict()['__sdcfduid']}"
            self._dump_to_file(cookies, cookies_file)
        return cookies

    def _generate_headers(self, method="POST", path="/api/v9/science",
                          content_length=None, referer="https://discord.com/channels/@me",
                          x_context_properties=None, user_agent=None, x_fingerprint=None) -> dict:
        default_x_context_properties = "eyJsb2NhdGlvbiI6IkpvaW4gR3VpbGQiLCJsb2NhdGlvbl9ndWlsZF9pZCI6Ijc1NzkzNjgzNjc3NjY4OTcwNCIsImxvY2F0aW9uX2NoYW5uZWxfaWQiOiI4ODI3NTcwODI0NjAzMjM4NzAiLCJsb2NhdGlvbl9jaGFubmVsX3R5cGUiOjB9"
        if user_agent is None:
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
        headers = {
            'authority': 'discord.com',
            'method': method,
            'path': path,
            'scheme': 'https',
            'accept': '*/*',
            'accept-encoding': 'gzip, deflate',
            'accept-language': 'en-US',
            'authorization': self._token,
            'content-length': str(content_length),
            'content-type': 'application/json',
            'cookie': self._cookies,
            'origin': 'https://discord.com',
            'referer': referer,
            'sec-ch-ua': '";Not A Brand";v="99", "Chromium";v="94"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': user_agent,
            'x-context-properties': default_x_context_properties,
            'x-fingerprint': self._fingerprint,
            'x-debug-options': 'bugReporterEnabled',
            'x-super-properties': 'eyJvcyI6IkxpbnV4IiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJlbi1VUyIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChYMTE7IExpbnV4IHg4Nl82NCkgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzk0LjAuNDYwNi44MSBTYWZhcmkvNTM3LjM2IiwiYnJvd3Nlcl92ZXJzaW9uIjoiOTQuMC40NjA2LjgxIiwib3NfdmVyc2lvbiI6IiIsInJlZmVycmVyIjoiIiwicmVmZXJyaW5nX2RvbWFpbiI6IiIsInJlZmVycmVyX2N1cnJlbnQiOiIiLCJyZWZlcnJpbmdfZG9tYWluX2N1cnJlbnQiOiIiLCJyZWxlYXNlX2NoYW5uZWwiOiJzdGFibGUiLCJjbGllbnRfYnVpbGRfbnVtYmVyIjoxMDIxMTMsImNsaWVudF9ldmVudF9zb3VyY2UiOm51bGx9'
        }
        if content_length is None:
            del headers['content-length']
        if x_context_properties is None:
            del headers['x-context-properties']
        return headers

    async def _make_request(self, path, headers: dict, payload: str, method="POST"):
        url = f"{self._base_url}{path}"
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.request(method, url=url, data=payload, proxy=self._proxy) as response:
                await response.read()
                if response.status > 200 and response.status < 300:
                    return response
                data = await json_or_text(response)
                if response.status == 403:
                    raise Forbidden(response, data)
                elif response.status == 404:
                    raise NotFound(response, data)
                elif response.status == 503:
                    raise DiscordServerError(response, data)
                else:
                    raise HTTPException(response, data)

    async def join_server(self, invite_code):
        invite_code = invite_code.split('/')[-1]
        payload = {}
        path = f"/api/v9/invites/{invite_code}"
        headers = self._generate_headers(path=path, content_length="2")
        response = await self._make_request(path, headers, payload=json.dumps(payload))
        return await response.json()
