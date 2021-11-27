import random
import aiohttp
import json
import pickle
import requests
import os
from .errors import *
from .http import json_or_text


class Web:
    def __init__(self, token, proxy=None):
        self._session: aiohttp.ClientSession = None
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
                if response.status >= 200 and response.status < 300:
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

    async def bypass_tos(self, channel_id: str, guild_id: str, invite_code: str):
        response = await self._get_tos(channel_id, guild_id, invite_code)
        tos_details = await response.json()
        await self._accept_tos(tos_details, channel_id, guild_id)

    async def _get_tos(self, channel_id, guild_id, invite_code):
        referer = f"{self._base_url}/channel/{guild_id}/{channel_id}"
        path = f"/api/v9/guilds/{guild_id}/member-verification?with_guild=false&invite_code={invite_code}"
        headers = self._generate_headers(
            method='GET', path=path, referer=referer)
        return await self._make_request(
            path, headers, payload={}, method="GET")

    async def _accept_tos(self, tos_details, channel_id, guild_id):
        path = f"/api/v9/guilds/{guild_id}/requests/@me"
        referer = f"{self._base_url}/channel/{guild_id}/{channel_id}"
        tos_details.pop("description")
        tos_details["form_fields"][0]["response"] = True
        headers = self._generate_headers(
            method='PUT', path=path, referer=referer)
        return await self._make_request(path, headers, payload=json.dumps(tos_details), method='PUT')

    async def send_message(self, guild_id, channel_id, message):
        nonce = random.randint(900000000000000000, 999999999999999999)
        payload = {"content": message,
                   "nonce": nonce, "tts": False}
        path = f"/api/v9/channels/{channel_id}/messages"
        method = "POST"
        referer = f"https://discord.com/channels/{guild_id}/{channel_id}"

        headers = self._generate_headers(
            method=method, path=path, referer=referer)
        r = await self._make_request(path, headers, json.dumps(payload), method=method)
        return await r.json()

    async def resolve_invite(self, invite_url: str):
        code = invite_url.split("/")[-1]
        referer = f"https://discord.com/invite/{code}"
        method = "GET"
        path = f"/api/v9/invites/{code}?with_counts=true&with_expiration=true"
        headers = self._generate_headers(method=method, path=path, )
        headers["referer"] = referer
        headers["authorization"] = "undefined"
        cookies = "__dcfduid=d2ce6e202f1711eca2519feb80321749; __sdcfduid=d2ce6e212f1711eca2519feb8032174961c30b89cd31d1d337f35b6c6bb976e7e26d5024d0c59e7882f3fa392f79dc14; _ga=GA1.2.105267511.1636270904; OptanonConsent=isIABGlobal=false&datestamp=Mon+Nov+08+2021+16:18:05+GMT+0500+(Pakistan+Standard+Time)&version=6.17.0&hosts=&landingPath=NotLandingPage&groups=C0001:1,C0002:1,C0003:1&AwaitingReconsent=false"
        headers["cookie"] = cookies
        # print(headers)
        r = await self._make_request(path, headers=headers, payload=dict(), method=method)
        return await r.json()

    async def iter_messages(self, guild_id: str, channel_id: str, limit=100):
        path = f"/api/v9/channels/{channel_id}/messages?limit={limit}"
        referer = f"https://discord.com/channels/{guild_id}/{channel_id}"
        method = "GET"
        headers = self._generate_headers(
            method=method, path=path, referer=referer)
        r = await self._make_request(path, headers=headers, payload=dict(), method=method)
        messages = await r.json()
        yield messages
        if len(messages) < limit:
            return
        last_message_id = messages[-1]["id"]
        while True:
            path = f"/api/v9/channels/{channel_id}/messages?before={last_message_id}&limit={limit}"
            r = await self._make_request(path, headers=headers, payload=dict(), method=method)
            messages = await r.json()
            yield messages
            if len(messages) < limit:
                return
            last_message_id = messages[-1]["id"]
