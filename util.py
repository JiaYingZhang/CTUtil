# -*- coding: utf-8 -*-

import hashlib
import json
from datetime import datetime
import time
import uuid
import os
import random
from typing import Dict

from urllib.parse import quote
from functools import wraps
import requests
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.profile import region_provider
from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
from django.core.mail import send_mail
from collections import namedtuple
import base64
from Crypto.Cipher import AES
import logging
import re


logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger_formatter = logging.Formatter(
    "%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")


def image_path(files_dir='image', file_type='jpeg'):
    dir_path = os.path.join('static', files_dir,
                            time.strftime('%Y%m%d',
                                          time.localtime(time.time())))
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    filename = '{file_name}.{file_type}'.format(
        file_name=str(uuid.uuid4()).replace('-', ''),
        file_type=file_type, )
    path = os.path.join(dir_path, filename)
    return path


def process_base64_in_content(post: dict):
    content: str = post.setdefault('content', '')
    if not content:
        return
    search_base64 = re.search('\"data\:image\/(.*?)\;base64\,(.*?)\"', content)
    if not search_base64:
        return
    image_type = search_base64.group(1)
    image_base64_string = search_base64.group(2)
    image_decode = base64.b64decode(image_base64_string)
    file_path = image_path(file_type=image_type)
    with open(file_path, 'wb') as f:
        f.write(image_decode)
    content = content.replace(search_base64.group(), '\"{path}\"'.format(path=file_path))
    post['content'] = content


def process_image_return_path(request, files_name='file', files_dir='image'):
    dir_path = os.path.join("static", files_dir)

    myFile = request.FILES.get(files_name)
    if myFile:
        mtime = time.strftime('%Y%m%d', time.localtime(time.time()))
        dir_path = os.path.join(dir_path, mtime)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        laname = (myFile.name).split(".")
        myfilename = str(uuid.uuid4()).replace("-", "") + "." + laname[-1]
        fileurl = os.path.join(dir_path, myfilename)

        with open(fileurl, 'wb+') as f:
            for chunk in myFile.chunks():
                f.write(chunk)
        return fileurl.replace('\\', '/')
    return None


def process_images_return_pathlist(request, files_dir='image'):
    dir_path = os.path.join("static", files_dir)
    myFiles = request.FILES
    data_list = []
    if myFiles:
        mtime = time.strftime('%Y%m%d', time.localtime(time.time()))
        dir_path = os.path.join(dir_path, mtime)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        for myFile in myFiles.itervalues():
            laname = (myFile.name).split(".")
            myfilename = str(uuid.uuid4()).replace("-", "") + "." + laname[-1]
            fileurl = os.path.join(dir_path, myfilename)
            with open(fileurl, 'wb+') as f:
                for chunk in myFile.chunks():
                    f.write(chunk)
            data_list.append(fileurl.replace('\\', '/'))
    return data_list


class SMS(object):

    REGION = "cn-hangzhou"
    PRODUCT_NAME = "Dysmsapi"
    DOMAIN = "dysmsapi.aliyuncs.com"

    def __init__(self, ACCESS_KEY_ID, ACCESS_KEY_SECRET, sign_name,
                 template_code):
        # 创建客户端
        self.acs_client = AcsClient(ACCESS_KEY_ID, ACCESS_KEY_SECRET,
                                    self.REGION)
        region_provider.add_endpoint(self.PRODUCT_NAME, self.REGION,
                                     self.DOMAIN)
        self.business_id = uuid.uuid1()

        # 短信签名
        self.sign_name = sign_name
        # 短信模板
        self.template_code = template_code
        self.template_param = '"code": "{code}"'

    # 发送信息
    def set_send_sms(self, phone, code):
        smsRequest = SendSmsRequest.SendSmsRequest()
        smsRequest.set_TemplateCode(self.template_code)
        smsRequest.set_TemplateParam('{' + self.template_param.format(
            code=code) + '}')
        smsRequest.set_SignName(self.sign_name)
        smsRequest.set_PhoneNumbers(phone)

        smsResponse = self.acs_client.do_action_with_exception(smsRequest)
        return smsResponse

    def __unicode__(self):
        return self.PRODUCT_NAME


class Email(object):

    SENED_EMAIL = 'kaka@cingta.com'
    SUBJECT_STRING = '注册青塔'

    def __init__(self, session, email):
        self.session = session
        self.email = email

    def make_email_text(self):
        text = """{session}""".format(session=self.session)
        return text

    @property
    def email_msg(self):
        data = {
            'subject': self.SUBJECT_STRING,
            'message': self.make_email_text(),
            'from_email': self.SENED_EMAIL,
            'recipient_list': [self.email],
        }
        return data

    def __unicode__(self):
        return 'send email {} to {}'.format(
            self.SUBJECT_STRING,
            self.email, )


_state = namedtuple('FUNCSTATE', ['SUCCESS', 'FAIL'])
_STATE = _state(0, -1)


