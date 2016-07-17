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
import threading
from Queue import Queue
import traceback
import tempfile

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
from zhihu_enum import Enum
from html_template import *

logger = logging.getLogger("UserLog")

ControlID = Enum([
'MAX_SUBMENU_COUNT= 50',
'MENUBAR_MENU_ITEM_REFRESH = 1000',
'MENUBAR_MENU_ITEM_CREATE',
'MENUBAR_MENU_ITEM_SHOW_STATUSBAR',
'MENUBAR_MENU_ITEM_HIDE_STATUSBAR',
'MENUBAR_MENU_ITEM_EXPORT_ALL',
'MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8',
'MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_GBK',
'MENUBAR_MENU_ITEM_EXPORT_ALL_HTML',
'MENUBAR_MENU_ITEM_QUIT',
'COLLECTION_LIST_MENU_OPEN',
'COLLECTION_LIST_MENU_RENAME',
'COLLECTION_LIST_MENU_EXPORT',
'COLLECTION_LIST_MENU_EXPORT_CHM_UTF8',
'COLLECTION_LIST_MENU_EXPORT_CHM_GBK',
'COLLECTION_LIST_MENU_EXPORT_HTML',
'COLLECTION_LIST_MENU_DELETE',
'ANSWER_LIST_MENU_BROWSE',
'ANSWER_LIST_MENU_BROWSE_COPY',
'ANSWER_LIST_MENU_BROWSE_MOVE',
'ANSWER_LIST_MENU_BROWSE_DELETE',
'ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START',
'ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_END = ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START + MAX_SUBMENU_COUNT',
'ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START',
'ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_END = ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START + MAX_SUBMENU_COUNT',
])


class BaseDialog(wx.Dialog):
    def __init__(self, *args, **kwds):
        wx.Dialog.__init__(self, *args, **kwds)

    def showMessageBox(self, text, caption=u"提示", style=wx.OK):
        dlg = wx.MessageDialog(None, text, caption, style)
        if dlg.ShowModal() == wx.ID_YES:
            self.Close(True)
        dlg.Destroy()

class LoginDialog(BaseDialog):

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

class CreateFavoriteDialog(BaseDialog):

    def __init__(self, userCollections):
        wx.Dialog.__init__(
            self, None, -1, u'新建收藏夹',
            style=wx.CAPTION | wx.CLOSE_BOX,
            size=(400, 160))
        self.SetIcon(images_icon.AppIcon.GetIcon())

        self.panel = wx.Panel(self, -1)

        self.basicLabel = wx.StaticText(self.panel, -1, u"收藏夹名称:", pos=(60, 15))
        self.favorite_title = wx.TextCtrl(
            self.panel,
            -1,
            u"",
            size=(175, -1),
            pos=(140, 10))
        self.favorite_title.SetHint(u"输入收藏夹名称")
        self.favorite_title.SetInsertionPoint(0)

        self.descLabel = wx.StaticText(self.panel, -1, u"描述:", pos=(60, 45))
        self.desc_text = wx.TextCtrl(
            self.panel,
            -1,
            u"",
            size=(175, -1),
            pos=(140, 40))
        self.desc_text.SetHint(u"输入描述")
        self.desc_text.SetInsertionPoint(0)

        self.public_radio = wx.RadioButton(self.panel, -1, u"公开", pos=(140, 70), style=wx.RB_GROUP)
        self.private_radio = wx.RadioButton(self.panel, -1, u"私有", pos=(200, 70))

        self.createButton = wx.Button(self.panel, -1, u"创建", pos=(150, 90))
        self.Bind(wx.EVT_BUTTON, self.OnLoginButtonClick, self.createButton)
        self.createButton.SetDefault()

        self.userCollections = userCollections

        self.Center()

    def OnLoginButtonClick(self, event):
        self.createButton.SetLabel(u"创建中...")
        title = self.favorite_title.GetValue()
        is_public = self.public_radio.GetValue()
        description = self.desc_text.GetValue()
        if title is None or len(title) <= 0:
            self.showMessageBox(u'收藏夹名称不能为空!')
            self.createButton.SetLabel(u"创建")
            return

        for collection in self.userCollections:
            if cmp(collection['title'], title) == 0:
                self.showMessageBox(u'收藏夹[%s]已存在!' % title)
                self.createButton.SetLabel(u"创建")
                return

        result = Utils.createCollection(title, is_public, description)
        if result['status']:
            self.showMessageBox(u'创建成功')
            self.EndModal(wx.ID_OK)
        else:
            self.showMessageBox(u'创建失败')
        self.createButton.SetLabel(u"创建")

