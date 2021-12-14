#!/usr/bin/env python
# -*- coding: utf-8 -*-


import requests
import re
from bs4 import BeautifulSoup
import time
import markdownify
import pandas as pd
import os


# 请求头信息
my_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:9527.0) Gecko/20100101 Firefox/9527.0"}


def get_id():
    while True:
        doubanid = input('\n--------------------\
                         \n\n请输入你的豆瓣id：')
        iscorr = input(f'您的豆瓣id为"{doubanid}" (yes(默认)/no): ')
        if (not iscorr) or iscorr.lower() != 'no':
            print('豆瓣id已确认。')
            break
    return doubanid 

def getcookies():
    """
    Input:
        raw_cookies(str): 豆瓣cookie
    
    Return:
       cookies(dict):豆瓣cookie
    """
    while True:
        try:
            raw_cookies = input('\n--------------------\
                                \n\n请输入你的cookie(最后不要带空格)：')
            cookies = {}
            for line in raw_cookies.split(';'):
                key,value = line.split('=',1)
                cookies[key] = value
            break
        except Exception as e:
            print('\ncookie输入错误：\n',e)            
    return cookies 

def set_time_interval():
    """
    Input: 1-10 Integer
    Return: Request Time Interval(int)
    """
    time_interval = input('请输入批次访问日记的时间间隔(范围为1-10以分为单位的整数，默认为1)：')
    if time_interval.isdigit() and int(time_interval) >= 1 and int(time_interval) <= 10:
        time_interval0 = int(time_interval)
    else:
        time_interval0 = 1
    return time_interval0

def set_batch_size():
    """
    Input: Batch size(Notes number) between each pause(request time interval)
    Return: batch size(int)
    """
    batch_size = input('请输入每一批访问日记的篇数数量(10-100的整数，默认为50)：')
    if batch_size and batch_size.isdigit() and \
        int(batch_size) >= 10 and int(batch_size) <= 100:
        batch_size0 = int(batch_size)
    else:
        batch_size0 = 50
    return batch_size0

def set_noteyear():
    """
    Input: 'all' or 4 digit int
    Return: Year
    """
    noteyear = input('\n--------------------\n\n请选择备份日记的年份：\
                     \n备份全部日记请输入‘all’(默认选项) \
                     \n备份指定年份日记输入四位整数，如‘2021’\n')
    if noteyear and noteyear.isdigit() and int(noteyear) >= 1999 \
        and int(noteyear) <= 3000:
        noteyear0 = noteyear
    else:
        noteyear0 = 'all'
    return noteyear0

def set_filetype():
    """
    Set the filetype
    """
    filetype = input('\n--------------------\n\n请选择备份日记的格式：\
                     \nA.md文件(默认选项)\nB.txt文件 \n')
    if filetype.lower() and filetype.lower() == 'b':
        filetype0 = 'txt'
    else:
        filetype0 = 'md'
    return filetype0

def validate_title(title):
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "_", title)  # 替换为下划线
    return new_title
    
