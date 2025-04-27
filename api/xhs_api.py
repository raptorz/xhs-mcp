import asyncio
import json
import time
from collections.abc import Mapping
from urllib.parse import urlencode
import requests
from curl_cffi.requests import AsyncSession, Response

from typing import Dict
import os
import execjs
from numbers import Integral
from typing import Iterable, List, Optional, Tuple
import random
import base64

class XhsApi:
    def __init__(self,cookie):
        self._cookie=cookie
        self._base_url="https://edith.xiaohongshu.com"
        self._headers = {
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
    def init_session(self):
        return AsyncSession(
            verify=True,
            impersonate="chrome124"
        )

    def _parse_cookie(self, cookie: str) -> Dict:

        cookie_dict = {}
        if cookie:
            pairs = cookie.split(';')
            for pair in pairs:
                key, value = pair.strip().split('=', 1)
                cookie_dict[key] = value
        return cookie_dict



    async def request(self,uri: str,session=None, method="GET",headers=None,params=None,data=None) -> Dict:
        if session is None:
            session=self.init_session()
        if headers is None:
            headers = {}
        response: Response = await session.request(
            method=method,
            url=f"{self._base_url}{uri}",
            params=params,
            json=data,
            cookies=self._parse_cookie(self._cookie),
            quote=False,
            stream=True,
            headers=headers
        )


        content = await response.acontent()
        return json.loads(content)
    def base36encode(self,number: Integral, alphabet: Iterable[str] = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') -> str:

        base36 = ''
        alphabet = ''.join(alphabet)
        sign = '-' if number < 0 else ''
        number = abs(number)

        while number:
            number, i = divmod(number, len(alphabet))
            base36 = alphabet[i] + base36

        return sign + (base36 or alphabet[0])

    def search_id(self):
        e = int(time.time() * 1000) << 64
        t = int(random.uniform(0, 2147483646))
        return self.base36encode((e + t))

    def get_xs_xt(self,uri, data, cookie):
        current_directory = os.path.dirname(__file__)
        file_path = os.path.join(current_directory, "xhsvm.js")
        return execjs.compile(open(file_path, 'r', encoding='utf-8').read()).call('GetXsXt', uri, data, cookie)

    async def search_notes(self, keywords: str, limit: int = 20) -> Dict:
        data={
            "keyword":keywords,
            "page":1,
            "page_size":limit,
            "search_id":self.search_id(),
            "sort":"general",
            "note_type":0,
            "ext_flags":[],
            "geo":"",
            "image_formats":json.dumps(["jpg","webp","avif"], separators=(",", ":"))
        }
        return await self.request("/api/sns/web/v1/search/notes",method="POST",data=data)


    async def get_note_content(self, note_id: str, xsec_token: str) -> Dict:
        data = {
            "source_note_id": note_id,
            "image_formats": ["jpg","webp","avif"],
            "extra": {"need_body_topic":"1"},
            "xsec_source": "pc_feed",
            "xsec_token": xsec_token
        }
        uri="/api/sns/web/v1/feed"
        p={"uri":uri,"method":"POST","data":data}
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
        xsxt=json.loads(self.get_xs_xt(uri,data,self._cookie))
        headers['x-s']=xsxt['X-s']
        headers['x-t']=str(xsxt['X-t'])

        return await self.request(**p,headers=headers)

    async def get_note_comments(self,note_id:str,xsec_token:str) -> Dict:
        uri = '/api/sns/web/v2/comment/page'
        # 680a25a4000000001c02d251
        # ABzm9YfVyNA1hsY-KwU7ybKNWlkpb8__t-jF9FwGKzZz0=
        params = {
            'note_id': note_id,
            'cursor': '',
            'top_comment_id': '',
            'image_formats': 'jpg,webp,avif',
            'xsec_token': xsec_token
        }


        return await self.request(uri,method="GET",params=params)

    async def post_comment(self,note_id:str, comment: str) -> Dict:
        uri='/api/sns/web/v1/comment/post'
        # 680ce9d1000000001c02cb9f
        data={
            "note_id":note_id,
            "content":comment,
            "at_users":[]
        }
        headers = {
            'content-type': 'application/json;charset=UTF-8',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        }
        xsxt = json.loads(self.get_xs_xt(uri, data, self._cookie))
        headers['x-s'] = xsxt['X-s']
        headers['x-t'] = str(xsxt['X-t'])
        return await self.request(uri, method="POST",headers=headers, data=data)