class EditFavoriteDialog(BaseDialog):

    def __init__(self, collection, userCollections):
        self.currentCollection = collection
        self.userCollections = userCollections

        wx.Dialog.__init__(
            self, None, -1, u'编辑收藏夹',
            style=wx.CAPTION | wx.CLOSE_BOX,
            size=(400, 160))
        self.SetIcon(images_icon.AppIcon.GetIcon())

        self.panel = wx.Panel(self, -1)

        self.basicLabel = wx.StaticText(self.panel, -1, u"收藏夹名称:", pos=(60, 15))
        self.favorite_title = wx.TextCtrl(
            self.panel,
            -1,
            u"",
            size=(175, -1),
            pos=(140, 10))
        self.favorite_title.SetHint(u"输入收藏夹名称")
        self.favorite_title.SetInsertionPoint(0)
        self.favorite_title.SetValue(self.currentCollection['title'])

        self.descLabel = wx.StaticText(self.panel, -1, u"描述:", pos=(60, 45))
        self.desc_text = wx.TextCtrl(
            self.panel,
            -1,
            u"",
            size=(175, -1),
            pos=(140, 40))
        self.desc_text.SetHint(u"输入描述")
        self.desc_text.SetInsertionPoint(0)
        print self.currentCollection
        self.desc_text.SetValue(self.currentCollection['favorite_info']['description'])

        self.public_radio = wx.RadioButton(self.panel, -1, u"公开", pos=(140, 70), style=wx.RB_GROUP)
        self.private_radio = wx.RadioButton(self.panel, -1, u"私有", pos=(200, 70))

        if self.currentCollection['favorite_info']['public']:
            self.public_radio.SetValue(True)
            self.public_radio.Enable(False)
            self.private_radio.SetValue(False)
            self.private_radio.Enable(False)
        else:
            self.public_radio.SetValue(False)
            self.private_radio.SetValue(True)

        self.createButton = wx.Button(self.panel, -1, u"修改", pos=(150, 90))
        self.Bind(wx.EVT_BUTTON, self.OnLoginButtonClick, self.createButton)
        self.createButton.SetDefault()

        self.Center()

    def OnLoginButtonClick(self, event):
        self.createButton.SetLabel(u"修改中...")
        title = self.favorite_title.GetValue()
        is_public = self.public_radio.GetValue()
        description = self.desc_text.GetValue()
        if title is None or len(title) <= 0:
            self.showMessageBox(u'收藏夹名称不能为空!')
            self.createButton.SetLabel(u"修改")
            return

        for collection in self.userCollections:
            if cmp(collection['title'], title) == 0 and self.currentCollection['favorite_info']['favorite_id'] != collection['favorite_info']['favorite_id']:
                self.showMessageBox(u'收藏夹[%s]已存在!' % title)
                self.createButton.SetLabel(u"修改")
                return

        result = Utils.editCollection(title, self.currentCollection['favorite_info']['favorite_id'], is_public, description)
        if result['status']:
            self.showMessageBox(u'修改成功')
            self.EndModal(wx.ID_OK)
        else:
            self.showMessageBox(u'修改失败')
        self.createButton.SetLabel(u"修改")

class Singleton(object):
    def __new__(cls,*args,**kwargs):
        if not hasattr(cls,'_inst'):
            cls._inst=super(Singleton,cls).__new__(cls,*args,**kwargs)
        return cls._inst

