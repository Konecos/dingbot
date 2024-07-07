#  This file is part of dingbot.
#
#  Copyright (C) 2024 Konecos
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
import time
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
import json


class DingBot:
    def __init__(self, access_token, secret):
        self.rsp = None
        self.access_token = access_token
        self.secret = secret
        self.text = ""
        self.status_code = -1
        self.errcode = -128
        self.errmsg = ""

    def _post(self, url, template):
        data = json.dumps(template).encode('utf-8')
        headers = {'Content-Type': 'application/json'}
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req) as response:
                rsp = response.read()
                self.status_code = response.getcode()
                return json.loads(rsp)
        except urllib.error.HTTPError as e:
            self.status_code = e.code
            return {"errcode": e.code, "errmsg": e.reason}
        except urllib.error.URLError as e:
            self.status_code = -1
            return {"errcode": -1, "errmsg": str(e.reason)}

    def gen_post_url(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        post_url = f"https://oapi.dingtalk.com/robot/send?access_token={self.access_token}&timestamp={timestamp}&sign={sign}"
        return post_url

    def send_pic(self, pic_url, addition_msg: str = "", atAll: bool = False):
        if addition_msg != "":
            addition_msg = '\n' + addition_msg
        now = time.strftime("%Y/%m/%d %H:%M:%S")
        template = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"{now}",
                "text": f"{now}\n![pic]({pic_url}){addition_msg}"
            },
            "at": {
                "isAtAll": atAll
            }
        }
        self.send(template)

    def send_markdown(self, title, md, atAll: bool = False):
        template = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": md
            },
            "at": {
                "isAtAll": atAll
            }
        }
        self.send(template)

    def send_text(self, msg: str, atAll: bool = False):
        assert type(msg) is str
        template = {
            "at": {
                "isAtAll": atAll
            },
            "text": {
                "content": msg
            },
            "msgtype": "text"
        }
        self.send(template)

    def send(self, template):
        post_url = self.gen_post_url()
        rj = self._post(post_url, template)
        try:
            self.errcode = rj['errcode']
            self.errmsg = rj['errmsg']
        except KeyError:
            self.errcode = -1
            self.errmsg = "解析json失败"

    @property
    def send_success(self):
        if self.errcode == 0 and self.status_code == 200:
            return True
        return False


if __name__ == '__main__':
    access_token = os.getenv("DINGDING_ACCESS_TOKEN", "")
    secret = os.getenv("DINGDING_SECRET", "")
    if not (access_token and secret):
        raise ValueError('环境变量未设置 DINGDING_ACCESS_TOKEN 或 DINGDING_SECRET')
    dingbot = DingBot(access_token, secret)
    dingbot.send_text('dingbot test')
