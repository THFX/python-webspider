# -*- coding: UTF-8 -*-
import requests
import re
import os
import time
import decrypt

# Some vars
SaveErrUrl = True
SaveImgUrl = True
DirPath = "./Downloads/"  # 注意以 / 结尾


class Spider:
    def __init__(self):
        global url
        self.hea = {
            "Accept-Encoding": "gzip, deflate",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
        }
        self.hea_download = {
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Referer": "",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
        }
        self.title = ""  # 初始化 存储图片的目录名 后续会根据网页赋值为 “第xx话”
        self.dirpath = DirPath  # 初始化 存储图片的一级路径
        self.dirpath_sub = ""  # 初始化 存储图片的二级路径 实际上后续会被赋值为：self.dirpath + self.title

    def get_info(self, _url):
        """
        :param _url: 需要获取加密文本的目标网页url
        :return: 若无异常，返回一个列表["加密文本","第xx话"], 若出现异常，返回 1
        """
        hea = self.hea
        encrypted_text = 1
        err_status = 0
        retry_n = 0
        while retry_n <= 3:
            if retry_n != 0:
                print("Retry: ", retry_n)
            try:
                res = requests.get(url=_url, headers=hea, timeout=5)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
                print("Timeout")
                err_status = 1
                retry_n += 1
                print("10s后继续...")
                # time.sleep(5)  # debug only
                time.sleep(10)
            except Exception as err_info:
                print("Error\n", err_info)
                err_status = 2
                retry_n += 1
                print("15s后继续...")
                # time.sleep(5)  # debug only
                time.sleep(15)
            else:
                # 以下的if是为了“链接无异常，而网站异常”的情况设置的
                if "error" in res.text:
                    print("Website seems down!")
                    err_status = 3
                    retry_n += 1
                    print("20s后继续...")
                    # time.sleep(5)  # debug only
                    time.sleep(20)
                elif "正在升级" in res.text:
                    print("网页提示：“网站正在升级”  可能为访问过于频繁导致")
                    err_status = 3
                    retry_n += 1
                    print("30s后继续...")
                    # time.sleep(5)  # debug only
                    time.sleep(30)
                else:
                    err_status = 0
                    self.title = re.findall(r"<title>(.*?)</title>", res.text)[0]
                    self.title = re.sub(r"_.*", "", self.title)  # 设置标题（通常是 第xx话），作为下边新建文件夹的名称
                    encrypted_text = re.findall(r"var km5_img_url='(.*?)'", res.text)[0]
                    break
        if err_status != 0:
            if SaveErrUrl:
                errurl_file = open(self.dirpath + "errors.txt", "a")
                errurl_file.write(_url + "\n")
                errurl_file.close()
            return 1
        else:
            self.mkdir_and_setpath()  # 建立下载文件夹并初始化下载路径
            return encrypted_text, self.title

    def mkdir_and_setpath(self):
        """
        This function will make dirs to save files and set some vars about path
        You must run it before save_imgurl() and downlload()
        :return:
        """
        if not os.path.exists(self.dirpath):
            os.mkdir(self.dirpath)
        self.dirpath_sub = self.dirpath + self.title + "/"  # 设置 存储图片的二级路径
        if not os.path.exists(self.dirpath_sub):
            os.mkdir(self.dirpath_sub)

    def save_imgurl(self, _imgurls):
        """
        :param _imgurls: 接受一个下载地址列表，将其逐行写入文件
        :return: 无
        """
        imgurl_file = open(self.dirpath_sub + "url.txt", "w+", encoding='utf-8')
        for each in _imgurls:
            imgurl_file.write(each + "\n")
        imgurl_file.close()

    def download(self, _url, _count):
        hea = self.hea_download
        hea["Referer"] = url
        err_status = 0
        retry_n = 0
        while retry_n <= 3:
            if retry_n != 0:
                print("Retry: ", retry_n)
            try:
                pic = requests.get(_url, headers=hea, timeout=60)
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
                print("Image:%d Timeout!" % count)
                err_status = 1
                retry_n += 1
                print("10s后继续...")
                # time.sleep(5)  # debug only
                time.sleep(10)
            except Exception:
                print("Image:%d Error!" % count)
                err_status = 2
                retry_n += 1
                print("10s后继续...")
                # time.sleep(5)  # debug only
                time.sleep(10)
            else:
                err_status = 0
                start = time.time()
                pic_file = open(self.dirpath_sub + str(_count) + ".jpg", "wb")
                pic_file.write(pic.content)
                pic_file.close()
                end = time.time()
                print("Image:%d Finished.  Cost: %.4f s" % (count, end - start))
                break
        if err_status != 0:
            if SaveErrUrl:
                errurl_file = open(self.dirpath_sub + "errors.txt", "a", encoding='utf-8')
                errurl_file.write(_url + "\n")
                errurl_file.close()
            return 1
        return 0


if __name__ == '__main__':
    spider = Spider()
    for i in range(25, 50):  # Change it before use
        url = "http://www.kuman5.com/1831/4108%d.html" % i
        getinfo_result = spider.get_info(url)
        if getinfo_result == 1:  # 检查返回值，如果获取图像下载地址列表环节出错,跳过此次循环
            continue
        imgurl_list = decrypt.run(getinfo_result[0])  # 解密，返回图片下载地址列表
        # 以下 逐行保存图片下载地址列表为 txt
        if SaveImgUrl:
            spider.save_imgurl(imgurl_list)
        # 以下 遍历“图片下载地址”列表，开始下载
        print("\n" + getinfo_result[1])
        count = 1
        for imgurl in imgurl_list:
            spider.download(imgurl, count)
            if count % 4 == 0:
                print("暂停一下...")
                # time.sleep(3)  # debug only
                time.sleep(10)
            count += 1
        print("Finished. Continue after 2s.")
        time.sleep(2)

    input("\nAll finished.\nPress ENTER to Exit.")