class VerificationControl(object):
    def __init__(self, model):
        self.smsmodel = model

    def send_sms(self, VerificationControl, client):
        code = random.randint(1000, 9999)
        s = self.smsmodel.objects.filter(
            VerificationControl=VerificationControl).first()
        if s:
            now_time = datetime.now()
            if (now_time - s.modifytime).seconds < 60:
                return '一分钟只能发送一条信息'
            s.code = str(code)
        else:
            s = self.smsmodel(
                VerificationControl=VerificationControl, code=str(code))
        sms_resp = client.set_send_sms(
            VerificationControl=VerificationControl, code=code)
        sms_resp = json.loads(sms_resp)
        s.bizId = sms_resp.get('BizId', '')

        if sms_resp.get('Code') != 'OK':
            s.error_msg = sms_resp.get('Code')
            s.save()
            return self._process_error_returncode(sms_resp.get('Code'))
        s.save()
        return 'OK'

    def send_cingta_email(self, session, email):
        mail = Email(session, email)
        try:
            send_mail(**mail.email_msg)
            return _STATE.SUCCESS
        except:
            return _STATE.FAIL

    def vadite_code(self, phone, code):
        return self.smsmodel.objects.filter(
            phone=phone, code=str(code)).exists()

    def _process_error_returncode(self, code):
        _return_error_dirct = {
            'isv.MOBILE_NUMBER_ILLEGAL': '请输入正确的手机号',
            'isv.BUSINESS_LIMIT_CONTROL': '你的手机号已被限流,请联系管理员',
            'default': '短信发送错误',
        }
        return _return_error_dirct.get(code, _return_error_dirct['default'])


class WxLogin(object):
    def __init__(self, APPID, APPSECRET):
        self.appid = APPID
        self.secret = APPSECRET
        self.redirect_url = quote('https://www.cingta.com/')

    # 生成二维码url
    def create_code_url(self):
        return 'https://open.weixin.qq.com/connect/qrconnect?appid={APPID}&redirect_uri={redirrect_uri}&response_type=code&scope={scope}&state=STATE#wechat_redirect'.format(
            APPID=self.appid,
            redirrect_uri=self.redirect_url,
            scope='snsapi_login', )

    # 获取open_id
    def get_access_token(self, code):
        url = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid={APPID}&secret={APPSECRET}&code={CODE}&grant_type=authorization_code'.format(
            APPID=self.appid,
            APPSECRET=self.secret,
            CODE=code, )
        resp = requests.get(url).json()
        return resp

    # 获取unionid
    @staticmethod
    def get_unionid(token, openid):
        url = 'https://api.weixin.qq.com/sns/userinfo?access_token={token}&openid={openid}'.format(
            token=token,
            openid=openid, )
        resp = requests.get(url).json()
        return resp.get('unionid')


class CTCache(object):
    defalut_values = ('default', 'Article', 'Position')

    def __init__(self, _type, timeout, data=''):
        self.type = _type
        self.data = data
        self.timeout = timeout

    @property
    def cache_key(self):
        md = hashlib.md5()
        md.update(self.type + self.data)
        md.digest()
        key = md.hexdigest()
        return key


def set_static_cache(timeout=60):
    def _set_static_cache(view_func):
        @wraps(view_func)
        def _do_something(request):
            resp = view_func(request)
            if getattr(resp, 'success', False):
                setattr(resp, 'cache_data', True)
                setattr(resp, 'cache_timeout', timeout)
            return resp

        return _do_something

    return _set_static_cache


def test_run_time(view_func):
    @wraps(view_func)
    def _do_something(request):
        start_time = datetime.now()
        n = view_func(request)
        end_time = datetime.now()
        s = end_time - start_time
        print('TEST------------------', 'url<{}>, run time is: {}'.format(
            view_func.__name__, s), '------------TEST')
        return n
    return _do_something


class WXBizDataCrypt:
    def __init__(self, appId, sessionKey):
        self.appId = appId
        self.sessionKey = sessionKey

    def decrypt(self, encryptedData, iv):
        sessionKey = base64.b64decode(self.sessionKey)
        encryptedData = base64.b64decode(encryptedData)
        iv = base64.b64decode(iv)

        cipher = AES.new(sessionKey, AES.MODE_CBC, iv)
        data = self._unpad(cipher.decrypt(encryptedData))
        decrypted = json.loads(data)

        if decrypted['watermark']['appid'] != self.appId:
            raise Exception('Invalid Buffer')

        return decrypted

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]


class WxMiniInterface(object):
    def __init__(self, APPID: str, APPSECRET: str):
        self.APPID = APPID
        self.APPSECRET = APPSECRET

    def get_user_session(self, code: str) -> Dict[str, str]:
        url = 'https://api.weixin.qq.com/sns/jscode2session?appid={AppID}&secret={AppSecret}&js_code={code}&grant_type=authorization_code'.format(
            AppID=self.APPID,
            AppSecret=self.APPSECRET,
            code=code, )
        resp = requests.get(url).json()
        return resp

    def get_user_info(self, session: str, encryptedata: str, iv: str) -> str:
        wx_mini = WXBizDataCrypt(self.APPID, session)
        userinfo = wx_mini.decrypt(encryptedata, iv)
        return userinfo

    def send_template_msg(self, **templatedata) -> Dict[str, str]:
        get_user_info = set(
            ['touser', 'template_id', 'page', 'form_id', 'data'])
        if not (get_user_info & set(templatedata.keys()) == get_user_info):
            raise TypeError(
                'send_template_msg missing required positional arguments: touser, template_id, page, form_id or data'
            )

        token_url: str = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={APPID}&secret={APPSECRET}'.format(
            APPID=self.APPID,
            APPSECRET=self.APPSECRET, )
        token: Dict[str, str] = requests.get(token_url).json()
        if token.get('errcode'):
            raise TypeError('error APPID or error APPSECRET')
        _token = token.get('access_token', '')
        template_url: str = 'https://api.weixin.qq.com/cgi-bin/message/wxopen/template/send?access_token={ACCESS_TOKEN}'.format(
            ACCESS_TOKEN=_token, )
        resp = requests.post(
            template_url, data=json.dumps(templatedata)).json()
        return resp
