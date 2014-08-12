#!/usr/bin/python

# http://blog.carduner.net/2010/05/26/authenticating-with-facebook-on-the-command-line-using-python/

import requests
from urllib import urlencode
from urlparse import urlparse, parse_qs
import BaseHTTPServer
import webbrowser
import os

APP_ID = '4502339'
APP_SECRET = 'fIvstq8mu5BKrVJNhHV2'
ENDPOINT = 'https://oauth.vk.com'
REDIRECT_URI = 'http://127.0.0.1:8080'
ACCESS_TOKEN = None
LOCAL_FILE = '.vk_access_token'

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    def do_GET(self):
        global ACCESS_TOKEN

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        code = parse_qs(urlparse(self.path).query).get('code')
        code = code[0] if code else None
        if code is None:
            self.wfile.write("Sorry, authentication failed.")
            sys.exit(1)

        response = requests.get(ENDPOINT + "/access_token", params={'client_id':APP_ID,
                                                'redirect_uri':REDIRECT_URI,
                                                'client_secret':APP_SECRET,
                                                'code':code})
        ACCESS_TOKEN = response.json()['access_token']
        open(LOCAL_FILE,'w').write(ACCESS_TOKEN)
        self.wfile.write("You have successfully logged in to VK. You can close this window now.")
   
    def log_message(self, format, *args):
        return

class VK():
    @classmethod
    def test_access_token(cls, access_token):
        r = requests.get("https://api.vk.com/method/getProfiles", params={"uid":1, "access_token":access_token})
        error = r.json().get("error")
        if error == None:
            return True
        else:
            return False

    @classmethod
    def get_access_token(cls):
        global ACCESS_TOKEN        
        if os.path.exists(LOCAL_FILE):
            ACCESS_TOKEN = open(LOCAL_FILE).read()

        if ACCESS_TOKEN and cls.test_access_token(ACCESS_TOKEN):
            return ACCESS_TOKEN

        url = ENDPOINT + "/authorize?" + urlencode({'client_id':APP_ID,
                                                    'redirect_uri':REDIRECT_URI,
                                                     'scope':'audio',
                                                     'display':'page',
                                                     'v':'5.24',
                                                     'response_type':'code'})
        webbrowser.open(url)
        httpd = BaseHTTPServer.HTTPServer(('127.0.0.1', 8080), RequestHandler)

        ACCESS_TOKEN = None
        while ACCESS_TOKEN is None: 
            httpd.handle_request()

        return ACCESS_TOKEN
