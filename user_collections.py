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
import traceback

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
from html_template import *
from chm_utils import *

init_logger()
logger = logging.getLogger("UserLog")

requests.packages.urllib3.disable_warnings()
zhihu_requests = requests.Session()
zhihu_requests.cookies = cookielib.LWPCookieJar('cookies')

try:
    zhihu_requests.cookies.load(ignore_discard=True)
except:
    pass

if islogin() != True:
    pass

reload(sys)
sys.setdefaultencoding('utf8')
codecs.register(
    lambda name: codecs.lookup('utf-8') if name == 'cp65001' else None)

headers = {
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
    'Host': "www.zhihu.com",
    'Origin': "https://www.zhihu.com",
    'Pragma': "no-cache",
    'Referer': "https://www.zhihu.com/"
}

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
            href = zm_item_title.a['href']
            self.question_id = href[href.rindex('/') + 1:]

    def set_answer(self, zm_item_answer):
        self.answer_id = zm_item_answer['data-aid']
        self.answer_id_url = zm_item_answer['data-atoken']
        self.author_id = zm_item_answer['data-created']
        self.author_name = ""
        self.author_url = ""
        infos = zm_item_answer.find_all(
            "div",
            class_="zm-item-answer-author-info")
        if len(infos) > 0:
            if hasattr(infos[0], 'a') and infos[0].a is not None:
                self.author_name = infos[0].a.string
                self.author_url = infos[0].a['href']
            elif hasattr(infos[0], 'span') and infos[0].span is not None:
                self.author_name = infos[0].span.string
                self.author_url = ""
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
        hidden_contents = zm_item_answer.find_all("textarea", class_="content")
        self.contents = ""
        if len(hidden_contents) > 0:
            textarea_hidden_content = hidden_contents[0]
            textarea_hidden_content.name = "div"
            
            # remove all unnecessary attributes
            kyes = [ k for k in textarea_hidden_content.attrs]
            for attr in kyes:
                del textarea_hidden_content[attr]
            textarea_hidden_content['class'] = "content"
            textarea_hidden_content['style'] = "width:780px;margin-left:auto;margin-right:auto;"

            self.contents = textarea_hidden_content.prettify()
            h = HTMLParser.HTMLParser()
            self.contents = h.unescape(self.contents)

            # html for chm
            textarea_hidden_content['style'] = "width:780px;margin:10px;"
            self.chm_contents = textarea_hidden_content.prettify()
            self.chm_contents = h.unescape(self.chm_contents)
        else:
            print 'hidden_contents\'s length is 0'

    def get_collection(self):
        answer = {}
        answer['question_id'] = self.question_id
        answer['question_title'] = self.question_title
        answer['answer_id'] = self.answer_id
        answer['answer_id_url'] = self.answer_id_url
        answer['author_id'] = self.author_id
        answer['author_url'] = self.author_url
        answer['author_name'] = self.author_name
        answer['answer_summary'] = self.answer_summary
        answer['contents'] = self.contents
        answer['chm_contents'] = self.chm_contents

        question_title_fld = zhihu_question_title_fld_template.replace('{style}', 'width:780px;margin-left:auto;margin-right:auto;')
        question_title_fld = question_title_fld.replace('{author_url}', self.author_url)
        question_title_fld = question_title_fld.replace('{author_name}', self.author_name)

        full_page = zhihu_page_header.replace('{question_title_fld}', question_title_fld)
        full_page = full_page.replace('{question_title}', self.question_title)
        full_page = full_page.replace('{answer_content}', self.contents)
        full_page = full_page.replace('{question_id}', self.question_id)
        answer['full_page'] = full_page

        answer['full_title'] = u"%s - %s的回答" % (self.question_title, self.author_name)

        question_title_fld = zhihu_question_title_fld_template.replace('{style}', 'width:780px;margin:10px;')
        question_title_fld = question_title_fld.replace('{author_url}', self.author_url)
        question_title_fld = question_title_fld.replace('{author_name}', self.author_name)

        full_chm_page = zhihu_page_header.replace('{question_title_fld}', question_title_fld)
        full_chm_page = full_chm_page.replace('{question_title}', self.question_title)
        full_chm_page = full_chm_page.replace('{answer_content}', self.chm_contents)
        full_chm_page = full_chm_page.replace('{question_id}', self.question_id)
        answer['full_chm_page'] = full_chm_page

        #full_chm_page_gbk = zhihu_page_header.replace('utf-8', 'gbk')
        #full_chm_page_gbk = full_chm_page_gbk.replace('{question_title_fld}', question_title_fld)
        #full_chm_page_gbk = full_chm_page_gbk.replace('{question_title}', self.question_title)
        #full_chm_page_gbk = full_chm_page_gbk.replace('{answer_content}', self.chm_contents)
        #full_chm_page_gbk = full_chm_page_gbk.replace('{question_id}', self.question_id)
        #answer['full_chm_page_gbk'] = full_chm_page_gbk.encode('gbk')

        return answer

