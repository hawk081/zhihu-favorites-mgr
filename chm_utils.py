# -*- coding: utf-8 -*-

import os
import sys
import traceback
import subprocess

try:
    from bs4 import BeautifulSoup
    import bs4
except:
    import BeautifulSoup

from chm_template import *

class CHMUtils:
    @staticmethod
    def get_child_collection_directory_name(html_file, base_dir=u"."):
        try:
            html_file_path = u"%s/%s" % (base_dir, html_file)
            soup = BeautifulSoup(open(html_file_path), 'html5lib')
            folders = soup.find_all("span", class_="folder")
            return [folder.string for folder in folders]
        except Exception,e:
            print Exception,":",e
            traceback.print_exc()
            return None
    @staticmethod
    def get_child_collection_files(directory_name, base_dir="."):
        files = CHMUtils.get_files("%s/%s" % (base_dir, directory_name))
        # convert to relative path
        files = [file.replace(base_dir, u".") for file in files]
        return files

    @staticmethod
    def get_files(topdir):
        for dirpath, dirnames, files in os.walk(topdir):
            for name in files:
                yield os.path.join(dirpath, name).replace(u'\\', u'/')

class CHMFile:
    def __init__(self, html_path):
        (self.base_dir, self.html_file) = os.path.split(html_path)
        self.collection_file_name = self.html_file[0:self.html_file.rfind('.')]
        self.chm_hhp_name = "%s.hhp" % self.collection_file_name
        if len(self.base_dir) <= 0:
            self.base_dir = "."
        print self.base_dir, self.html_file
        self.folders = CHMUtils.get_child_collection_directory_name(self.html_file, self.base_dir)
        self.files = []
        for folder in self.folders:
            self.files.extend(CHMUtils.get_child_collection_files(folder, self.base_dir))
        content_files = "\n".join(self.files)

        self.chm_hhp = chm_hhp_template.replace(u"{collection_file_name}", self.collection_file_name)
        self.chm_hhp = self.chm_hhp.replace("{default_topic}", self.html_file)
        self.chm_hhp = self.chm_hhp.replace("{content_files}", content_files)

    def build(self):
        hpp_full_name = "%s/%s" % (self.base_dir, self.chm_hhp_name)
        with open(hpp_full_name, "w") as fhndl:
            fhndl.write(self.chm_hhp.encode('cp936'))
        
        hhc_file_path = r'C:\\Program Files (x86)\\HTML Help Workshop\\hhc.exe'
        if not os.path.exists(hhc_file_path.replace("\\", "/")):
            hhc_file_path = r'C:\\Program Files\\HTML Help Workshop\\hhc.exe'
            if not os.path.exists(hhc_file_path.replace("\\", "/")):
                raise ValueError("Set path of 'hhc.exe'")

        cmd = r'"%s" %s' % (hhc_file_path, hpp_full_name.encode('cp936'))
        os.system(cmd)
        os.remove(hpp_full_name)

        return {"fname": "%s.chm" % self.collection_file_name}

if __name__ == '__main__':
    CHMFile(u"./export/哈.html").build()
    exit(0)
    folders = CHMUtils.get_child_collection_directory_name(u"哈.html", u"./export")
    if folders is not None:
        print folders
        for folder in folders:
            for file in CHMUtils.get_files(u"./export/" + folder):
                print file
