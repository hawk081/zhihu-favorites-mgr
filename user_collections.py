# -*- coding: utf-8 -*-

# Build-in / Std
import os
import sys
import time
import platform
import re
import json
import cookielib
import codecs
import HTMLParser

# requirements
import requests
import logging

try:
    from bs4 import BeautifulSoup
    import bs4
except:
    import BeautifulSoup

# module
from authorize import islogin
from user_logger import init_logger

init_logger()
logger = logging.getLogger("UserLog")

requests = requests.Session()
requests.cookies = cookielib.LWPCookieJar('cookies')

try:
    requests.cookies.load(ignore_discard=True)
except:
    pass

if islogin() != True:
    pass

reload(sys)
sys.setdefaultencoding('utf8')
codecs.register(
    lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)


class Collection:
    def __init__(self, href, title):
        self.href = href
        self.title = title
        self.collection_id = href[href.rindex('/') + 1:]

    def __getitem__(self, key):
        return self.title

    def __str__(self):
        return '%s, %s' % (self.title, self.href)
        # return "%s, %s" % (self.title.encode('unicode_escape'), self.href)


class CollectionGetter:
    def __init__(self):
        self.question_title = ""

    def set_question(self, zm_item_title):
        if zm_item_title is not None and hasattr(zm_item_title, 'a'):
            self.question_title = zm_item_title.a.string

    def set_answer(self, zm_item_answer):
        self.answer_id = zm_item_answer['data-aid']
        self.author_id = zm_item_answer['data-created']
        self.author_name = ""
        infos = zm_item_answer.find_all(
            "div",
            class_="zm-item-answer-author-info")
        if len(infos) > 0:
            if hasattr(infos[0], 'a') and infos[0].a is not None:
                self.author_name = infos[0].a.string
            elif hasattr(infos[0], 'span') and infos[0].span is not None:
                self.author_name = infos[0].span.string
        zh_summarys = zm_item_answer.find_all(
            "div",
            class_="zh-summary summary clearfix")
        self.answer_summary = ""
        if len(zh_summarys) > 0:
            # print hasattr(zh_summarys[0], "img") and zh_summarys[0].img != None
            for content in zh_summarys[0].contents:
                if type(content) == bs4.element.NavigableString:
                    # print content.decode('utf-8').encode('gbk')
                    if(len(content.strip()) > 0):
                        self.answer_summary += content.strip()
        hidden_contents = zm_item_answer.find_all("textarea", class_="content hidden")
        self.contents = ""
        if len(hidden_contents) > 0:
            textarea_hidden_content = hidden_contents[0]
            textarea_hidden_content.name = "div"
            textarea_hidden_content['class'] = "content"
            textarea_hidden_content['style'] = "width:760px;margin-left:auto;margin-right:auto;"
            self.contents = textarea_hidden_content.prettify()
            h = HTMLParser.HTMLParser()
            self.contents = h.unescape(self.contents)

    def get_collection(self):
        answer = {}
        answer['question_title'] = self.question_title
        answer['answer_id'] = self.answer_id
        answer['author_id'] = self.author_id
        answer['author_name'] = self.author_name
        answer['answer_summary'] = self.answer_summary
        answer['contents'] = self.contents

        return answer


class Utils:
    @staticmethod
    def search_xsrf():
        url = "http://www.zhihu.com/"
        r = requests.get(url)
        if int(r.status_code) != 200:
            logger.error('fetch XSRF fail')
        results = re.compile(r"\<input\stype=\"hidden\"\sname=\"_xsrf\"\svalue=\"(\S+)\"", re.DOTALL).findall(r.text)
        if len(results) < 1:
            Logging.info('fetch XSRF fail')
            return None
        return results[0]

    @staticmethod
    def getUserFavoriteList():
        r = requests.get("http://www.zhihu.com/collections/json?answer_id=20176787")
        s = json.loads(r.content)
        for msg in s['msg']:
            for _msg in msg:
                if type(_msg) == list:
                    yield _msg

    @staticmethod
    def getUserCollectionListColumns():
        return [u"收藏夹名称"]

    @staticmethod
    def getUserCollectionList():
        r = requests.get("http://www.zhihu.com/collections/mine")
        soup = BeautifulSoup(r.content, 'html5lib')
        zm_items = soup.find_all("div", class_="zm-item")
        for zm_item in zm_items:
            collection_item = {}
            href = zm_item.h2.a['href']
            collection_item['href'] = href
            collection_item['title'] = zm_item.h2.a.string
            collection_item['collection_id'] = href[href.rindex('/') + 1:]
            yield collection_item

    @staticmethod
    def getUserCollectionAnswersListColumns():
        return [u"回答ID", u"问题", u"回答作者", u"概要"]

    @staticmethod
    def getAnswersInCollection(collection_id):
        r = requests.get("http://www.zhihu.com/collection/" + str(collection_id))
        soup = BeautifulSoup(r.content, 'html5lib')
        zm_items = soup.find_all("div", class_="zm-item")
        _collectionGetter = CollectionGetter()
        for zm_item in zm_items:
            zm_item_titles = zm_item.find_all("h2", class_="zm-item-title")
            if len(zm_item_titles) > 0:
                _collectionGetter.set_question(zm_item_titles[0])
            zm_item_answers = zm_item.find_all("div", class_="zm-item-answer")
            if len(zm_item_answers) > 0:
                _collectionGetter.set_answer(zm_item_answers[0])
            else:
                continue

            yield _collectionGetter.get_collection()

    @staticmethod
    def getTaskListColumns():
        return [u"操作", u"从", u"到"]

    @staticmethod
    def add_favorite(answer_id, favlist_id):
        url = "http://www.zhihu.com/collection/add"
        form = {'answer_id': answer_id, 'favlist_id': favlist_id, '_xsrf': Utils.search_xsrf()}
        headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
            'Host': "www.zhihu.com",
            'Origin': "http://www.zhihu.com",
            'Pragma': "no-cache",
            'Referer': "http://www.zhihu.com/",
            'X-Requested-With': "XMLHttpRequest"
        }

        r = requests.post(url, data=form, headers=headers)
        s = json.loads(r.content)
        if int(r.status_code) != 200:
            logger.debug("add_favorite fail %d!" % int(r.status_code))
            return False
        elif s['r'] != 0:
            logger.debug("Error msg: %s" % s['msg'].decode('utf-8').encode('gbk'))
            return False
        else:
            logger.debug("add_favorite success!")

        return True

    @staticmethod
    def remove_favorite(answer_id, favlist_id):
        url = "http://www.zhihu.com/collection/remove"
        form = {'answer_id': answer_id, 'favlist_id': favlist_id, '_xsrf': Utils.search_xsrf()}
        headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
            'Host': "www.zhihu.com",
            'Origin': "http://www.zhihu.com",
            'Pragma': "no-cache",
            'Referer': "http://www.zhihu.com/",
            'X-Requested-With': "XMLHttpRequest"
        }

        r = requests.post(url, data=form, headers=headers)
        s = json.loads(r.content)
        if int(r.status_code) != 200:
            logger.debug("add_favorite fail %d!" % int(r.status_code))
            return False
        elif s['r'] != 0:
            logger.debug("Error msg: %s" % s['msg'].decode('utf-8').encode('gbk'))
            return False
        else:
            logger.debug("remove_favorite success!")

        return True

