__author__ = 'Andy'
"""
A Python library for accessing the FitBit API.

This library provides a wrapper to the FitBit API and does not provide storage of tokens or caching if that is required.

Most of the code has been adapted from: https://groups.google.com/group/fitbit-api/browse_thread/thread/0a45d0ebed3ebccb
"""
import os, httplib
from oauth import oauth
from xml.dom.minidom import parseString
import credentials

# pass oauth request to server (use httplib.connection passed in as param)
# return response as a string
class FitBit():
    CONSUMER_KEY = '53b4f8d0b6ab41fcacfa3ad135ae8a9e'
    CONSUMER_SECRET = 'acc5fb84273747b8916a3dfd253f2427'
    SERVER = 'api.fitbit.com'
    REQUEST_TOKEN_URL = 'http://%s/oauth/request_token' % SERVER
    ACCESS_TOKEN_URL = 'http://%s/oauth/access_token' % SERVER
    AUTHORIZATION_URL = 'http://www.fitbit.com/oauth/authorize'
    DEBUG = False

    def FetchResponse(self, oauth_request, connection, debug=DEBUG):
        url = oauth_request.to_url()
        connection.request(oauth_request.http_method, url)
        response = connection.getresponse()
        s = response.read()
        if debug:
            print 'requested URL: %s' % url
            print 'server response: %s' % s
        return s

    def GetRequestToken(self):
        connection = httplib.HTTPSConnection(self.SERVER)
        consumer = oauth.OAuthConsumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, http_url=self.REQUEST_TOKEN_URL)
        oauth_request.sign_request(signature_method, consumer, None)

        resp = self.FetchResponse(oauth_request, connection)
        auth_token = oauth.OAuthToken.from_string(resp)

        #build the URL
        authkey = str(auth_token.key)
        print auth_token.key
        print authkey
        authsecret = str(auth_token.secret)
        auth_url = "%s?oauth_token=%s" % (self.AUTHORIZATION_URL, auth_token.key)
        return auth_url, auth_token

    def GetAccessToken(self, access_code, auth_token):
        oauth_verifier = access_code
        connection = httplib.HTTPSConnection(self.SERVER)
        consumer = oauth.OAuthConsumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=auth_token,
                                                                   http_url=self.ACCESS_TOKEN_URL,
                                                                   parameters={'oauth_verifier': oauth_verifier})
        oauth_request.sign_request(signature_method, consumer, auth_token)
        # now the token we get back is an access token
        # parse the response into an OAuthToken object
        access_token = oauth.OAuthToken.from_string(self.FetchResponse(oauth_request, connection))

        # store the access token when returning it
        access_token = access_token.to_string()
        return access_token

    def ApiCall(self, access_token, apiCall):
        #other API Calls possible, or read the FitBit documentation for the full list.
        #apiCall = '/1/user/-/devices.json'
        #apiCall = '/1/user/-/profile.json'
        #apiCall = '/1/user/-/activities/date/2011-06-17.json'
        print apiCall
        signature_method = oauth.OAuthSignatureMethod_PLAINTEXT()
        connection = httplib.HTTPSConnection(self.SERVER)
        #build the access token from a string
        access_token = oauth.OAuthToken.from_string(access_token)
        consumer = oauth.OAuthConsumer(self.CONSUMER_KEY, self.CONSUMER_SECRET)
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, token=access_token, http_url=apiCall)
        oauth_request.sign_request(signature_method, consumer, access_token)
        headers = oauth_request.to_header(realm='api.fitbit.com')
        connection.request('GET', apiCall, headers=headers)
        resp = connection.getresponse()
        json = resp.read()
        return json


if __name__ == '__main__':
    Debug=False
    ACCESS_TOKEN_STRING_FNAME = 'access_token.string'
    fb = FitBit()
    if not os.path.exists(ACCESS_TOKEN_STRING_FNAME):
        auth_url, auth_token = fb.GetRequestToken()
        print auth_url
        oauth_verifier = raw_input(
            'Please go to the above URL and authorize the ' +
            'app -- Type in the Verification code from the website, when done: ')
        access_token = fb.GetAccessToken(oauth_verifier, auth_token)
        print "Access Token: %s" % (access_token)
        fobj = open(ACCESS_TOKEN_STRING_FNAME, 'w')
        fobj.write(access_token)
        fobj.close()

    else:
        fobj = open(ACCESS_TOKEN_STRING_FNAME)
        access_token = fobj.read()
        fobj.close()
        if Debug:
            print "Access Token %s" % (access_token)
        #access_token = oauth.OAuthToken.from_string(access_token_string)
    #print access_token
    weight=fb.ApiCall(access_token, '/1/user/-/body/log/weight/date/2013-12-21/7d.xml')
    print type(weight)
    print weight
    #parse the xml you downloaded
    dom = parseString(weight)
    #retrieve the first xml tag (<tag>data</tag>) that the parser finds with name tagName:
    xmlTag = dom.getElementsByTagName('weight')[0].toxml()
    #strip off the tag (<tag>data</tag>  --->   data):
    xmlData=xmlTag.replace('<weight>','').replace('</weight>','')
    #print out the xml tag and data in this format: <tag>data</tag>
    print xmlTag
    #just print the data
    print xmlData