class DoubanNote:
    """
    DoubanNote DoubanNote是一次备份过程
    
    Attributes:
        id:豆瓣 id (str)
        headers: 请求头信息 (str)
        cookies: 豆瓣cookies (dict)
        mydoubannote_url: “我的日记”的链接 (str)
        note_url_list:所有日记的url (str list)
        note_title_list:所有日记的标题 (str list)
        note_pubdate_list:所有日记的发表日期 (str list)
        note_number: 所有日记数量 (int)
        noteyear: 将备份的日记年份 (str)
        note_range: 将要备份的日记范围 (range)
        note_res_text_list: 成功获取的日记html文档列表（str list）
        note_res_num: 成功获取的日记数量（int）
        backupnote_url_list: 备份日记的url (str list）
        backupnote_title_list: 备份日记的标题 (str list）
        backupnote_text_list: 备份日记md格式的内容 (str list)
        note_dict: 包含备份日记url，标题，md格式内容，完整页面html文档的dict  
        
    """
    def __init__(self,doubanid,headers,cookies=None):
        self.id = doubanid
        self.headers = headers
        self.cookies = cookies
        self.mydoubannote_url = 'https://www.douban.com/people/' + self.id + '/notes'
        self.note_url_list = []
        self.note_title_list = []
        self.note_pubdate_list = []
        self.note_number = 0
        self.noteyear = 'all'
        self.note_range = range(self.note_number)
        self.note_res_text_list = []
        self.note_res_num = 0
        self.backupnote_url_list = []
        self.backupnote_date_list = []
        self.backupnote_title_list = []
        self.backupnote_text_list = []
        self.note_dict = {}
        
        
    def request_init(self):
        """ 
        设置访问信息
        """
        self.s = requests.Session()
        self.s.headers.update(self.headers)
        
    def add_cookies(self):
        """
        添加cookies
    
        """
        self.s.cookies.update(self.cookies)
        
    def get_note_lists(self):
        print(f"\n开始访问{self.id}的日记页面。并获取所有日记相关信息与url\n...")
        response_mydoubannote = self.s.get(self.mydoubannote_url)
        soup = BeautifulSoup(response_mydoubannote.text, 'html.parser')
        mydoubannote_pagenum = 1
        self.note_url_list = [tag.get('href') for tag in soup.find_all(id=re.compile('naf-'))]
        self.note_title_list = [tag.get('title') for tag in soup.find_all('a', title=True)]
        self.note_pubdate_list = [tag.string for tag in soup.find_all('span', class_='pub-date')]
        get_note_start_time = time.time()
        while 1:
            time.sleep(1.5)
            try:
                next_url=soup.find(class_="next").link.get('href')
            except:
                break
            else:
                mydoubannote_pagenum += 1
                res = self.s.get(next_url)
                soup=BeautifulSoup(res.text,'html.parser')
                if mydoubannote_pagenum % 10 == 0:
                    print(f'- 已经访问{mydoubannote_pagenum}页{self.id}的日记页面...\
                          响应状态码:',res.status_code)
                for tag in soup.find_all(id=re.compile('naf-')):
                    self.note_url_list.append(tag.get('href'))
                for tag in soup.find_all('a', title=True):
                    self.note_title_list.append(tag.get('title'))
                for tag in soup.find_all('span', class_='pub-date'):
                    self.note_pubdate_list.append(tag.string)          
        self.note_number = len(self.note_url_list)
        get_note_end_time = time.time()
        time_cost = get_note_end_time - get_note_start_time
        time_cost_min = int(time_cost)//60
        time_cost_sec = int(time_cost)%60
        print(f"共{self.note_number}篇日记url成功收集完毕！\n耗时{time_cost_min}分{time_cost_sec}秒。")
     
                    
    def get_note_range(self,noteyear='all'):
        if noteyear == 'all':
            self.note_range = range(self.note_number)
            self.noteyear = noteyear
            print(f"\n将访问所有一共{self.note_number}篇日记。")
        else:
            note_index = [i for i, date in enumerate(self.note_pubdate_list) if noteyear in date]
            while not note_index:
                print(f'\n{noteyear}年无日记,请重新选择：')
                noteyear = set_noteyear()
                if noteyear == 'all':
                    self.note_range = range(self.note_number)
                    self.noteyear = noteyear
                    print(f"\n将访问所有一共{self.note_number}篇日记。")
                    return
                else:
                    note_index = [i for i, date in enumerate(self.note_pubdate_list) if noteyear in date]
            self.note_range = range(note_index[0],note_index[-1]+1)
            self.noteyear = noteyear
            get_note_num = len(self.note_range)
            print(f"\n将访问{self.noteyear}年一共{get_note_num}篇日记。")
           
            
       
    def get_note_res_text(self,time_interval0=1,batch_size0=50):
        get_note_num = len(self.note_range)
        time_pred = get_note_num // batch_size0 * time_interval0 * 60 +  get_note_num * 2
        time_pred_min = int(time_pred )//60
        time_pred_sec = int(time_pred )%60
        print(f"预计耗时{time_pred_min}分{time_pred_sec}秒。")
        get_note_res_start_time = time.time()     
        for url_i in self.note_range:       
            try:
                res = self.s.get(self.note_url_list[url_i])
                self.note_res_text_list.append(res.text)
                self.backupnote_url_list.append(self.note_url_list[url_i])
            except Exception as e:
                print(f'打开第{url_i+1-self.note_range[0]}篇日记失败。\n',e)
            if (url_i+1-self.note_range[0]) % batch_size0 == 0:
                print(f'- 已经访问{get_note_num}篇日记中的{url_i+1-self.note_range[0]}篇，休息{time_interval0}分钟...')
                time.sleep(time_interval0*60)
            time.sleep(1.5)
        get_note_res_end_time = time.time()
        time_cost = get_note_res_end_time - get_note_res_start_time
        time_cost_min = int(time_cost)//60
        time_cost_sec = int(time_cost)%60
        self.note_res_num = len(self.note_res_text_list)
        print(f"共{get_note_num}篇日志访问完毕，成功获取{self.note_res_num}篇日记html信息！\n耗时{time_cost_min}分{time_cost_sec}秒。")

    def extract_date_titile_text(self):
        for restext in self.note_res_text_list:
            htmlsp = BeautifulSoup(restext,'html.parser')
            date = htmlsp.find(class_='pub-date').text
            title = htmlsp.find('h1').text
            htmlnote = htmlsp.find(id=re.compile('full')).find(class_='note')
            htmlnotesp = BeautifulSoup(str(htmlnote),'html.parser')
            for i in range(len(htmlnotesp.find_all("div",class_="image-caption-wrapper"))):
                htmlnotesp.find_all("div",class_="image-caption-wrapper")[i].wrap(htmlnotesp.new_tag("p"))
            for i in range(len(htmlnotesp.find_all("div",class_="image-wrapper"))):
                htmlnotesp.find_all("div",class_="image-wrapper")[i].wrap(htmlnotesp.new_tag("p")) 
            for i in range(len(htmlnotesp.find_all("div",class_="image-container image-float-center"))):
                htmlnotesp.find_all("div",class_="image-container image-float-center")[i].wrap(htmlnotesp.new_tag("blockquote"))
            for i in range(len(htmlnotesp.find_all("div",class_="introduction"))):
                htmlnotesp.find_all("div",class_="introduction")[i].wrap(htmlnotesp.new_tag("blockquote"))
            mdnote = markdownify.markdownify(str(htmlnotesp))
            self.backupnote_date_list.append(date)
            self.backupnote_title_list.append(title)
            self.backupnote_text_list.append(mdnote)
        print("\nhtml文档格式已成功转换为md文件格式！")
    
    def save_md(self, filetype):
        dirname = self.id + '豆瓣日记备份_' + filetype + '文件'
        os.makedirs(dirname,exist_ok=True)
        path = os. getcwd()
        for i in range(self.note_res_num):
            try:
                full_mdnote = '\n# ' + self.backupnote_title_list[i] + '\n##### ' \
                    + self.backupnote_date_list[i] + '\n' + self.backupnote_text_list[i]
                filename = self.backupnote_date_list[i][0:10] + '_' + validate_title(self.backupnote_title_list[i])\
                    + '.' + filetype
                with open(os.path.join(path,dirname,filename.replace('/','_')),'w',encoding='utf-8_sig') as f:
                    f.write(full_mdnote)
            except Exception as e:
                print(f'保存第{i+1}篇日记失败。\n',e) 
        print(f"成功备份共{self.note_res_num}篇日志为{filetype}文件！")
    
    def make_csv(self):
        dirname = self.id + '豆瓣日记信息汇总'
        os.makedirs(dirname,exist_ok=True)
        path = os. getcwd()
        if self.noteyear == 'all':
            filename = self.id + '的所有豆瓣日记信息汇总.csv'
        else:
            filename = self.id + '的豆瓣日记信息汇总_' + self.noteyear + '年.csv'
        pd.DataFrame({'日期':self.backupnote_date_list,'标题':self.backupnote_title_list,\
                      '日记内容(md格式)':self.backupnote_text_list, '日记完整页面html':self.note_res_text_list,\
                          '日记url':self.backupnote_url_list}).to_csv(os.path.join(path,dirname,filename))
        print("\n已备份日记的相关信息已成功保存为CSV文件。")
        
        
