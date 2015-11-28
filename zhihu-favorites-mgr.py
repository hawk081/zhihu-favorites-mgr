# -*- coding: utf-8 -*-

# Build-in / Std
import os
import sys
import time
import platform
import random
import re
import json
import cookielib
import json
import wx
import wx.html
import wx.html2
import wx.lib.mixins.listctrl

# requirements
import requests
import html2text
import logging

try:
    from bs4 import BeautifulSoup
except:
    import BeautifulSoup

# module
from authorize import *
from user_logger import init_logger
from user_collections import *
import images_icon

logger = logging.getLogger("UserLog")


class LoginDialog(wx.Dialog):

    def __init__(self):
        wx.Dialog.__init__(
            self, None, -1, u'登录',
            style=wx.CAPTION | wx.CLOSE_BOX,
            size=(400, 300))
        self.SetIcon(images_icon.AppIcon.GetIcon())

        self.panel = wx.Panel(self, -1)

        self.basicLabel = wx.StaticText(self.panel, -1, u"邮箱地址:", pos=(50, 20))
        self.accountText = wx.TextCtrl(
            self.panel,
            -1,
            u"",
            size=(175, -1),
            pos=(140, 20))
        self.accountText.SetHint(u"输入账户")
        self.accountText.SetInsertionPoint(0)

        self.pwdLabel = wx.StaticText(self.panel, -1, u"密码:", pos=(50, 60))
        self.pwdText = wx.TextCtrl(
            self.panel,
            -1,
            u"",
            size=(175, -1),
            style=wx.TE_PASSWORD,
            pos=(140, 60))
        self.pwdText.SetHint(u"输入密码")

        self.captchaLabel = wx.StaticText(
            self.panel,
            -1,
            u"验证码:",
            pos=(50, 100))
        self.captchaText = wx.TextCtrl(
            self.panel,
            -1,
            "",
            size=(175, -1),
            pos=(140, 100))
        self.captchaText.SetHint(u"输入验证码")

        self.loginButton = wx.Button(self.panel, -1, u"登录", pos=(80, 140))
        self.Bind(wx.EVT_BUTTON, self.OnLoginButtonClick, self.loginButton)
        self.loginButton.SetDefault()

        self.refreshButton = wx.Button(
            self.panel,
            -1,
            u"刷新验证码",
            pos=(300 - 80, 140))
        self.Bind(wx.EVT_BUTTON, self.OnRefreshClick, self.refreshButton)

        self.imageCtrl = wx.StaticBitmap(
            self.panel,
            wx.ID_ANY,
            images_icon.AppIcon.GetBitmap(),
            size=(240, 60),
            pos=(80, 180))

        self.Center()
        self.OnRefreshClick(None)

    def OnLoginButtonClick(self, event):
        self.loginButton.SetLabel(u"登录中...")
        account = self.accountText.GetValue()
        password = self.pwdText.GetValue()
        captcha = self.captchaText.GetValue().strip()
        if len(captcha) <= 0:
            self.showMessageBox(u'请输入验证码')
            self.loginButton.SetLabel(u"登录")
            return
        xsrf = search_xsrf()
        result = login(account, password, xsrf, captcha)
        self.showMessageBox(result['msg'])
        if result['status']:
            try:
                module = sys.modules['user_collections']
                if module is not None:
                    reload(module)
            except:
                logger.error('reload user_collections fail!')
                pass
            self.EndModal(wx.ID_OK)
        self.loginButton.SetLabel(u"登录")

    def OnRefreshClick(self, event):
        self.refreshButton.SetLabel(u"刷新中...")
        image_name = get_captcha()
        self.imageCtrl.SetBitmap(
            wx.Image(image_name, wx.BITMAP_TYPE_ANY).ConvertToBitmap())
        self.refreshButton.SetLabel(u"刷新验证码")
        os.remove(image_name)

    def showMessageBox(self, text, caption=u"提示", style=wx.OK):
        dlg = wx.MessageDialog(None, text, caption, style)
        if dlg.ShowModal() == wx.ID_YES:
            self.Close(True)
        dlg.Destroy()