class TaskExecutor(threading.Thread, Singleton):
    def __init__(self, callback=None, progress_callback=None):
        threading.Thread.__init__(self)
        self.taskQueue = Queue()
        self.callback = callback
        self.progress_callback = progress_callback
        self.timeToQuit = threading.Event()
        self.timeToQuit.clear()

    def stop(self):
        self.timeToQuit.set()

    def run(self):
        while True:
            if self.taskQueue.qsize() <= 0:
                if self.timeToQuit.isSet():
                    break
                time.sleep(1)
            else:
                taskItem = self.taskQueue.get()
                status = {'status': False, 'msg': 'No action id found'}
                try:
                    if taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_DELETE:  # 取消收藏
                        status = Utils.remove_favorite(
                            taskItem['selected_answer']['answer_id'],
                            taskItem['from_collection_info']['favorite_info']['favorite_id'])
                    elif taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START:  # 移动
                        status = Utils.move_favorite(
                            taskItem['selected_answer']['answer_id'],
                            taskItem['from_collection_info']['favorite_info']['favorite_id'],
                            taskItem['dest_collecion_info']['favorite_id'])
                    elif taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START:  # 复制
                        status = Utils.copy_favorite(
                            taskItem['selected_answer']['answer_id'],
                            taskItem['from_collection_info']['favorite_info']['favorite_id'],
                            taskItem['dest_collecion_info']['favorite_id'])
                    elif taskItem['action']['id'] == ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_HTML:  # 导出
                        status = Utils.export_collections(taskItem['export_collections'], self.progress_callback)
                    elif taskItem['action']['id'] == ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8:  # 导出
                        status = Utils.export_collections_chm(taskItem['export_collections'], self.progress_callback)
                    if self.callback is not None:
                        self.callback(status, taskItem)
                except Exception,e:
                    print Exception,":",e
                    traceback.print_exc()
                    status['msg'] = traceback.format_exc()
                    if self.callback is not None:
                        self.callback(status, taskItem)

    def add_task(self, taskItem):
        self.taskQueue.put(taskItem)