def main():
    print('--------------------------------------------------------------------------------')
    print('\nHello，DoubanDown是一个备份豆瓣日记的小程序。')
    print('\n- Doubandown能将自己的豆瓣日记备份为md或txt文件')
    print('- md文件保持了日记原有格式，配合合适的md软件可以快速便捷地搜素浏览。')
    print('- Doubandown支持备份特定年份的日记。')
    print('- 所有备份日记的相关信息还会以CSV格式保存下来。便于你进一步使用，分析或处理。')  
    print('\n--------------------------------------------------------------------------------')
    print('\n请按照提示输入相应的信息！')
    exemption = input('备份过程有一定风险(如IP被douban在一定时间段内拦截)，请确定你要开始备份(yes/no)：')
    if exemption.lower() == 'yes':
        doubanid =  get_id()   
        private = input('\n--------------------\n\n请选择备份日记类型：\
                        \nA.只需要备份他人可见的日记\
                        \nB.需要备份包括仅自己可见的日记（需要你提供自己的cookie，默认）\n')
        if private.lower() != 'a':
              cookies = getcookies()   
        noteyear = set_noteyear()
        filetype = set_filetype()
        print('\n--------------------\
              \n\n请设置访问参数。减小批次数量、增加间隔时间，可以减少被douban拦截IP的可能性。\
              \n请放心，跳过输入将采用默认设置。')
        time_interval = set_time_interval()
        batch_size = set_batch_size()       
        headers = my_headers 
        
        print('\n--------------------\n\n启动DoubanDown备份进程！') 
        try:
            dbdown = DoubanNote(doubanid, headers,cookies)
        except Exception as e:
            print('\n启动DoubanDown备份进程出错。\n',e) 
        try:
            dbdown.request_init()
            dbdown.add_cookies()
        except Exception as e:
            print('\n访问设置出错。\n',e) 
        try:
            dbdown.get_note_lists()
        except Exception as e:
            print('\n收集日记url出错。\n',e) 
        try:
            dbdown.get_note_range(noteyear)
        except Exception as e:
            print('\n获取指定年份的日记url信息出错。\n',e) 
        try:    
            dbdown.get_note_res_text(time_interval,batch_size)
        except Exception as e:
            print('\n访问并获取日记页面html出错。\n',e) 
        try:
            dbdown.extract_date_titile_text()
        except Exception as e:
            print('\n收集日记信息或将日记内容转换为md格式出错。\n',e)  
        try:
            dbdown.save_md(filetype)
        except Exception as e:
            print(f'\n保存日记为{filetype}文件过程出错。\n',e) 
        try:
            dbdown.make_csv()
        except Exception as e:
            print('\n汇总豆瓣日记信息并保存CSV文件过程出错。\n',e)
        print('\nDoubanDown备份程序结束，相关文件包存在该程序所在文件夹的子文件夹中。\
              \n---Process completed---\n')
    else:
        print('\n--- 战战兢兢 如临深渊 如履薄冰 ---')
    print('\n\nDoubanDown, 把线上日记变为线下日记') 
    print('------------------------------------------------------------')
    print('问题反馈：https://www.douban.com/people/thisisstan/')  
    print('推荐使用免费软件Obsidian浏览md文件。')
    input('按任意键退出...')
            
    
          
    
main()