class MainFrame(wx.Frame):
    def __init__(self):
        if islogin() == False:
            dlg = LoginDialog()
            if wx.ID_OK == dlg.ShowModal():
                dlg.Destroy()
            else:
                dlg.Destroy()
                wx.Exit()

        wx.Frame.__init__(self, None, -1, u'知乎收藏夹', size=(900, 500))
        self.SetIcon(images_icon.AppIcon.GetIcon())
        self.SetBackgroundColour(wx.Colour(240, 240, 240))

        self.panel = wx.Panel(self)
        self.horizontalBoxSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.menubar_menu_items = [
            {'id': 30000,      'text': u'刷新', 'separator': True},
            {'id': 30001,      'text': u'刷新', 'separator': True},
            {'id': wx.ID_EXIT, 'text': u'退出', 'separator': False}
            ]

        menu = wx.Menu()
        for menu_item in self.menubar_menu_items:
            menu.Append(menu_item['id'], menu_item['text'])
            self.Bind(
                wx.EVT_MENU,
                lambda event, temp_item=menu_item:
                    self.OnMenu(event, temp_item),
                id=menu_item['id'])
            if menu_item['separator']:
                menu.AppendSeparator()

        menuBar = wx.MenuBar()
        menuBar.Append(menu, u"菜单")
        self.SetMenuBar(menuBar)

        self.collections_menu_itemms = {
            20000: u"打开",
            20001: u"重命名",
            20002: u"删除"}

        # create the list control
        self.ListCtrl_CollectionList = wx.ListCtrl(
            self.panel,
            -1,
            style=wx.LC_REPORT)
        wx.EVT_LIST_ITEM_RIGHT_CLICK(
            self.ListCtrl_CollectionList,
            -1,
            self.OnCollectionListRightClick)
        wx.EVT_LIST_ITEM_ACTIVATED(
            self.ListCtrl_CollectionList,
            -1,
            self.OnCollectionListDoubleClick)
        self.ListCtrl_CollectionList_item_clicked = None

        for col, text in enumerate(Utils.getUserCollectionListColumns()):
            self.ListCtrl_CollectionList.InsertColumn(col, text)

        self.horizontalBoxSizer.Add(
            self.ListCtrl_CollectionList,
            proportion=0,
            flag=wx.ALL | wx.EXPAND,
            border=5)

        self.UpdateCollectionList()

        # init collection answers list
        self.collections_answers_menu_items = {
            10000: u"浏览",
            10001: u"复制到",
            10002: u"移动到",
            10003: u"取消收藏"}

        # create the list control
        self.ListCtrl_CollectionAnswersList = wx.ListCtrl(
            self.panel,
            -1,
            style=wx.LC_REPORT)
        wx.EVT_LIST_ITEM_RIGHT_CLICK(
            self.ListCtrl_CollectionAnswersList,
            -1,
            self.OnCollectionAnswersListRightClick)
        wx.EVT_LIST_ITEM_ACTIVATED(
            self.ListCtrl_CollectionAnswersList,
            -1,
            self.OnCollectionAnswersListDoubleClick)
        self.ListCtrl_CollectionAnswersList_item_clicked = None

        for col, text in enumerate(Utils.getUserCollectionAnswersListColumns()):
            self.ListCtrl_CollectionAnswersList.InsertColumn(col, text)

        self.horizontalBoxSizer.Add(
            self.ListCtrl_CollectionAnswersList,
            proportion=2,
            flag=wx.ALL | wx.EXPAND,
            border=5)

        self.ListCtrl_TaskList = wx.ListCtrl(
            self.panel,
            -1,
            style=wx.LC_REPORT)
        # wx.EVT_LIST_ITEM_RIGHT_CLICK( self.ListCtrl_TaskList, -1, self.OnCollectionListRightClick )
        # wx.EVT_LIST_ITEM_ACTIVATED( self.ListCtrl_TaskList, -1, self.OnCollectionListDoubleClick )
        self.ListCtrl_TaskList_item_clicked = None

        for col, text in enumerate(Utils.getTaskListColumns()):
            self.ListCtrl_TaskList.InsertColumn(col, text)
        self.tasklist_items = []

        self.horizontalBoxSizer.Add(
            self.ListCtrl_TaskList,
            proportion=1,
            flag=wx.ALL | wx.EXPAND,
            border=5)

        self.UpdateFatitesList()

        self.panel.SetSizer(self.horizontalBoxSizer)
        self.horizontalBoxSizer.Fit(self.panel)
        self.Center()

    def UpdateFatitesList(self):
        self.FavoritesList = Utils.getUserFavoriteList()
        self.favorites_list_menu_title_by_id = {}
        logger.info("Utils.getUserFavoriteList()")
        for favorite in self.FavoritesList:
            self.favorites_list_menu_title_by_id[wx.NewId()] = favorite
            logger.info(favorite)

    def OnMenu(self, event, menu_item):
        id = event.GetId()
        logger.info('%s(%s) clicked' % (menu_item, id))
        if id == wx.ID_EXIT:
            self.Close()
        elif id == 30000:
            # refresh
            self.UpdateCollectionList()
            self.UpdateFatitesList()
            # clear answer list
            self.ListCtrl_CollectionAnswersList.DeleteAllItems()
            pass

    def AddTaskItem(self, action, selected_answer, from_collection_info, dest_collecion_info=None):
        item = {}
        item['action'] = action
        item['selected_answer'] = selected_answer
        item['from_collection_info'] = from_collection_info
        item['dest_collecion_info'] = dest_collecion_info
        self.tasklist_items.append(item)
        logger.info("item added: %s" % item)

    def UpdateTaskList(self):
        self.TaskItemsDataMap = {}
        self.ListCtrl_TaskList.DeleteAllItems()
        for item in self.tasklist_items:
            print item
            index = self.ListCtrl_TaskList.InsertStringItem(sys.maxint, item['action'])
            self.ListCtrl_TaskList.SetStringItem(index, 1, item['from_collection_info']['title'])
            if item['dest_collecion_info'] != None:
                self.ListCtrl_TaskList.SetStringItem(index, 2, item['dest_collecion_info'][1])
            else:
                self.ListCtrl_TaskList.SetStringItem(index, 2, "")
            self.TaskItemsDataMap[item['action']] = item
        self.ListCtrl_TaskList.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.ListCtrl_TaskList.SetColumnWidth(1, wx.LIST_AUTOSIZE)
        self.ListCtrl_TaskList.SetColumnWidth(2, wx.LIST_AUTOSIZE)

    def UpdateCollectionAnswersList(self, collection_id):
        self.AnswersItemsDataMap = {}
        self.ListCtrl_CollectionAnswersList.DeleteAllItems()
        for item in Utils.getAnswersInCollection(collection_id):
            index = self.ListCtrl_CollectionAnswersList.InsertStringItem(sys.maxint, item['answer_id'])
            self.ListCtrl_CollectionAnswersList.SetStringItem(index, 1, item['question_title'])
            self.ListCtrl_CollectionAnswersList.SetStringItem(index, 2, item['author_name'])
            self.ListCtrl_CollectionAnswersList.SetStringItem(index, 3, item['answer_summary'])
            self.AnswersItemsDataMap[item['answer_id']] = item
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(1, 220)
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(3, wx.LIST_AUTOSIZE)

    def OnCollectionAnswersListDoubleClick(self, event):
        self.ListCtrl_CollectionAnswersList_item_clicked = event.GetText()
        selected_answer = self.GetSelectedAnswer()
        logger.info('OnCollectionAnswersListDoubleClick - %s' % selected_answer)
        question_title = selected_answer['question_title']
        answer_content = selected_answer['contents']

        contents = zhihu_page_header.replace('{question_title}', question_title).replace('{answer_content}', answer_content)

        question_title += u" - %s的回答" % selected_answer['author_name']
        self.showHtml2(contents, question_title)

    def OnCollectionAnswersListRightClick(self, event):
        self.ListCtrl_CollectionAnswersList_item_clicked = event.GetText()

        menu = wx.Menu()
        for (id, title) in self.collections_answers_menu_items.items():
            if cmp(title, u'移动到') == 0:
                sub_menu = wx.Menu()
                for (_id, _title) in self.favorites_list_menu_title_by_id.items():
                    sub_menu.Append(_id, _title[1])
                    wx.EVT_MENU(menu, _id, self.OnMenuSelect_MoveToFavoriteList)
                menu.AppendSubMenu(sub_menu, title)
            elif cmp(title, u'复制到') == 0:
                sub_menu = wx.Menu()
                for (_id, _title) in self.favorites_list_menu_title_by_id.items():
                    sub_menu.Append(_id + 1000, _title[1])
                    wx.EVT_MENU(menu, _id + 1000, self.OnMenuSelect_CopyToFavoriteList)
                menu.AppendSubMenu(sub_menu, title)
            else:
                menu.Append(id, title)
                wx.EVT_MENU(menu, id, self.OnMenuSelect_CollectionAnswersList)
        self.PopupMenu(menu, event.GetPoint())
        menu.Destroy()

    def OnMenuSelect_CollectionAnswersList(self, event):
        operation = self.collections_answers_menu_items[event.GetId()]
        target = self.ListCtrl_CollectionAnswersList_item_clicked
        selected_answer = self.GetSelectedAnswer()
        logger.info('Perform "%(operation)s" on "%(target)s"' % vars())
        if operation == u'浏览':
            logger.info('OnCollectionAnswersListDoubleClick - %s' % selected_answer)
            question_title = selected_answer['question_title']
            answer_content = selected_answer['contents']

            question_title += u" - %s的回答" % selected_answer['author_name']
            contents = zhihu_page_header.replace('{question_title}', question_title).replace('{answer_content}', answer_content)
            print contents
            self.showHtml2(contents, question_title)
        elif event.GetId() == 10003:
            action = u'取消收藏'
            selected_answer = self.GetSelectedAnswer()
            from_collection_info = self.GetSelectedCollection()
            self.AddTaskItem(action, selected_answer, self.from_collection_info)
            self.UpdateTaskList()

    def GetSelectedAnswer(self):
        return self.AnswersItemsDataMap[self.ListCtrl_CollectionAnswersList_item_clicked]

    def GetSelectedCollection(self):
        return self.collectionsItemsDataMap[self.ListCtrl_CollectionList_item_clicked]

    def OnMenuSelect_MoveToFavoriteList(self, event):
        operation = self.favorites_list_menu_title_by_id[event.GetId()]
        target = self.ListCtrl_CollectionAnswersList_item_clicked
        action = u'移动到'
        logger.info('"%(action)s" "%(operation)s" on "%(target)s"' % vars())
        selected_answer = self.GetSelectedAnswer()
        from_collection_info = self.GetSelectedCollection()
        dest_collecion_info = operation
        self.AddTaskItem(action, selected_answer, from_collection_info, dest_collecion_info)
        self.UpdateTaskList()

    def OnMenuSelect_CopyToFavoriteList(self, event):
        operation = self.favorites_list_menu_title_by_id[event.GetId() - 1000]
        target = self.ListCtrl_CollectionAnswersList_item_clicked
        action = u'复制到'
        logger.info('"%(action)s" "%(operation)s" on "%(target)s"' % vars())
        selected_answer = self.GetSelectedAnswer()
        from_collection_info = self.GetSelectedCollection()
        dest_collecion_info = operation
        self.AddTaskItem(action, selected_answer, from_collection_info, dest_collecion_info)
        self.UpdateTaskList()

    def UpdateCollectionList(self):
        self.collectionsItemsDataMap = {}
        self.ListCtrl_CollectionList.DeleteAllItems()
        for item in Utils.getUserCollectionList():
            index = self.ListCtrl_CollectionList.InsertStringItem(sys.maxint, item['title'])
            self.collectionsItemsDataMap[item['title']] = item
        self.ListCtrl_CollectionList.SetColumnWidth(0, 175)  # wx.LIST_AUTOSIZE

    def OnCollectionListDoubleClick(self, event):
        self.ListCtrl_CollectionList_item_clicked = event.GetText()
        selected_item = self.GetSelectedCollection()
        logger.info('OnCollectionListDoubleClick - %s' % selected_item)
        self.UpdateCollectionAnswersList(selected_item['collection_id'])

    def OnCollectionListRightClick(self, event):
        self.ListCtrl_CollectionList_item_clicked = event.GetText()

        menu = wx.Menu()
        for (id, title) in self.collections_menu_itemms.items():
            menu.Append(id, title)
            wx.EVT_MENU(menu, id, self.OnMenuSelect_CollectionList)
        self.PopupMenu(menu, event.GetPoint())
        menu.Destroy()

    def OnMenuSelect_CollectionList(self, event):
        operation = self.collections_menu_itemms[event.GetId()]
        target = self.ListCtrl_CollectionList_item_clicked
        selected_item = self.GetSelectedCollection()
        logger.info('Perform "%(operation)s" on "%(target)s."' % vars())
        if operation == u'打开':
            self.UpdateCollectionAnswersList(selected_item['collection_id'])

    def showMessageBox(self, text, caption="提示", style=wx.OK):
        dlg = wx.MessageDialog(None, text, caption, style)
        if dlg.ShowModal() == wx.ID_YES:
            self.Close(True)
        dlg.Destroy()

    def showHtml2(self, content, title=None):
        class AnswerBrowser(wx.Frame):
            def __init__(self, *args, **kwds):
                wx.Frame.__init__(self, *args, **kwds)
                self.SetIcon(images_icon.AppIcon.GetIcon())
                self.panel = wx.Panel(self, -1)
                self.title = None
                self.browser = wx.html2.WebView.New(self.panel, pos=(10, 10), size=(780, 580))
                self.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.OnPageLoad, self.browser)
                internal_sizer = wx.BoxSizer(wx.VERTICAL)
                internal_sizer.Add(self.browser, 1, wx.EXPAND, 15)
                self.panel.SetSizer(internal_sizer)

                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(self.panel, 1, wx.EXPAND, 10)
                self.SetSizer(sizer)
                internal_sizer.Fit(self.panel)

            def OnPageLoad(self, event):
                self.WebTitle = self.browser.GetCurrentTitle()
                self.SetTitle(self.WebTitle)

            def SetTitleContent(self, title):
                if title is not None and len(title.strip()) > 0:
                    self.title = title
                    self.SetTitle(self.title)

        dialog = AnswerBrowser(None, -1, size=(820, 600))
        dialog.browser.SetPage(content, "")
        dialog.SetTitleContent(title)
        dialog.Show()

if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
