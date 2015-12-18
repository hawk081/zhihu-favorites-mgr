zhihu-favorites-mgr 管理知乎收藏夹内容,复制/移动/删除/导出(HTML/CHM)
===============================

:Author: `hawk081 <https://github.com/hawk081>`_ ( `邮箱 <hawk081@126.com>`_ )
:Update: 12/13/12015


.. contents::


介绍
----

只因为知乎网页/App的收藏夹管理不太能使用, 便利用Python2.7.6写了此工具来方便收藏夹的管理,此工具不但可以方便整理收藏夹,还能将收藏夹的内容导出,以供离线查看.

主要功能:

+ 收藏夹管理
    + 打开
    + 重命名
    + 删除
+ 答案管理
    + 浏览
    + 复制
    + 移动
    + 取消收藏
+ 导出
    + 导出所选收藏夹为HTML
    + 导出所选收藏夹为CHM(UTF-8)
    + 导出所有收藏夹为HTML
    + 导出所有收藏夹为CHM(UTF-8)

**注: 本项目代码均在 Windows 7上使用 python2.7.6 编写和测试通过，其他环境未做测试。**

准备工作
---------


**通过可执行文件运行** :

1. 下载 `deliverable/zhihu-favorites-mgr.exe <https://github.com/hawk081/downloads/blob/master/zhihu-favorites-mgr/zhihu-favorites-mgr.exe>`_ (启动有点慢 - - !)

**通过代码运行** :

1.  确保你的系统里面已经安装了 `Python2.7 <https://www.python.org/>`_ ，不同作业系统如何安装不再赘述。
2.  检查你系统中 `python` 和 `pip` 的版本, 如果不属于 `python2.7` , 请在执行代码范例时，自行将 `python` 和 `pip` 分别替换成 `python2.7` 和 `pip2` 。
3.  确保你的系统中安装了 `git` 程序 以及 `python-pip` 。


**克隆本项目**


.. code:: bash

  git clone https://github.com/hawk081/zhihu-favorites-mgr.git
  cd zhihu-favorites-mgr


**解决依赖**

* `wxPython <http://www.wxpython.org/>`_
* `Beautiful Soup 4 <http://www.crummy.com/software/BeautifulSoup/>`_
* `requests <https://github.com/kennethreitz/requests>`_
* `html2text <https://github.com/aaronsw/html2text>`_
* `html5lib <http://lxml.de/html5parser.html>`_


.. code:: bash

  sudo pip install -r requirements.txt


or

.. code:: bash

  sudo pip2 install -r requirements.txt


功能介绍
---------


登录
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/login.png


界面
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/main_frame.png

+ 区域①: 当前账号所有收藏夹
+ 区域②: 当前收藏夹中所有收藏的回答
+ 区域③: 操作以及操作结果

收藏夹操作
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/collection_menu.png

+ 打开收藏夹
    + 双击收藏夹
    + 右键 -> 打开
+ 新建收藏夹
+ 编辑收藏夹
+ 导出收藏夹
    + 导出为CHM(UTF-8)
    + 导出为HTML
+ 删除 - 删除收藏夹

管理答案
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/answer_menu.png

+ 浏览 - 通使用自带的窗口查看
+ 复制到 - 复制所选答案到目标收藏夹
+ 移动到 - 移动所选答案到目标收藏夹, 当前收藏夹内该答案讲会被删除
+ 取消收藏 - 取消收藏该答案


功能展示
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
+ 浏览答案内容
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/answer_review.png

+ 导出为HTML
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/export_html_review.png

+ 导出为CHM
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/export_chm_review.png

+ 导出所有
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/main_menu.png

+ 查看所有导出结果
.. image:: https://github.com/hawk081/zhihu-favorites-mgr/blob/master/screenshots/export_result.png


TODO List
----------
+ 导出为PDF
+ 导出为EPUB
+ 查看某用户的所有回答
+ 导出某用户的所有回答
+ 查看某公开收藏夹的所有回答
+ 导出某公开收藏夹的所有回答

感谢
----------
- `egrcc <https://github.com/egrcc>`_ `zhihu-python <https://github.com/egrcc/zhihu-python>`_

联系我
----------

- github：https://github.com/hawk081
- email：hawk081@126.com
