#!/usr/bin/env python

import os
import ConfigParser
import urlparse
from HTMLParser import HTMLParser
import oauth2 as oauth
import twitter

class TwParser(HTMLParser):
    pin = ''
    temp = 0
    def __init__(self, data):
        HTMLParser.__init__(self)
        self.feed(data)
    def handle_starttag(self, tag, attrs):
        if tag == 'div' and attrs[0][1] == 'oauth_pin':
            self.temp = 1
    def handle_data(self, data):
        if self.temp:
            self.pin = data
            self.temp = 0
        return self.pin

class Auth:

    def __init__(self, username, password):
        self.consumer_key       = 'Ku59hdNBCxX58MC8oQpfbA'
        self.consumer_secret    = 'OzWeLSE3iufvgxedkKEYg2QPvRRSe17AZUVI0V5jM'

        self.request_token_url  = 'http://twitter.com/oauth/request_token'
        self.access_token_url   = 'http://twitter.com/oauth/access_token'
        self.authorize_url      = 'http://twitter.com/oauth/authorize'
        
        self.oauth_token        = ''
        self.username	        = username
        self.password	        = password

    def auth(self):
        consumer    = oauth.Consumer(self.consumer_key, self.consumer_secret)
        client      = oauth.Client(consumer)

        resp, content   = client.request(self.request_token_url, "GET")
        if resp['status'] != '200':
            raise Exception("invalid response %s." % resp['status'])

        request_token = dict(urlparse.parse_qsl(content))
        
        username = self.username
        password = self.password

        resp, content = client.request(self.authorize_url, "POST", body="session[username_or_email]=%s&session[password]=%s&oauth_token=%s" % (username, password, request_token['oauth_token']))
        if resp['status'] != '200':
            raise Exception("invalid response %s to authorize." % resp['status'])
        parse = TwParser(content)
        oauth_verifier = parse.pin.strip()
        #print oauth_verifier
        token = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
        client = oauth.Client(consumer, token)

        resp, content = client.request(self.access_token_url, 'POST', body='oauth_verifier=%s' % oauth_verifier)
        access_token = dict(urlparse.parse_qsl(content))
        #print access_token
        conf = os.environ["HOME"]+os.sep+'.pytwitrc'

        config = ConfigParser.RawConfigParser()
        config.add_section('Profile')
        config.set('Profile', 'oauth_token', access_token['oauth_token'])
        config.set('Profile', 'oauth_token_secret', access_token['oauth_token_secret'])
        with open(conf, 'wb') as configfile:
            config.write(configfile)

        self.token()

    def token(self):
        path    = os.environ["HOME"]+os.sep+'.pytwitrc'
        if os.path.exists(path):
            config  = ConfigParser.ConfigParser()
            config.read(path)
        
            self.oauth_token = {'oauth_token':config.get('Profile','oauth_token'), 'oauth_token_secret':config.get('Profile','oauth_token_secret')}
        else:
            self.auth()

class PyTwit:
    def __init__(self, username, password):
        auth        = Auth(username, password)
        auth.token()
        token  = auth.oauth_token
        self.api    = twitter.Api(username=auth.consumer_key, password=auth.consumer_secret, access_token_key=token['oauth_token'], access_token_secret=token['oauth_token_secret'])
        #self.friends = ''

    def status(self, message):
        status = self.api.PostUpdate(message)
        print 'Last status: %s' % status

    def friends(self):
        friends = self.api.GetFriends()
        self.friends = []
        for friend in friends:
            self.friends.append(friend.name)

