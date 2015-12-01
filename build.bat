@ECHO OFF
@pyinstaller -w -F -i ./zhihu.ico ./zhihu-favorites-mgr.py
@copy dist\zhihu-favorites-mgr.exe .
@rd /S /Q build\
@rd /S /Q dist\
@pause