zhihu_page_header = '''
<html lang="zh-CN" dropeffect="none" class="js  show-app-promotion-bar cssanimations csstransforms csstransitions flexbox no-touchevents no-mobile"><head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
<meta name="renderer" content="webkit">
<title>{question_title}</title>
<meta name="apple-itunes-app" content="app-id=432274380, app-argument=zhihu://questions/31496671">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<meta http-equiv="mobile-agent" content="format=html5;url=http://www.zhihu.com/question/31496671">
<meta id="znonce" name="znonce" content="f7cf44443ebc4b7ba6b9f9c1272772ae">
<link rel="apple-touch-icon-precomposed" href="http://static.zhihu.com/static/img/ios/zhihu(57px).png">
<link rel="apple-touch-icon-precomposed" href="http://static.zhihu.com/static/img/ios/zhihu(72px).png" sizes="72x72">
<link rel="apple-touch-icon-precomposed" href="http://static.zhihu.com/static/img/ios/zhihu(76px).png" sizes="76x76">
<link rel="apple-touch-icon-precomposed" href="http://static.zhihu.com/static/img/ios/zhihu(114px).png" sizes="114x114">
<link rel="apple-touch-icon-precomposed" href="http://static.zhihu.com/static/img/ios/zhihu(120px).png" sizes="120x120">
<link rel="apple-touch-icon-precomposed" href="http://static.zhihu.com/static/img/ios/zhihu(152px).png" sizes="152x152">
<link rel="shortcut icon" href="http://static.zhihu.com/static/favicon.ico" type="image/x-icon">
<link rel="search" type="application/opensearchdescription+xml" href="http://static.zhihu.com/static/search.xml" title="知乎">
<link rel="stylesheet" href="http://static.zhihu.com/static/revved/-/css/z.7fde691e.css">
<!--[if lt IE 9]>
<script src="http://static.zhihu.com/static/components/respond/dest/respond.min.js"></script>
<link href="http://static.zhihu.com/static/components/respond/cross-domain/respond-proxy.html" id="respond-proxy" rel="respond-proxy" />
<link href="/static/components/respond/cross-domain/respond.proxy.gif" id="respond-redirect" rel="respond-redirect" />
<script src="/static/components/respond/cross-domain/respond.proxy.js"></script>
<![endif]-->
<script type="text/javascript" async="" src="http://zhstatic.zhihu.com/za/za-0.1.0.min.js"></script><script async="" src="http://www.google-analytics.com/ga.js"></script><script src="http://static.zhihu.com/static/revved/-/js/instant.92770c12.js"></script><style type="text/css"></style>
<style>html.modal-open {overflow:hidden}html.modal-doc-overflow {margin-right:14px}html.modal-doc-overflow .modal-translate-shifting.sticky {transition-property:none; transform:translateX(-7px)}html.modal-doc-overflow .modal-shifting {position:relative; right:7px}</style><style id="style-1-cropbar-clipper">/* Copyright 2014 Evernote Corporation. All rights reserved. */
.en-markup-crop-options {
    top: 18px !important;
    left: 50% !important;
    margin-left: -100px !important;
    width: 200px !important;
    border: 2px rgba(255,255,255,.38) solid !important;
    border-radius: 4px !important;
}
.en-markup-crop-options div div:first-of-type {
    margin-left: 0px !important;
}
</style></head>
<body style='align:center;'>
{answer_content}
</body>
</html>
'''

# Test
if __name__ == '__main__':
    for m in Utils.getUserFavoriteList():
        print m

    for m in Utils.getUserCollectionList():
        print m.title, m.href, m.collection_id
        for m in Utils.getAnswersInCollection(m.collection_id):
            print m['question_title'].decode('utf-8').encode("gbk"), m['author_name'].decode('utf-8').encode("gbk")

    Utils.add_favorite(18930058, 24663914)
    Utils.remove_favorite(18930058, 24663914)
