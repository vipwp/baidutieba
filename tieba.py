#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 2013-04-04
@author: 594peng@gmail.com
'''
import getpass
import random,re,time

import urllib,urllib2,Cookie,cookielib
try:
    import json
except:
    import simplejson as json

class BaiduTieBa():
    class LoginError(Exception):
        def __init__(self,*argv):
            if argv:
                Exception.__init__(self,*argv)
            else:
                Exception.__init__(self,'Login must be Done first~') 

    USERINFO_URL='http://tieba.baidu.com/f/user/json_userinfo'
    COOKIE_FILE='baidutieba.cookie'   
    TBS_URL = "http://tieba.baidu.com/dc/common/tbs"
    BASE_URL='http://tieba.baidu.com'
    MYTIEBA_URL='http://tieba.baidu.com/i/%s/forum'
    callback='bd__cbs__1fr7of'
    PASSPORT_URL='https://passport.baidu.com/v2/api/'
    loginURL1='?getapi&tpl=tb&apiver=v3&tt=%d&class=login&'
    loginURL2='?logincheck&token=%s=&tpl=tb&apiver=v3&tt=%d&username=%s&isphone=false'
    verifyURL='http://tieba.baidu.com/cgi-bin/genimg?%s&t=%s'
    signURL='http://tieba.baidu.com/sign/add'


    pageDataReg='var PageData.?=(.*?);'
    old_tidsReg='<a class="(.+)" forum-id="(.*?)" forum="(.*?)" forum-type="(.+)" forum-like="(.*?)" href="(.*?)" target="_blank">(.*?)</a>'
    tidsReg ='<a href="(.*?)" title="(.+)">'
    tbsReg='PageData.tbs.+=.+"(.*?)"'
    isSignReg='PageData.is_sign_in.?=.?(\d);'

    LOGIN_ERR_MSGS = {
        "1": "用户名格式错误，请重新输入",
        "2": "用户不存在",
        "3": "",
        "4": "登录密码错误，请重新输入",
        "5": "今日登录次数过多",
        "6": "验证码不匹配，请重新输入验证码",
        "7": "登录时发生未知错误，请重新输入",
        "8": "登录时发生未知错误，请重新输入",
        "16": "对不起，您现在无法登录",
        "51": '该手机号未通过验证',
        "52": '该手机已经绑定多个用户',
        "53": '手机号码格式不正确',
        "58": '手机号格式错误，请重新输入',
        "256": "",
        "257": "请输入验证码",
        "20": "此账号已登录人数过多",
        "default": "登录时发生未知错误，请重新输入"
    }
    POST_ERR_MSGS = {
        "38": "验证码超时，请重新输入",
        "40": "验证码输入错误，请您返回后重新输入",
        "703": "为了减少恶意灌水和广告帖，本吧被设置为仅本吧会员才能发贴",
        "704": "为了减少恶意灌水和广告帖，本吧被设置为仅本吧管理团队才能发贴，给您带来的不便深表歉意",
        "705": "本吧当前只能浏览，不能发贴！",
        "706": "抱歉，本贴暂时无法回复。",
        "900": "为抵御挖坟危害，本吧吧主已放出贴吧神兽--超级静止蛙，本贴暂时无法回复。"
    }    

    def __init__(self,uin,pwd):
        if uin:
            self.uin=uin
            self.pwd=pwd
            self.cookies=cookielib.MozillaCookieJar()
            self.openner=urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookies))
            self.openner.addheaders=[('User-agent','Mozilla/5.0 (X11; Linux i686)'),('Accept-Charset','GBK,utf-8')]
            self.verifycode=''
            self.isLogin=False
            self.pageData=None
            self.user=None
            self.tiebas=[]
            self.name_link=None
            self.session_id=None

            self.isLogging=True

        else:
            raise self.LoginError('Uin must be input~')

    def get_userinfo(self):
        if self.checkLogin():
            try:
                ret=self.openner.open(self.USERINFO_URL)
                data=ret.read()
                jdata=json.loads(data)
                self.user=jdata['data']
                self.name_link=str(self.user['user_name_link'])
                self.session_id=self.user['session_id'].encode('utf-8')
            except Exception ,e:
                return False,'Get useinfo error:'+str(e)
        else:
            raise self.LoginError  

    def mylog(self,msg):
        if self.isLogging:
            print msg

    def getTimeStamp(self):
        return int(time.time()*1000)

    def get_ppui_logintime(self):
        return ''.join([str(random.randint(0,9))  for i in range(5)])

    def get_verifyCode(self,codeString):
        if not codeString:
            return ''
        else:
            import Image,StringIO
            url=self.verifyURL%(codeString,str(random.random()))
            ret=self.openner.open(url)
            html=ret.read()
            img=Image.open(StringIO.StringIO(html))
            img.show()
            verify=raw_input('Pls input the verify:')
            return verify
        
    def get_tbs(self):
        if not self.checkLogin():
            raise self.LoginError()
        try:
            ret=self.openner.open(self.TBS_URL)
            data=ret.read()
            jdata=json.loads(data)
            tbs=jdata['tbs'].encode('utf-8')
            return tbs
        except Exception,e:
            self.mylog("Can't get tbs:"+str(e))
            return None
        
    def login(self):
        try:
            self.cookies.load(self.COOKIE_FILE)
            if self.checkLogin():
                self.get_userinfo()
                self.mylog('载入cookie登录成功～')
                return True,'载入cookie登录成功～'

        except Exception,e:
            self.mylog('本地cookie登录失败,尝试post登录')
        try:
            ret=self.openner.open(self.BASE_URL)
            url1=self.PASSPORT_URL+self.loginURL1 %(self.getTimeStamp())
            ret=self.openner.open(url1)
            html=ret.read()
            data=json.loads(html)
            self.token=data['data']['token'].encode('utf-8')

            url2=self.PASSPORT_URL+self.loginURL2%(self.token,self.getTimeStamp(),self.uin)
            ret=self.openner.open(url2)
            html=ret.read()
            data=json.loads(html)
            verifycode = data['data']['codeString'].encode('utf-8')
            if verifycode:
                self.verifycode=self.get_verifyCode(verifycode)
            else:
                pass
            if not self.pwd:
                self.pwd=getpass.getpass('Pls input the pwd of %s:'%self.uin)
            url3=self.PASSPORT_URL+'?login'
            data={
                #'staticpage':'http://tieba.baidu.com/tb/static-common/html/pass/v3Jump.html',
                'charset':'utf-8',
                'token':self.token,
                'tpl':'tb',
                'apiver':'v3',                
                'tt':str(self.getTimeStamp()),
                'u':self.BASE_URL+'/index.html',
                'codestring':verifycode,
                'isPhone':'false',
                'safeflg':'0',
                'username':self.uin,
                'password':self.pwd,
                'mem_pass':'on',
                'ppui_logintime':self.get_ppui_logintime(),
                'verifycode':self.verifycode,
                #'callback':'parent.bd__pcbs__7cfzfq'
            }
            ret=self.openner.open(url3,urllib.urlencode(data))
            html=ret.read()
            err_code=re.search('err_no=(\d+)',html).group(1)
            if err_code!='0':
                errmsg=self.LOGIN_ERR_MSGS[err_code]
                self.mylog(errmsg)
                return False,errmsg
            self.get_userinfo()
            self.openner.open(self.BASE_URL)
            self.cookies.save(self.COOKIE_FILE)
            self.isLogin=True
            self.mylog('logged,and cookieinfo saved~')
            return True,'Login successfully!'


        except Exception ,e:
            self.mylog('登录失败：'+str(e))
            return False,str(e)

    def get_tiebas(self):
        if not self.checkLogin():
            raise self.LoginError()
        try:
            #tiebaURL=self.MYTIEBA_URL%self.name_link
            tiebaURL = self.BASE_URL+'/i/'+self.name_link
            ret=self.openner.open(tiebaURL)
            html=ret.read().decode('gbk').encode('utf-8')
            tids=re.findall(self.old_tidsReg,html)
            self.tiebas=[(i[-1],i[-2]) for i in tids]
            return True,'Get TieBa list Done~'
        except Exception ,e :
            return False,str(e)    

    def sign_single(self,url,name):
        if not url.startswith('http'):
            url=self.BASE_URL+url
        try:
            #ret=self.openner.open(url)
            #html=ret.read()
            #isSign=re.findall(self.isSignReg,html)[0]
            #if '1'==isSign:
            #    return False,name+' 今天已经签到了'
            #tbs=re.findall(self.tbsReg,html)[0]
            data={
                'ie':'utf-8',
                'kw':name,
                'tbs':self.get_tbs()
            }
            ret=self.openner.open(self.signURL,urllib.urlencode(data))
            html=ret.read()
            data=json.loads(html)
            if data['no']!=0:
                return False,name+" 签到失败:"+data['error'].encode('utf-8')
            data=data['data']['uinfo']
            return True,name+ " 签到成功!今日第%d个签到，连续%d天，共签到%d次"%\
                   (data['user_sign_rank'],data['cont_sign_num'],data['cout_total_sing_num'])
        except Exception ,e:
            return False,name+' 签到失败:'+str(e)

    def sign_all(self):
        for i in self.tiebas:
            ret,msg=self.sign_single(i[1],i[0])
            print msg
            if ret: time.sleep(3)
        print 'All done!'

    def checkLogin(self):
        if self.isLogin:
            return True
        data=self.openner.open(self.TBS_URL).read()
        jdata=json.loads(data)
        if not jdata['is_login']:
            self.isLogin =False
            print '登录cookie过期'
            return False
        return True

if __name__=='__main__':
    c=BaiduTieBa('w16212','')
    ret,msg=c.login()
    c.get_tbs()
    if not ret:
        print msg
    ret,msg=c.get_tiebas()
    c.sign_all()
