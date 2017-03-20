#!/usr/bin/env python
# -*- coding:utf-8 -*-

# Build-in / Std
import os
import sys
import time
import platform
import random
import re
import json
import cookielib

# requirements
import requests

requests = requests.Session()
requests.cookies = cookielib.LWPCookieJar('cookies')
try:
    requests.cookies.load(ignore_discard=True)
except:
    pass

headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
    'Host': "www.zhihu.com",
    'Origin': "https://www.zhihu.com",
    'Pragma': "no-cache",
    'Referer': "https://www.zhihu.com/",
    'X-Requested-With': "XMLHttpRequest"
}

def get_captcha():
    url = "https://www.zhihu.com/captcha.gif"
    r = requests.get(url, headers=headers, params={"r": random.random()}, verify=False)
    if int(r.status_code) != 200:
        raise NetworkError(u"get captcha fail")
    image_name = u"captcha." + r.headers['content-type'].split("/")[1]
    open(image_name, "wb").write(r.content)

    return image_name


def search_xsrf():
    url = "https://www.zhihu.com/"
    r = requests.get(url, verify=False)
    if int(r.status_code) != 200:
        return None

    results = re.compile(r"\<input\stype=\"hidden\"\sname=\"_xsrf\"\svalue=\"(\S+)\"", re.DOTALL).findall(r.text)
    if len(results) < 1:
        return None

    return results[0]


def login(account, password, xsrf, captcha):
    account_type = "phone_num"
    url = "https://www.zhihu.com/login/phone_num"
    if re.match(r"^\S+\@\S+\.\S+$", account):
        account_type = "email"
        url = "https://www.zhihu.com/login/email"

    form = {account_type: account,
            "password": password,
            "remember_me": True,
            "_xsrf": xsrf,
            "captcha": captcha}

    headers = {
        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
        'Host': "www.zhihu.com",
        'Origin': "https://www.zhihu.com",
        'Pragma': "no-cache",
        'Referer': "https://www.zhihu.com/",
        'X-Requested-With': "XMLHttpRequest"
    }

    r = requests.post(url, data=form, headers=headers, verify=False)
    if int(r.status_code) != 200:
        return {'status': False, 'msg': 'Login fail!'}

    if r.headers['content-type'].lower() == "application/json":
        try:
            result = json.loads(r.content)
        except Exception as e:
            result = {}
        if result["r"] == 0:
            requests.cookies.save()
            return {"status": True, 'msg': "Login success!"}
        elif result["r"] == 1:
            return {"status": False, 'msg': "Login fail!", 'code': int(result['errcode'])}
        else:
            return {"status": False, 'msg': "Login fail!"}
    else:
        return {"status": False, 'msg': "Unknown error!"}



def islogin():
    # check session
    url = "https://www.zhihu.com/settings/profile"
    r = requests.get(url, headers=headers, allow_redirects=False, verify=False)
    status_code = int(r.status_code)
    if status_code == 301 or status_code == 302:
        # 未登录
        return False
    elif status_code == 200:
        return True
    else:
        return None
