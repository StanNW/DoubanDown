#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 15 05:40:10 2021

@author: LiKai
"""

import requests
import re
from bs4 import BeautifulSoup
import time
import markdownify
import pandas as pd
import os
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import string
import jieba.analyse


"""
第一部分为DoubanDown主体
"""

# 请求头信息
my_headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:9527.0) Gecko/20100101 Firefox/9527.0"}


def get_id():
    while True:
        doubanid = input('\n--------------------\
                         \n\n请输入你(或其他日记备份对象)的豆瓣id：')
        iscorr = input(f'日记备份对象的豆瓣id为"{doubanid}" (yes(默认)/no): ')
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
                                \n\n请输入你的豆瓣cookie(最后不要带空格)\
                                \n获取豆瓣cookie的方法请参考 https://rb.gy/fbpp4\
                                \n:')
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
        nickname: 豆瓣网名 (str)
        headers: 请求头信息 (str)
        cookies: 豆瓣cookies (dict)
        mydoubannote_url: “我的日记”的链接 (str)
        mydouban_url: 个人豆瓣主页的链接 (str)
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
    def __init__(self,doubanid,headers):
        self.id = doubanid
        self.nickname = doubanid
        self.headers = headers
        self.cookies = {}
        self.mydoubannote_url = 'https://www.douban.com/people/' + self.id + '/notes'
        self.mydouban_url = 'https://www.douban.com/people/' + self.id
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
        
    def add_cookies(self,cookies):
        """
        添加cookies
    
        """
        self.cookies = cookies
        self.s.cookies.update(self.cookies)
    
    def get_nickname(self):
        res = self.s.get(self.mydouban_url)
        soup = BeautifulSoup(res.text, 'html.parser')
        head_tag = soup.find('head')
        title_tag = head_tag.find('title')
        self.nickname = title_tag.text.strip()
        
    def get_note_lists(self):
        print(f"\n开始访问{self.nickname}的日记页面。并获取所有日记相关信息与url\n...")
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
                    print(f'- 已经访问{mydoubannote_pagenum}页{self.nickname}的日记页面...\
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
        path = os.getcwd()
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
        path = os.getcwd()
        if self.noteyear == 'all':
            filename = self.id + '的豆瓣日记信息汇总_All.csv'
        else:
            filename = self.id + '的豆瓣日记信息汇总_' + self.noteyear + '年.csv'
        pd.DataFrame({'Pub-date':self.backupnote_date_list,'Title':self.backupnote_title_list,\
                      'Note_content_md':self.backupnote_text_list, 'Note_full_html':self.note_res_text_list,\
                          'Note_url':self.backupnote_url_list}).to_csv(os.path.join(path,dirname,filename))
        nickname_name = os.path.join(path,dirname,'nickname.txt')
        with open(nickname_name, 'w') as file:
            file.write(self.nickname)
        print("\n已备份日记的相关信息已成功保存为CSV文件。")
        
        
def doubandown_backup():
    print('\n--------------------------------------------------------------------------------')
    print('\nDoubanDown备份程序能将自己的豆瓣日记备份为md或txt文件。')
    print('\n- md文件保持了日记原有格式，配合合适的md软件可以快速便捷地搜素浏览。')
    print('- Doubandown支持备份特定年份的日记。')
    print('- 备份日记的相关信息还会以CSV格式保存下来。便于你进一步使用，分析或处理。')  
    print('\n--------------------------------------------------------------------------------')
    print('\n请按照提示输入相应的信息！')
    exemption = input('备份过程有一定风险(如IP被douban在一定时间段内拦截)，请确定你要开始备份(yes/no)：')
    if exemption.lower() == 'yes':
        doubanid =  get_id()   
        cookies = getcookies()   
        noteyear = set_noteyear()
        filetype = set_filetype()
        print('\n--------------------\
              \n\n请设置访问参数。减小批次数量、增加间隔时间，可以减少被douban拦截IP的可能性。\
              \n请放心，跳过输入将采用默认安全设置。')
        time_interval = set_time_interval()
        batch_size = set_batch_size()       
        headers = my_headers 
        
        print('\n--------------------\n\n启动DoubanDown备份进程！') 
        try:
            dbdown = DoubanNote(doubanid, headers)
        except Exception as e:
            print('\n启动DoubanDown备份进程出错。\n',e) 
        try:
            dbdown.request_init()
            dbdown.add_cookies(cookies)
            dbdown.get_nickname()
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
        print('\nDoubanDown备份程序结束，相关文件保存在该程序所在文件夹的子文件夹中。\n\
              \n------Process completed------')
    else:
        print('\n------ 战战兢兢 如临深渊 如履薄冰 ------')

            
    


"""
第二部分 追加分析功能
"""
def str_count(s):
    '''统计字符串中的中文，英文，数字个数'''
    count_en=count_zh=count_dg=0
    for c in s:
        if c in string.ascii_letters:
            count_en += 1
        elif c.isalpha():
            count_zh += 1
        elif s.isdigit():
            count_dg += 1
    return count_zh,count_en,count_dg

def choose_csv_dirs():
    print('\n--------------------\
          \n\n有以下用户的豆瓣日记信息汇总：')
    for f in os.listdir(os. getcwd()):
        if os.path.isdir(os.path.join(os. getcwd(), f)) and '信息汇总' in f and '分析' not in f:
            print('- ['+ f + ']')
    while True:
        doubanid = input('请输入想要分析的豆瓣id：')
        dirname = doubanid + '豆瓣日记信息汇总'
        if dirname in os.listdir(os. getcwd()):
            break
        else:
            print(f'不存在{doubanid}的豆瓣日记信息汇总，请重新输入！')
    dirpath = os.path.join(os. getcwd(), dirname)
    return doubanid, dirpath


def get_nickname(doubanid, dirpath):
    '''确定用户的豆瓣网名，如果没有则确定ID'''
    nickname_path = dirpath + '/nickname.txt'
    with open(nickname_path, "r") as file:
        nickname = file.read()
        print(f'{doubanid}的豆瓣网名为{nickname}.')
    return nickname
    
    
def choose_csv_files(nickname, csv_dirpath):
    print(f'\n--------------------\
          \n\n{nickname}有以下年份的豆瓣日记信息汇总：')
    for f in os.listdir(csv_dirpath):
        if '.csv' in f:
            print(f)
    while True:
        year_num = input('请输入想要分析的年份：\
                         \n分析全部日记请输入‘all’(默认选项)\
                         \n分析指定年份日记输入四位整数，如‘2021’\n')
        if year_num.isdigit() and int(year_num) >= 1000 and int(year_num) <= 9999:
            year_num0 = year_num
        else:
            year_num0 = 'all'
        for csv_name in os.listdir(csv_dirpath):
            if year_num0 in csv_name[-9:]:
                print('\n--------------------\
                      \n\n将分析['+ csv_name + ']')
                csv_full_name = os.path.join(csv_dirpath, csv_name)
                return csv_full_name, csv_name    
        else:
            print('\n不存在相应信息汇总文件，请重新输入！')

def make_analysis_dir(csv_name):   
    dirname = csv_name[:-4]+'分析_'+time.strftime("%Y-%m-%d")
    os.makedirs(dirname,exist_ok=True)
    result_dirpath = os.path.join(os.getcwd(),dirname)
    return result_dirpath
    
    
def make_monthly_heatmap(csv_full_name, csv_name, nickname, result_dirpath):
    df = pd.read_csv(csv_full_name)
    datelist = df['Pub-date'].to_list()
    yearlist = [int(date[0:4]) for date in datelist]
    year_num = max(yearlist) - min(yearlist)+1
    monthly_note_n = np.zeros((12,year_num))
    monthly_words_n = np.zeros((12,year_num))    
    mdcontentlist = df['Note_content_md'].to_list()
    
    for i, date in enumerate(datelist):
        year = int(date[0:4])
        month = int(date[5:7])
        monthly_note_n[month-1, year-min(yearlist)] += 1
        words = int(str_count(mdcontentlist[i])[0])
        monthly_words_n[month-1, year-min(yearlist)] += words
       
    month_name =['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    if year_num >= 5:
        x_label_rotation = 60
    else:
        x_label_rotation = 0
    hfont = {'fontname':'SongTi SC'}
    
    ##每月码字数热图
    sns.set()
    cmap = sns.light_palette("seagreen", as_cmap=True)
    f, ax = plt.subplots()
    sns.heatmap(monthly_words_n,cmap=cmap,ax=ax,annot=True,annot_kws={"size": 5,'fontname':'Helvetica'},fmt=".0f",\
                vmin=0, vmax=2*int(np.mean(monthly_words_n)))#annot=True
    plt.yticks(np.arange(1,13)-0.5, month_name[0:12],rotation=0,fontsize=8,horizontalalignment='left')
    plt.xticks(np.arange(1, year_num+1)-0.5, np.arange(min(yearlist), max(yearlist)+1),rotation=x_label_rotation,fontsize=8)
    ax.tick_params(axis='y', pad=15)
    ax.set_title(nickname+'的每月码字数',fontsize=8,**hfont)
    cbar = ax.collections[0].colorbar
    cbar.ax.tick_params(width=0.4,length=3,labelsize=5,color='lightgray')
    filename1 = csv_name[:-4] + '_每月码字数.png'
    # plt.savefig('doubanDairyMonthlyNum2.eps',dpi=600,format='eps')
    file_path1 = os.path.join(result_dirpath,filename1)
    plt.savefig(file_path1,dpi=600,format='png')
    ##每月日记数热图 
    sns.set()
    f, ax = plt.subplots()
    sns.heatmap(monthly_note_n,cmap=cmap,ax=ax,annot=True,annot_kws={"size": 5,'fontname':'Helvetica'})#annot=True
    plt.yticks(np.arange(1,13)-0.5, month_name[0:12],rotation=0,fontsize=8,horizontalalignment='left')
    plt.xticks(np.arange(1, year_num+1)-0.5, np.arange(min(yearlist), max(yearlist)+1),rotation=x_label_rotation,fontsize=8)
    ax.tick_params(axis='y', pad=15)
    ax.set_title(nickname+'的每月日记数',fontsize=8,**hfont)
    cbar = ax.collections[0].colorbar
    # Set the colorbar tick labels to integers
    tick_labels = cbar.get_ticks()
    cbar.set_ticks(tick_labels.astype(int))
    cbar.ax.tick_params(width=0.4,length=3,labelsize=5,color='lightgray')
    filename2 = csv_name[:-4] + '_每月日记数.png'
    # plt.savefig('doubanDairyMonthlyNum2.eps',dpi=600,format='eps')
    file_path2 = os.path.join(result_dirpath,filename2)
    plt.savefig(file_path2,dpi=600,format='png')

def make_daily_heatmap(csv_full_name, csv_name, nickname, result_dirpath):
    df = pd.read_csv(csv_full_name)
    datelist = df['Pub-date'].to_list()
    yearlist = [int(date[0:4]) for date in datelist]
    year_num = max(yearlist)-min(yearlist)+1  
    mdcontentlist = df['Note_content_md'].to_list()
    lines = len(df)
    firstmonth = datelist[-1][5:7]
    lastmonth = datelist[0][5:7]
    month_name =['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    ## Build y-Axes
    if year_num == 1:
        month_axes = month_name
        year_axes = [str(min(yearlist))]*12 
    else:
        month_axes = month_name[int(firstmonth)-1:] + month_name*(year_num-2) + month_name[:int(lastmonth)]
        year_axes = [str(min(yearlist))]*(12-int(firstmonth)+1)    
        for y in range(min(yearlist)+1,max(yearlist)):
            year_axes = year_axes + [str(y)]*12
        year_axes = year_axes +[str(max(yearlist))]*(int(lastmonth))   
    y_axes = [i +' '+ j for i, j in zip(year_axes, month_axes )]
    month_num = len(month_axes)
    y_list = np.arange(1,month_num+1)
    x_list = np.arange(1,32)   
    daily_note_n = np.zeros((month_num,31))
    daily_Words_n = np.zeros((month_num,31))    
    
    for i in range(0,lines):
        year = int(datelist[i][0:4])
        month = int(datelist[i][5:7])
        day = int(datelist[i][8:10])
        if year_num == 1:
            month_y = month
        else:
            month_y = (year-min(yearlist))*12 + month - int(firstmonth)
        daily_note_n[month_y-1,day-1] =  daily_note_n[month_y-1,day-1] + 1
        words_n = str_count(mdcontentlist[i])[0]
        daily_Words_n[month_y-1,day-1] = daily_Words_n[month_y-1,day-1] + words_n
   
    total_words_n = int(daily_Words_n.sum())
    print(f'\n{nickname}一共码字数为：{total_words_n }')
    #Make plots
    hfont = {'fontname':'SongTi SC'}
    '''每日是否写日志HeatMap 有label版本'''
    sns.set()
    f, ax = plt.subplots(figsize=(31/10,(month_num+3)/10))
    cmap = sns.light_palette("seagreen", as_cmap=True)
    sns.heatmap(daily_note_n,cmap=cmap,vmin=0, vmax=1,square=True,cbar=False,ax=ax,linewidths=0.1)#annot=True
    plt.yticks(y_list-0.5,y_axes,rotation=0,fontsize=3,horizontalalignment='left')
    plt.xticks(x_list-0.5,x_list,rotation=0,fontsize=3) 
    ax.tick_params(axis='x',direction='out', pad=-3)
    ax.tick_params(axis='y',direction='out', pad=+10)
    ax.set_title(nickname+'每日日记与否', fontsize=4, **hfont)
    filename1 = csv_name[:-4] + '_每日日记与否.png'
    file_path1 = os.path.join(result_dirpath,filename1)
    plt.savefig(file_path1,dpi=1200,format='png')
     
    '''每日写字数量HeatMap'''
    sns.set()
    grid_kws = {"height_ratios": ((month_num+3)/10, 1/10), "hspace": 0.2}
    f, (ax, cbar_ax) = plt.subplots(2,gridspec_kw=grid_kws, figsize=(31/10,(month_num+3)/10))
    #annot = (daily_Words_n != 0) & (year_num == 1)
    sns.heatmap(daily_Words_n ,cmap="mako_r",ax=ax,square=True,vmin=0,\
                vmax=5000,linewidths=0.1,cbar_ax=cbar_ax,cbar_kws={"orientation": "horizontal"})#annot=True
    for i in range(daily_Words_n.shape[0]):
        for j in range(daily_Words_n.shape[1]):
            value = daily_Words_n[i, j]
            if value != 0 and year_num == 1:
                ax.text(j + 0.5, i + 0.5, f"{value:.0f}", fontsize=2, fontname='Helvetica', ha='center', va='center',color='w')
    
    plt.sca(ax)
    plt.yticks(y_list-0.5,y_axes,rotation=0,fontsize=3,horizontalalignment='left')
    plt.xticks(x_list-0.5,x_list,rotation=0,fontsize=3) 
    ax.tick_params(axis='x',direction='out', pad=-3)
    ax.tick_params(axis='y',direction='out', pad=+10)
    ax.set_title(nickname+'的每日码字数', fontsize=4, **hfont)
    # cbar = ax.collections[0].colorbar
    # cbar.ax.tick_params(width=0.4,length=3,labelsize=5,color='darkgray')
    cbar = ax.collections[0].colorbar
    tick_labels = cbar.get_ticks()
    cbar.set_ticks(tick_labels.astype(int))
    cbar.ax.tick_params(width=0.2,length=2,labelsize=3,color='lightgray')
    filename2 = csv_name[:-4] + '_每日码字数.png'
    file_path2 = os.path.join(result_dirpath,filename2)
    plt.savefig(file_path2,dpi=1200,format='png')
   
def get_keywords(csv_full_name, csv_name, nickname, result_dirpath):
    df = pd.read_csv(csv_full_name)
    datelist = df['Pub-date'].to_list()
    yearlist = [int(date[0:4]) for date in datelist]
    year_num = max(yearlist) - min(yearlist)+1
    mdcontentlist = df['Note_content_md'].to_list()
    yearly_note_n = [0]*year_num
    yearly_word_n = [0]*year_num
    yearly_content = [""]*year_num
  
    for i, date in enumerate(datelist):
        year = int(date[0:4])
        yearly_note_n[year-min(yearlist)] += 1
        words = int(str_count(mdcontentlist[i])[0])
        yearly_word_n[year-min(yearlist)] += words
        yearly_content[year-min(yearlist)] += mdcontentlist[i]
        
    filename = csv_name[:-4] + '_年度分析.txt'
    file_path = os.path.join(result_dirpath,filename)
    jieba.setLogLevel(20)
    with open(file_path, 'w', encoding='utf-8') as f:
        for year in range(min(yearlist), max(yearlist)+1):
            note_n = yearly_note_n[year-min(yearlist)]
            word_n = yearly_word_n[year-min(yearlist)] 
            print(f'\n{year}年，{nickname}共写日志{note_n}篇，码字{word_n}字')
            print(f'{year}年，{nickname}共写日志{note_n}篇，码字{word_n}字', file=f)
            
            text = yearly_content[year-min(yearlist)]
            jieba.analyse.set_stop_words(os. getcwd()+'/banWord.txt')  
            keywords_textrank_list = jieba.analyse.textrank(text)
            keywords_textrank = '，'.join(keywords_textrank_list)
            print(f'{year}年，{nickname}的Textrank关键词是：\n{keywords_textrank}')
            print(f'{year}年，{nickname}的Textrank关键词是：\n{keywords_textrank}\n', file=f)
            
def doubandown_analysis():
    print('\n--------------------------------------------------------------------------------')
    print('\nDoubanDown分析程序将分析已备份的豆瓣日记信息汇总。')
    print('\n- 生成不同时间精度下的日记数和码字数热图。')
    print('- 基于Textrank生成年度关键词。')
    print('\n--------------------------------------------------------------------------------')
    print('\n请按照提示输入相应的信息！')
    exemption = input('请确定你要开始分析(yes/no)：')
    if exemption.lower() == 'yes':
        try:
            doubanid, dirpath = choose_csv_dirs()
        except Exception as e:
            print('\n用户选择出错。\n',e)
        nickname = doubanid
        try:
            nickname = get_nickname(doubanid, dirpath)
        except Exception as e:
            print('\n获取用户豆瓣名出错。\n',e)
        try:
            csv_full_name, csv_name = choose_csv_files(nickname, dirpath)
        except Exception as e:
            print('\n获取豆瓣日记信息汇总出错。\n',e)
        try:
            result_dirpath = make_analysis_dir(csv_name)
        except Exception as e:
            print('\n新建分析结果文件夹出错。\n',e)
        try:
            make_monthly_heatmap(csv_full_name, csv_name, nickname, result_dirpath)
        except Exception as e:
            print('\n生成每月日记数和码字数热图出错。\n',e)
        try:
            make_daily_heatmap(csv_full_name, csv_name, nickname, result_dirpath)
        except Exception as e:
            print('\n生成每日日记与否和码字数热图出错。\n',e) 
        try:
            get_keywords(csv_full_name, csv_name, nickname, result_dirpath)
        except Exception as e:
            print('\n生成年度分析和关键词出错。\n',e) 
        print(f'\nDoubanDown分析程序结束，分析结果图片和文本保存在以下地址：\n{result_dirpath}\n\
              \n------Process completed------')
    else:
        print('\n------ 战战兢兢 如临深渊 如履薄冰 ------')
        
        
def doubandown_end():
    print('\n\n------------------------------------------------------------\
          \n               DoubanDown, 把线上日记变为线下日记') 
    print('------------------------------------------------------------')
    print('问题反馈：https://www.douban.com/people/thisisstan/')  
    print('推荐使用免费软件Obsidian浏览md文件。')
    input('请按任意键退出...')
        
def doubandown():
    print('--------------------------------------------------------------------------------')
    print('\nHello，DoubanDown是一个备份并分析豆瓣日记的小程序。')
    while True: 
        print('\n--------------------------------------------------------------------------------')
        function = input('请选择备份豆瓣日志(B)（默认选项），分析豆瓣日志(A)，或者退出DoubanDown(E)\
                         \n初次使用请先进行备份(B)：\n')
        if function.lower() != 'a' and function.lower() != 'e':
            try:
                doubandown_backup()
            except Exception as e:
                print('\n豆瓣日记备份出错。\n',e)
        elif function.lower() == 'a':
            try:
                doubandown_analysis()
            except Exception as e:
                print('\n豆瓣日记分析出错。\n',e)
        elif function.lower() == 'e':
            break
        if_switch = input('请选择是否继续使用DoubanDown(yes/no)：')
        if if_switch.lower() != 'yes':
            break
    doubandown_end()

if __name__ == "__main__":
    doubandown()
    