class Utils:
    @staticmethod
    def search_xsrf():
        url = "https://www.zhihu.com/"
        r = zhihu_requests.get(url, verify=False)
        if int(r.status_code) != 200:
            logger.error('fetch XSRF fail')
        results = re.compile(r"\<input\stype=\"hidden\"\sname=\"_xsrf\"\svalue=\"(\S+)\"", re.DOTALL).findall(r.text)
        if len(results) < 1:
            Logging.info('fetch XSRF fail')
            return None
        return results[0]

    @staticmethod
    def createCollection(title, is_public=False, description="" ):
        if is_public:
            is_public = 1
        else:
            is_public = 0

        if description is None or len(description) <= 0:
            description = -1

        url = 'https://www.zhihu.com/collection/create'
        form = {
                'title': title,
                'is_public': is_public,
                'description': description,
                'answer_id': 25523047,
                '_xsrf': Utils.search_xsrf()}

        r = zhihu_requests.post(url, data=form, headers=headers, verify=False)
        if int(r.status_code) != 200:
            logger.debug("createCollection fail %d!" % int(r.status_code))
            return {'status': False, 'msg': r.status_code, 'extra': form}
        s = json.loads(r.content)
        if s['r'] != 0:
            logger.debug("Error msg: %s" % s['msg'].decode('utf-8'))
            return {'status': False, 'msg': s['msg'].decode('utf-8'), 'extra': form}
        else:
            logger.debug("createCollection success!")
            # remove the temp answer id
            msg = s['msg']
            status = Utils.remove_favorite(25523047, msg[0])

        return {'status': True, 'msg': 'success'}

    @staticmethod
    def deleteCollection(favlist_id):
        url = 'https://www.zhihu.com/collection/delete'
        form = {
                'favlist_id': favlist_id,
                '_xsrf': Utils.search_xsrf()}

        r = zhihu_requests.post(url, data=form, headers=headers, verify=False)
        if int(r.status_code) != 302 and int(r.status_code) != 200:
            logger.debug("deleteCollection fail %d!" % int(r.status_code))
            return {'status': False, 'msg': r.status_code, 'extra': form}

        return {'status': True, 'msg': 'success'}

    @staticmethod
    def editCollection(title, favlist_id, is_public=False, description="" ):
        if is_public:
            is_public = 1
        else:
            is_public = 0

        if description is None or len(description) <= 0:
            description = -1

        url = 'https://www.zhihu.com/collection/update'
        form = {
                'title': title,
                'is_public': is_public,
                'description': description,
                'favlist_id': favlist_id,
                '_xsrf': Utils.search_xsrf()}

        r = zhihu_requests.post(url, data=form, headers=headers, verify=False)
        if int(r.status_code) != 200:
            logger.debug("editCollection fail %d!" % int(r.status_code))
            return {'status': False, 'msg': r.status_code, 'extra': form}
        else:
            logger.debug("editCollection success!")

        return {'status': True, 'msg': 'success'}

    @staticmethod
    def getUserFavoriteList():
        r = zhihu_requests.get("https://www.zhihu.com/collections/json?answer_id=20176787", verify=False, headers=headers)
        s = json.loads(r.content)
        for msg in s['msg']:
            for _msg in msg:
                if type(_msg) == list:
                    item = {}
                    item['favorite_id'] = _msg[0]
                    item['title'] = _msg[1]
                    item['description'] = _msg[2]
                    item['3'] = _msg[3]
                    item['4'] = _msg[4]
                    item['public'] = _msg[5]
                    yield item

    @staticmethod
    def getUserCollectionListColumns():
        return [u"收藏夹名称"]

    @staticmethod
    def getUserCollectionList():
        r = zhihu_requests.get("https://www.zhihu.com/collections/mine", headers=headers, verify=False)
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
        r = zhihu_requests.get("https://www.zhihu.com/collection/" + str(collection_id), headers=headers, verify=False)
        soup = BeautifulSoup(r.content, 'html5lib')

        page_count = 1

        zm_invite_pagers = soup.find_all("div", class_="zm-invite-pager")
        if zm_invite_pagers is not None and len(zm_invite_pagers) > 0:
            zm_invite_pager = zm_invite_pagers[0]
            page_count = len(zm_invite_pager.find_all("span")) - 2 # 上一页/下一页

        if page_count > 1:
            for i in range(1, page_count + 1):
                r = zhihu_requests.get("https://www.zhihu.com/collection/" + str(collection_id) + "?page=%d" % i, headers=headers, verify=False)
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
        else:
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
        return [u"操作", u'状态', u'答案', u"从", u"到" ]

    @staticmethod
    def add_favorite(answer_id, favlist_id):
        url = "https://www.zhihu.com/collection/add"
        form = {'answer_id': answer_id, 'favlist_id': favlist_id, '_xsrf': Utils.search_xsrf()}

        r = zhihu_requests.post(url, data=form, headers=headers, verify=False)
        s = json.loads(r.content)
        if int(r.status_code) != 200:
            logger.debug("add_favorite fail %d!" % int(r.status_code))
            return {'status': False, 'msg': r.status_code, 'extra': form}
        elif s['r'] != 0:
            logger.debug(u"Error msg: %s" % s['msg'].decode('utf-8'))
            return {'status': False, 'msg': s['msg'].decode('utf-8'), 'extra': form}
        else:
            logger.debug("add_favorite success!")

        return {'status': True, 'msg': 'success'}

    @staticmethod
    def remove_favorite(answer_id, favlist_id):
        url = "https://www.zhihu.com/collection/remove"
        form = {'answer_id': answer_id, 'favlist_id': favlist_id, '_xsrf': Utils.search_xsrf()}

        r = zhihu_requests.post(url, data=form, headers=headers, verify=False)
        if int(r.status_code) != 200:
            logger.debug("remove_favorite fail %d!" % int(r.status_code))
            return {'status': False, 'msg': r.status_code, 'extra': form}
        s = json.loads(r.content)
        if s['r'] != 0:
            logger.debug("Error msg: %s" % s['msg'].decode('utf-8'))
            return {'status': False, 'msg': s['msg'].decode('utf-8'), 'extra': form}
        else:
            logger.debug("remove_favorite success!")

        return {'status': True, 'msg': 'success'}

    @staticmethod
    def move_favorite(answer_id, from_collection_id, dest_collection_id):
        if Utils.add_favorite(answer_id, dest_collection_id):
            if Utils.remove_favorite(answer_id, from_collection_id):
                return {'status': True, 'msg': 'success'}
            return {'status': False, 'msg': 'success to add, but fail to remove form original collection'}
        return {'status': False, 'msg': 'fail to add favorite to %s' % dest_collection_id}

    @staticmethod
    def copy_favorite(answer_id, from_collection_id, dest_collection_id):
        if Utils.add_favorite(answer_id, dest_collection_id):
            return {'status': True, 'msg': 'success'}
        return {'status': False, 'msg': 'fail to add favorite to %s' % dest_collection_id}

    # 1. find all resources by reg:"[-\w\./:]+\.(css|js|jpg|png|bmp|jpeg)"
    # 2. download resources to res
    # 3. replace the orginal link with local link
    # 4. link all html to index.html
    # 5. copy file from temp_dir_path to local
    @staticmethod
    def export_html_and_res(html_content, collection_title, answer_id, base_dir=".", progress_callback=None):
        collection_path = "%s/%s" % (base_dir, collection_title)
        collection_res_path = "%s/res" % collection_path
        collection_css_path = "%s/css" % collection_res_path
        collection_js_path = "%s/js" % collection_res_path
        answer_res_path = "%s/%s" % (collection_res_path, answer_id)
        
        if not os.path.exists(collection_path):
            os.makedirs(collection_path)
        if not os.path.exists(collection_res_path):
            os.makedirs(collection_res_path)
        if not os.path.exists(collection_css_path):
            os.makedirs(collection_css_path)
        if not os.path.exists(collection_js_path):
            os.makedirs(collection_js_path)
        if not os.path.exists(answer_res_path):
            os.makedirs(answer_res_path)
        # ([-\w]+)\s*=\s*"([-\w\./:]+\.(?:css|js|jpg|png|bmp|jpeg))"
        res_re_obj = re.compile(r"([-\w]+)\s*=\s*\"([-\w\./:]+\.(?:css|js|jpg|png|bmp|jpeg))\"")
        results = res_re_obj.findall(html_content)
        if results:
            for result in results:
                if cmp(result[0], "data-original") != 0:
                    status = {'status': False, 'url': "", 'o': "", 'r': result[1]}
                    if result[1].endswith('.css'):
                        status = Utils.download_res(result[1], collection_css_path)
                        if progress_callback is not None:
                            progress_callback({'msg': status['r']})
                    elif result[1].endswith('.js'):
                        status = Utils.download_res(result[1], collection_js_path)
                        if progress_callback is not None:
                            progress_callback({'msg': status['r']})
                    else:
                        status = Utils.download_res(result[1], answer_res_path)
                        if progress_callback is not None:
                            progress_callback({'msg': status['r']})

                    if status['status']:
                        html_content = html_content.replace(result[1], status['r'])

        fname = "%s/%s.html" % (collection_path, answer_id)
        with open(fname, "wb") as fhndl:
             fhndl.write(html_content)

        if progress_callback is not None:
            progress_callback({'msg': fname})

        return {'status': True, 'fname': fname, "r": re.sub(r".*?export", ".", fname)}

    @staticmethod
    def download_res(url, dir):
        def download(url, fname):
            status = True
            print "downloading %s from %s" % (fname, url)
            try:
                r = requests.get(url, verify=False)
                with open(fname, "wb") as fhndl:
                     fhndl.write(r.content)
            except Exception,e:
                status = False
                print Exception,":",e
                traceback.print_exc()

            return status
        fname  = "%s/%s" % (dir, url[url.rfind('/')+1:])
        status = download(url, fname)
        relative_fname = re.sub(r".*?res", "./res", fname)
        return {'status': status, 'url': fname, 'o': url, 'r': relative_fname}

    @staticmethod
    def export_collections_chm(collection_items, progress_callback=None):
        status = Utils.export_collections(collection_items, progress_callback, True)
        if progress_callback is not None:
            progress_callback({'msg': "正在转换为chm文件"})
        status = CHMFile(status['fname']).build()
        if progress_callback is not None:
            progress_callback({'msg': "成功! %s" % status['fname']})

        fname = status['fname']
        return {'status': True, 'msg': u'导出成功 %s' % fname, 'fname': fname}

    @staticmethod
    def export_collections(collection_items, progress_callback=None, export_for_chm=False):
        if len(collection_items) <= 0:
            return {'status': False, 'msg': 'No items to be exported'}
        fname = ""
        if len(collection_items) > 1:
            fname = u"%s,%s等%d个收藏夹" % (collection_items[0]['title'], collection_items[1]['title'], len(collection_items))
        else:
            fname = collection_items[0]['title']

        base_dir = "./export"

        html_navigator_directory_list = []
        for collection_item in collection_items:
            directory_info = Utils.export_collection(collection_item, base_dir, progress_callback, export_for_chm)
            html_navigator_directory_list.append(directory_info)

        index_html = index_html_template.replace("{navigator_directory_list_items}", "".join([x['directory'] for x in html_navigator_directory_list]))
        index_html = index_html.replace("{collection_title}", fname)
        index_html = index_html.replace("{default_page}", "")
        index_html = index_html.replace("{collection_set_title}", fname)

        fname = "%s/%s.html" % (base_dir, fname)
        with open(fname, "wb") as fhndl:
             fhndl.write(index_html)

        logger.info(u"导出成功 - %s" % fname)
        return {'status': True, 'msg': u'导出成功 %s' % fname, 'fname': fname}

    @staticmethod
    def export_collection(collection, base_dir, progress_callback=None, export_for_chm=False):
        answerItems = Utils.getAnswersInCollection(collection['collection_id'])
        html_navigator_list = []
        all_pages_relative_path = []
        for answerItem in answerItems:
            if export_for_chm:
                status = Utils.export_html_and_res(answerItem['full_chm_page'], collection['title'], answerItem['answer_id'], base_dir, progress_callback)
            else:
                status = Utils.export_html_and_res(answerItem['full_page'], collection['title'], answerItem['answer_id'], base_dir, progress_callback)
            index_html_navigator = index_html_navigator_item_template.replace("{target_html_relative_path}", status['r'])
            index_html_navigator = index_html_navigator.replace("{question_title}", answerItem['full_title'])
            html_navigator_list.append(index_html_navigator)
            all_pages_relative_path.append(status['fname'])

        index_html_navigator_directory_item = index_html_navigator_directory_item_template.replace("{navigator_list_items}", "".join(html_navigator_list))
        index_html_navigator_directory_item = index_html_navigator_directory_item.replace("{collection_title}", collection['title'])

        default_page = ""
        if len(all_pages_relative_path) > 0:
            default_page = all_pages_relative_path[0]

        return {'directory': index_html_navigator_directory_item, 'default': default_page }

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
