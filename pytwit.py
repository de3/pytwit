#!/usr/bin/env python

import os
import ConfigParser
import urlparse
import oauth2 as oauth
import twitter
import BeautifulSoup
import getopt
import sys

class Auth:

    def __init__(self, username, password=''):
        self.consumer_key       = 'Ku59hdNBCxX58MC8oQpfbA'
        self.consumer_secret    = 'OzWeLSE3iufvgxedkKEYg2QPvRRSe17AZUVI0V5jM'

        self.request_token_url  = 'http://twitter.com/oauth/request_token'
        self.access_token_url   = 'http://twitter.com/oauth/access_token'
        self.authorize_url      = 'http://twitter.com/oauth/authorize'
        
        self.oauth_token        = {}
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
        
        try:
            self.checktoken()
        except:
            resp, content = client.request(self.authorize_url, "POST", body="session[username_or_email]=%s&session[password]=%s&oauth_token=%s" % (username, password, request_token['oauth_token']))
            if resp['status'] != '200':
                raise Exception("invalid response %s to authorize." % resp['status'])

            oauth_verifier  = BeautifulSoup.BeautifulSoup(content).find('div', attrs={'id':'oauth_pin'}).string.strip()
            token           = oauth.Token(request_token['oauth_token'], request_token['oauth_token_secret'])
            client          = oauth.Client(consumer, token)

            resp, content   = client.request(self.access_token_url, 'POST', body='oauth_verifier=%s' % oauth_verifier)
            access_token    = dict(urlparse.parse_qsl(content))
            
            # Write Config
            conf = os.environ["HOME"]+os.sep+'.pytwitrc'
            config = ConfigParser.RawConfigParser()
            config.add_section(username)
            config.set(username, 'oauth_token', access_token['oauth_token'])
            config.set(username, 'oauth_token_secret', access_token['oauth_token_secret'])
            with open(conf, 'a+b') as configfile:
                config.write(configfile)

            self.checktoken()

    def checktoken(self):
        conf = os.environ["HOME"]+os.sep+'.pytwitrc'
        config = ConfigParser.RawConfigParser()
        config.readfp(open(conf))
        self.oauth_token['oauth_token']         = config.get(self.username, 'oauth_token')
        self.oauth_token['oauth_token_secret']  = config.get(self.username, 'oauth_token_secret')

class PyTwit:
    def __init__(self, username, password):
        auth        = Auth(username, password)
        auth.auth()
        token  = auth.oauth_token
        self.api    = twitter.Api(username=auth.consumer_key, password=auth.consumer_secret, access_token_key=token['oauth_token'], access_token_secret=token['oauth_token_secret'])
        self.username = username
        self.friends = []
        self.timeline = []

    def Status(self, message):
        status = self.api.PostUpdate(message)
        print 'Last status: %s' % status

    def Friends(self):
        friends = self.api.GetFriends()
        for friend in friends:
            self.friends.append(friend.name)
	
    def Timeline(self):
        timeline = self.api.GetFriendsTimeline(self.username)
        return timeline
    
    def Search(self, term):
        res = self.api.GetSearch(term)
        return res

def Usage():
    print """
    Example:
        $ python pytwit.py -u your_username -p your_password -a status -s "your message"
    
    Available option:
    -u                  : Twitter username
    --username
    
    -p                  : Twitter password, you can give null value if your token already write in pytwitrc
    --password            Example:
                            $ python pytwit.py -u your_username -a timeline
    
    -a                  : What action you want do
    --action              Available Action:
                            status      : Post your status with option -s or --status
                            timeline    : view your timeline
                            friends     : View your friend lists
                            search      : Search something
    
    -s                  : Message that you want to post to your timeline
    --status
    """
    
if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:p:a:s:",["help","username=","password=","action=","status="])
    except getopt.GetoptError, err:
        print str(err)
        Usage()
        sys.exit(2)
    
    username = None
    password = None
    action  = None
    
    for o,a in opts:
        if o in ("-h", "--help"):
            Usage()
            sys.exit()
        elif o in ("-u", "--username"):
            username = a
        elif o in ("-p", "--password"):
            password = a
        elif o in ("-a", "--action"):
            action = a
        elif o in ("-s", "--status"):
            status = a
    
    a = PyTwit(username, password)
    if action == "friends":
        a.Friends()
        print a.friends
    elif action == "status":
        a.Status(status)
    elif action == "timeline":
        a.Timeline()
        print a.timeline 