class ZhihuStatusBar(wx.StatusBar):
    def __init__(self, *args, **kwds):
        wx.StatusBar.__init__(self, *args, **kwds)
        self.basicLabel = wx.StaticText(self, -1, u"", pos=(5, 5))

    def setText(self, text):
        self.basicLabel.SetLabel(text)

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

        self.baseBoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.baseBoxSizer.Add(
            self.panel,
            proportion=1,
            flag=wx.ALL | wx.EXPAND,
            border=0)
        self.SetSizer(self.baseBoxSizer)

        self.statusBar = ZhihuStatusBar(self)
        self.SetStatusBar(self.statusBar)
        self.statusBar.Hide()

        self.menuBar_menubar_menu_items = [
            {'id': ControlID.MENUBAR_MENU_ITEM_REFRESH, 'title': u'刷新', 'separator': True, 'IsShown': lambda : True},
            {'id': ControlID.MENUBAR_MENU_ITEM_CREATE, 'title': u'新建收藏夹', 'separator': True, 'IsShown': lambda : True},
            {'id': ControlID.MENUBAR_MENU_ITEM_SHOW_STATUSBAR, 'title': u'隐藏状态栏', 'separator': True, 'IsShown': lambda : self.statusBar.IsShown()},
            {'id': ControlID.MENUBAR_MENU_ITEM_HIDE_STATUSBAR, 'title': u'显示状态栏', 'separator': True, 'IsShown': lambda : not self.statusBar.IsShown()},
            {'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL, 'title': u'导出所有', 'separator': True, 'IsShown': lambda : True,
                'hasSub': True,
                'sub' : [{'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8, 'title': u"导出为CHM(UTF-8)"},
                         {'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_GBK, 'title': u"导出为CHM(GBK)", 'IsShown': lambda : False},
                         {'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_HTML, 'title': u"导出为HTML"}]},
            {'id': ControlID.MENUBAR_MENU_ITEM_QUIT, 'title': u'退出', 'separator': False, 'IsShown': lambda : True}
            ]

        self.menuBar_menuBar = wx.MenuBar()
        self.SetMenuBar(self.menuBar_menuBar)
        self.UpdaetMenuBarMenu()

        self.collections_menu_itemms = [
            {'id': ControlID.COLLECTION_LIST_MENU_OPEN, 'title': u"打开"},
            {'id': ControlID.COLLECTION_LIST_MENU_RENAME, 'title': u"编辑收藏夹"},
            {'id': ControlID.COLLECTION_LIST_MENU_EXPORT, 'title': u"导出", 'hasSub': True,
                'sub' : [{'id': ControlID.COLLECTION_LIST_MENU_EXPORT_CHM_UTF8, 'title': u"导出为CHM(UTF-8)"},
                         {'id': ControlID.COLLECTION_LIST_MENU_EXPORT_CHM_GBK, 'title': u"导出为CHM(GBK)", 'IsShown': lambda : False},
                         {'id': ControlID.COLLECTION_LIST_MENU_EXPORT_HTML, 'title': u"导出为HTML"}]},
            {'id': ControlID.COLLECTION_LIST_MENU_DELETE, 'title': u"删除"}
            ]

        # create the list control
        self.ListCtrl_CollectionList = wx.ListCtrl(
            self.panel,
            -1,
            style=wx.LC_REPORT)

        self.ListCtrl_CollectionList_imgs = wx.ImageList(16, 16, True)
        self.ListCtrl_CollectionList_imgs.Add(images_icon.LockIcon.GetBitmap())
        self.ListCtrl_CollectionList.AssignImageList(self.ListCtrl_CollectionList_imgs, wx.IMAGE_LIST_SMALL)

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

        self.favorites_list_menu_copy_to = []
        self.favorites_list_menu_move_to = []

        # init collection answers list
        self.collections_answers_menu_items = [
            {'id': ControlID.ANSWER_LIST_MENU_BROWSE, 'title': u"浏览"},
            {'id': ControlID.ANSWER_LIST_MENU_BROWSE_COPY, 'title': u"复制到", 'hasSub': True,
                'sub': self.favorites_list_menu_copy_to},
            {'id': ControlID.ANSWER_LIST_MENU_BROWSE_MOVE, 'title': u"移动到", 'hasSub': True,
                'sub': self.favorites_list_menu_move_to},
            {'id': ControlID.ANSWER_LIST_MENU_BROWSE_DELETE, 'title': u"取消收藏"},
        ]

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
            self.ListCtrl_TaskList.SetColumnWidth(col, 40)
        self.tasklist_items = []

        self.horizontalBoxSizer.Add(
            self.ListCtrl_TaskList,
            proportion=1,
            flag=wx.ALL | wx.EXPAND,
            border=5)

        self.OnMenuRefresh()

        self.status_msg = {}
        self.status_msg[True] = u'成功'
        self.status_msg[False] = u'失败'

        # init task queue
        self.taskExecutor = TaskExecutor(self.OnTaskFinish, self.OnTaskProgress)
        self.taskExecutor.start()

        # create tmpfile
        self.temp_dir_path = tempfile.mkdtemp()

        self.panel.SetSizer(self.horizontalBoxSizer)
        self.horizontalBoxSizer.Fit(self.panel)
        self.Layout()
        self.Center()

    def SetStatusBarText(self, text):
        if not self.statusBar.IsShown():
            self.statusBar.Show()
            self.UpdaetMenuBarMenu()
            self.SendSizeEvent()
        self.statusBar.setText(text)

    def OnTaskProgress(self, status):
        wx.CallAfter(self.ProcProgessMsg, status)

    def ProcProgessMsg(self, status):
        self.SetStatusBarText(u"正在处理: " +status['msg'])
        
    def OnTaskFinish(self, status, taskItem):
        if taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_DELETE:
            wx.CallAfter(self.ProcTaskFinish, status, taskItem)
        elif taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START:
            wx.CallAfter(self.ProcTaskFinish, status, taskItem)
        elif taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START:
            wx.CallAfter(self.ProcTaskFinish, status, taskItem)
        elif taskItem['action']['id'] == ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_HTML:
            wx.CallAfter(self.ProcExportFinish, status, taskItem)
        elif taskItem['action']['id'] == ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8:
            wx.CallAfter(self.ProcExportFinish, status, taskItem)

    def ProcTaskFinish(self, status, taskItem):
        answer_string = "回答编号:%s(%s),作者:%s,问题标题:%s,编号:%s(%s),收藏夹名称:%s,编号:%s(%s)" % (
            taskItem['selected_answer']['answer_id'], u'http://www.zhihu.com/answer/%s' % taskItem['selected_answer']['answer_id_url'], taskItem['selected_answer']['author_name'],
            taskItem['selected_answer']['question_title'],
            taskItem['selected_answer']['question_id'], u'http://www.zhihu.com/question/%s' % taskItem['selected_answer']['question_id'],
            taskItem['from_collection_info']['title'],
            taskItem['from_collection_info']['favorite_info']['favorite_id'], u"http://www.zhihu.com/collection/%s" % taskItem['from_collection_info']['collection_id'])
        answer_string = "%s%s, %s, %s" % (taskItem['action']['name'], self.status_msg[status['status']], answer_string, status['msg'])
        logger.info(answer_string)

        if taskItem in self.tasklist_items:
            taskItem['status'] = self.status_msg[status['status']]
            self.SetStatusBarText(u"%s%s %s" % (taskItem['status'], taskItem['action']['name'], taskItem['col2']))
        self.UpdateTaskList()

        if taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START:
            self.DeleteAnswerFromAnswerList(taskItem['selected_answer']['answer_id'])
        elif taskItem['action']['id'] == ControlID.ANSWER_LIST_MENU_BROWSE_DELETE:
            self.DeleteAnswerFromAnswerList(taskItem['selected_answer']['answer_id'])

    def ProcExportFinish(self, status, taskItem):
        if taskItem in self.tasklist_items:
            taskItem['status'] = self.status_msg[status['status']]
            self.SetStatusBarText(u"%s导出 %s" % (taskItem['status'], taskItem['col2']))
        self.UpdateTaskList()

    def __del__(self):
        os.removedirs(self.temp_dir_path)
        self.taskExecutor.stop()
        wx.Frame.__del__(self)

    def UpdaetMenuBarMenu(self):
        self.menuBar_menu = self.BuildMenuItems(self.menuBar_menubar_menu_items, self.OnMenubarMenu_Select)

        index = self.menuBar_menuBar.FindMenu(u'菜单')
        if index != wx.NOT_FOUND:
            self.menuBar_menuBar.Replace(index, self.menuBar_menu, u'菜单')
        else:
            self.menuBar_menuBar.Append(self.menuBar_menu, u"菜单")

    def _clear_list(self, _list_data):
        for i in range(len(_list_data) - 1, -1, -1):
            _list_data.pop(i)

    def UpdateFavoriteList(self):
        # clear list
        self._clear_list(self.favorites_list_menu_copy_to)
        self._clear_list(self.favorites_list_menu_move_to)
        logger.info("Utils.getUserFavoriteList()")
        idx = 0
        for favorite in self.userFavorites:
            c_item = {'id': ControlID.ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START + idx,
                        'title': favorite['title'], 'data': favorite}
            self.favorites_list_menu_copy_to.append(c_item)
            m_item = {'id': ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START + idx,
                        'title': favorite['title'], 'data': favorite}
            self.favorites_list_menu_move_to.append(m_item)
            idx += 1

    def OnMenuRefresh(self):
        # refresh
        self.userCollections = list(Utils.getUserCollectionList())
        self.userFavorites = list(Utils.getUserFavoriteList())
        print 'len: %d' % len(self.userFavorites)
        for coll in self.userCollections:
            for fav in self.userFavorites:
                if cmp(coll['title'], fav['title']) == 0:
                    coll['favorite_info'] = fav
                    print coll, fav
        self.UpdateCollectionList()
        self.UpdateFavoriteList()

    def OnMenubarMenu_Select(self, event, menu_item, path):
        id = event.GetId()
        logger.info('%s(%s) clicked' % (menu_item, id))
        if id == ControlID.MENUBAR_MENU_ITEM_QUIT:
            self.Close()
        elif id == ControlID.MENUBAR_MENU_ITEM_REFRESH:
            self.OnMenuRefresh()
            # clear answer list
            self.ListCtrl_CollectionAnswersList.DeleteAllItems()
        elif id == ControlID.MENUBAR_MENU_ITEM_CREATE:
            dlg = CreateFavoriteDialog(self.userCollections)
            if wx.ID_OK == dlg.ShowModal():
                self.OnMenuRefresh()
            dlg.Destroy()
        elif id == ControlID.MENUBAR_MENU_ITEM_SHOW_STATUSBAR:
            self.statusBar.Hide()
            self.UpdaetMenuBarMenu()
            self.SendSizeEvent()
            #wx.PostEvent(self.GetEventHandler(), wx.SizeEvent(self.GetSize(), self.GetId()))
        elif id == ControlID.MENUBAR_MENU_ITEM_HIDE_STATUSBAR:
            self.statusBar.Show()
            self.UpdaetMenuBarMenu()
            self.SendSizeEvent()
            #wx.PostEvent(self.GetEventHandler(), wx.SizeEvent(self.GetSize(), self.GetId()))
        elif id == ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8:
            collections = list(Utils.getUserCollectionList())
            action = { 'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8, 'name': u'导出收藏(CHM)'}
            self.AddTaskItem(action, export_collections=collections)
            self.UpdateTaskList()
        elif id == ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_GBK:
            pass
        elif id == ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_HTML:
            collections = list(Utils.getUserCollectionList())
            action = { 'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_HTML, 'name': u'导出收藏'}
            self.AddTaskItem(action, export_collections=collections)
            self.UpdateTaskList()

    def AddTaskItem(self, action, selected_answer=None, from_collection_info=None, dest_collecion_info=None, export_collections=None):
        item = {}
        item['action'] = action
        item['selected_answer'] = selected_answer
        item['from_collection_info'] = from_collection_info
        item['dest_collecion_info'] = dest_collecion_info
        item['export_collections'] = export_collections
        item['col2'] = ""
        item['col3'] = ""
        item['col4'] = ""

        switch_group1 = [
                        ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START,
                        ControlID.ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START
                        ]
        switch_group2 = [
                        ControlID.ANSWER_LIST_MENU_BROWSE_DELETE
                        ]
        switch_group3 = [
                        ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_HTML,
                        ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8
                        ]
        if action['id'] in switch_group1:
            item['col2'] = u"%s回答的关于 %s:%s" % (item['selected_answer']['author_name'], item['selected_answer']['question_title'], item['selected_answer']['answer_summary'])
            item['col3'] = item['from_collection_info']['title']
            item['col4'] = item['dest_collecion_info']['title']
        elif action['id'] in switch_group2:
            item['col2'] = u"%s回答的关于 %s:%s" % (item['selected_answer']['author_name'], item['selected_answer']['question_title'], item['selected_answer']['answer_summary'])
            item['col3'] = item['from_collection_info']['title']
            #item['col4'] = item['dest_collecion_info']['title']
        elif action['id'] in switch_group3:
            fname = ""
            if len(export_collections) > 1:
                fname = u"%s,%s等%d个收藏夹" % (export_collections[0]['title'], export_collections[1]['title'], len(export_collections))
            else:
                fname = export_collections[0]['title']
            item['col2'] = fname

        self.tasklist_items.insert(0, item)
        #logger.info("item added: %s" % item)
        self.taskExecutor.add_task(item)

    def UpdateTaskList(self):
        self.TaskItemsDataMap = {}
        self.ListCtrl_TaskList.DeleteAllItems()
        for item in self.tasklist_items:
            index = self.ListCtrl_TaskList.InsertStringItem(sys.maxint, item['action']['name'])
            if 'status' in item:
                self.ListCtrl_TaskList.SetStringItem(index, 1, item['status'])
            else:
                self.ListCtrl_TaskList.SetStringItem(index, 1, "")
            self.ListCtrl_TaskList.SetStringItem(index, 2, item['col2'])
            self.ListCtrl_TaskList.SetStringItem(index, 3, item['col3'])
            self.ListCtrl_TaskList.SetStringItem(index, 4, item['col4'])
            self.TaskItemsDataMap[item['action']['name']] = item

        self.ListCtrl_TaskList.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.ListCtrl_TaskList.SetColumnWidth(1, 40)
        self.ListCtrl_TaskList.SetColumnWidth(2, 230)
        self.ListCtrl_TaskList.SetColumnWidth(3, wx.LIST_AUTOSIZE)
        self.ListCtrl_TaskList.SetColumnWidth(4, wx.LIST_AUTOSIZE)

    def UpdateCollectionAnswersList(self, collection_id):
        self.Current_Shown_Answers = list(Utils.getAnswersInCollection(collection_id))
        self.BuildCollectionAnswersList(self.Current_Shown_Answers)

    def BuildCollectionAnswersList(self, answers):
        self.AnswersItemsDataMap = {}
        self.ListCtrl_CollectionAnswersList.DeleteAllItems()
        for item in answers:
            index = self.ListCtrl_CollectionAnswersList.InsertStringItem(sys.maxint, item['answer_id'])
            self.ListCtrl_CollectionAnswersList.SetStringItem(index, 1, item['question_title'])
            self.ListCtrl_CollectionAnswersList.SetStringItem(index, 2, item['author_name'])
            self.ListCtrl_CollectionAnswersList.SetStringItem(index, 3, item['answer_summary'])
            self.AnswersItemsDataMap[item['answer_id']] = item
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(1, 220)
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(2, wx.LIST_AUTOSIZE)
        self.ListCtrl_CollectionAnswersList.SetColumnWidth(3, wx.LIST_AUTOSIZE)

    def DeleteAnswerFromAnswerList(self, answer_id):
        itemToBeDeleted = None
        for item in self.Current_Shown_Answers:
            if cmp(item['answer_id'], answer_id) == 0:
                itemToBeDeleted = item
        if itemToBeDeleted is not None:
            self.Current_Shown_Answers.remove(itemToBeDeleted)
            self.BuildCollectionAnswersList(self.Current_Shown_Answers)

    def GetSelectedAnswer(self):
        return self.AnswersItemsDataMap[self.ListCtrl_CollectionAnswersList_item_clicked]

    def GetSelectedAnswers(self):
        selected_answers = []
        current_item_idx = -1
        while True:
            current_item_idx = self.ListCtrl_CollectionAnswersList.GetNextSelected(current_item_idx)
            if current_item_idx != -1:
                selected_answers.append(self.AnswersItemsDataMap[self.ListCtrl_CollectionAnswersList.GetItemText(current_item_idx)])
            else:
                break
        return selected_answers

    def GetSelectedCollection(self):
        return self.collectionsItemsDataMap[self.ListCtrl_CollectionList_item_clicked]

    def OnCollectionAnswersListDoubleClick(self, event):
        self.ListCtrl_CollectionAnswersList_item_clicked = event.GetText()
        selected_answer = self.GetSelectedAnswer()
        # logger.info('OnCollectionAnswersListDoubleClick - %s' % selected_answer)

        self.showHtml2(selected_answer['full_page'], selected_answer['full_title'])

    def OnCollectionAnswersListRightClick(self, event):
        self.ListCtrl_CollectionAnswersList_item_clicked = event.GetText()

        menu = self.BuildMenuItems(self.collections_answers_menu_items, self.OnAnswerMenuSelect)
        self.PopupMenu(menu, event.GetPoint())
        menu.Destroy()

    def OnAnswerMenuSelect(self, event, item, path):
        print event,item
        logger.info(u"=>".join([u"%s(%d)" % (p['title'], p['id']) for p in path]))
        selected_answer = self.GetSelectedAnswer()
        if event.GetId() == ControlID.ANSWER_LIST_MENU_BROWSE:
            #logger.info('OnCollectionAnswersListDoubleClick - %s' % selected_answer)

            self.showHtml2(selected_answer['full_page'], selected_answer['full_title'])
        elif event.GetId() == ControlID.ANSWER_LIST_MENU_BROWSE_DELETE:
            action = { 'id': event.GetId(), 'name': u'取消收藏'}
            from_collection_info = self.GetSelectedCollection()
            for selected_answer in self.GetSelectedAnswers():
                self.AddTaskItem(action, selected_answer, from_collection_info)
            self.UpdateTaskList()
        elif ControlID.ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START <= event.GetId() < ControlID.ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_END:
            action = { 'id': ControlID.ANSWER_LIST_MENU_BROWSE_COPY_SUBMENU_START, 'name': u'复制'}
            from_collection_info = self.GetSelectedCollection()
            dest_collecion_info = item['data']
            for selected_answer in self.GetSelectedAnswers():
                self.AddTaskItem(action, selected_answer, from_collection_info, dest_collecion_info)
            self.UpdateTaskList()
        elif ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START <= event.GetId() < ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_END:
            action = { 'id': ControlID.ANSWER_LIST_MENU_BROWSE_MOVE_SUBMENU_START, 'name': u'移动'}
            from_collection_info = self.GetSelectedCollection()
            dest_collecion_info = item['data']
            for selected_answer in self.GetSelectedAnswers():
                self.AddTaskItem(action, selected_answer, from_collection_info, dest_collecion_info)
            self.UpdateTaskList()

    def UpdateCollectionList(self):
        self.collectionsItemsDataMap = {}
        self.ListCtrl_CollectionList.DeleteAllItems()
        for item in self.userCollections:
            index = self.ListCtrl_CollectionList.InsertStringItem(sys.maxint, item['title'])
            if not item['favorite_info']['public']:
                self.ListCtrl_CollectionList.SetItemImage(index, 0, 0)
            self.collectionsItemsDataMap[item['title']] = item
        self.ListCtrl_CollectionList.SetColumnWidth(0, 175)  # wx.LIST_AUTOSIZE

    def OnCollectionListDoubleClick(self, event):
        self.ListCtrl_CollectionList_item_clicked = event.GetText()
        selected_item = self.GetSelectedCollection()
        logger.info('OnCollectionListDoubleClick - %s' % selected_item)
        self.UpdateCollectionAnswersList(selected_item['collection_id'])

    def OnCollectionListRightClick(self, event):
        self.ListCtrl_CollectionList_item_clicked = event.GetText()

        menu = self.BuildMenuItems(self.collections_menu_itemms, self.OnMenuSelect_CollectionList)
        self.PopupMenu(menu, event.GetPoint())
        menu.Destroy()

    def BuildMenuItems(self, menu_items, callback, root=None, path=None):
        '''
        menu_items = [
            {'id': id_1, 'title': u"title"},
            {'id': id_2, 'title': u"title2", 'hasSub': True,
                'sub': [
                    {'id': sub_id_1, 'title': u"sub title 1"},
                    {'id': sub_id_2, 'title': u"sub title 2"},
                    ]},
        ]
        '''
        if root is None:
            root = wx.Menu()
            menu = root
        else:
            menu = wx.Menu()
        if path is None:
            path = []

        for item in menu_items:
            if item.has_key('IsShown') and item['IsShown']() == False:
                pass
            else:
                if item.has_key('hasSub') and item['hasSub']:
                    t_path = [x for x in path]
                    t_path.append(item)
                    sub_menu = self.BuildMenuItems(item['sub'], callback, self, t_path)
                    menu.AppendSubMenu(sub_menu, item['title'])
                else:
                    menu.Append(item['id'], item['title'])
                    t_path = [x for x in path]
                    t_path.append(item)
                    wx.EVT_MENU(self, item['id'], lambda event, temp_item=item, temp_path=t_path: callback(event, temp_item, temp_path))
                if item.has_key('separator') and item['separator']:
                    menu.AppendSeparator()

        return menu

    def OnMenuSelect_CollectionList(self, event, item, path):
        selected_item = self.GetSelectedCollection()
        logger.info('Perform "%s" on "%s."' % (item['title'], selected_item))
        if event.GetId() == ControlID.COLLECTION_LIST_MENU_OPEN: # 打开
            self.UpdateCollectionAnswersList(selected_item['collection_id'])
        elif event.GetId() == ControlID.COLLECTION_LIST_MENU_EXPORT_HTML:
            dummy_items = []
            dummy_items.append(selected_item)
            action = { 'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_HTML, 'name': u'导出收藏'}
            self.AddTaskItem(action, export_collections=dummy_items)
            self.UpdateTaskList()
        elif event.GetId() == ControlID.COLLECTION_LIST_MENU_EXPORT_CHM_UTF8:
            dummy_items = []
            dummy_items.append(selected_item)
            action = { 'id': ControlID.MENUBAR_MENU_ITEM_EXPORT_ALL_CHM_UTF8, 'name': u'导出收藏(CHM)'}
            self.AddTaskItem(action, export_collections=dummy_items)
            self.UpdateTaskList()
        elif event.GetId() == ControlID.COLLECTION_LIST_MENU_DELETE:
            dlg = wx.MessageDialog(None, u"确认删除[%s]?" % selected_item['title'], u"提示", style=wx.OK)
            if dlg.ShowModal() == wx.ID_YES:
                self.Close(True)
                result = Utils.deleteCollection(selected_item['favorite_info']['favorite_id'])
                if result['status']:
                    self.OnMenuRefresh()
                    self.showMessageBox(u"删除收藏夹成功")
                else:
                    self.showMessageBox(u"删除收藏夹失败")
        elif event.GetId() == ControlID.COLLECTION_LIST_MENU_RENAME:
            dlg = EditFavoriteDialog(selected_item, self.userCollections)
            if wx.ID_OK == dlg.ShowModal():
                self.OnMenuRefresh()
            dlg.Destroy()

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
                self.browser = wx.html2.WebView.New(self.panel, pos=(10, 10), size=(800, 580))
                self.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.OnPageLoad, self.browser)
                internal_sizer = wx.BoxSizer(wx.VERTICAL)
                internal_sizer.Add(self.browser, 1, wx.EXPAND, 15)
                self.panel.SetSizer(internal_sizer)

                self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyUP)

                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(self.panel, 1, wx.EXPAND, 10)
                self.SetSizer(sizer)
                internal_sizer.Fit(self.panel)
                self.Center()

            def OnPageLoad(self, event):
                self.WebTitle = self.browser.GetCurrentTitle()
                self.SetTitle(self.WebTitle)

            def SetTitleContent(self, title):
                if title is not None and len(title.strip()) > 0:
                    self.title = title
                    self.SetTitle(self.title)

            def OnKeyUP(self, event):
                keyCode = event.GetKeyCode()
                if keyCode == wx.WXK_ESCAPE:
                    self.Close()

        dialog = AnswerBrowser(None, -1, size=(840, 600))
        dialog.browser.SetPage(content, "")
        dialog.SetTitleContent(title)
        dialog.Show()

if __name__ == '__main__':
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
