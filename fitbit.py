__author__ = 'Andy'
"""
A Python library for accessing the FitBit API.

This library provides a wrapper to the FitBit API and does not provide storage of tokens or caching if that is required.

Most of the code has been adapted from: https://groups.google.com/group/fitbit-api/browse_thread/thread/0a45d0ebed3ebccb
"""
import os, httplib
from oauth import oauth
from xml.etree import ElementTree as ET
# Consumer Key and Secret resides in credentials
import credentials as my

# pass oauth request to server (use httplib.connection passed in as param)
# return response as a string
class FitBit():
    CONSUMER_KEY = my.CONSUMER_KEY
    CONSUMER_SECRET = my.CONSUMER_SECRET
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
    Debug = True
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
    weight = fb.ApiCall(access_token, '/1/user/-/body/log/weight/date/2013-12-30/7d.xml')
    fatlist = fb.ApiCall(access_token, '/1/user/-/body/log/fat/date/2013-12-30/7d.xml')
    if Debug:
        print weight
        print fatlist
    root = ET.fromstring(weight)
    data = {}

    for weightLog in root.iter('weightLog'):
        #print weightLog.attrib
        bmi = weightLog.find('bmi').text
        date = weightLog.find('date').text
        weight = weightLog.find('weight').text
        data.update({date: [weight, bmi, ]})
        #print date, weight,bmi
    if Debug:
        print data
    root = ET.fromstring(fatlist)
    for fatLog in root.iter('fatLog'):
        #print weightLog.attrib
        fat = fatLog.find('fat').text
        date = fatLog.find('date').text
        l = data.get(date)
        l.append(fat)
    if Debug:
        print data
    # sort dictionary
    sorted(data.iterkeys())
    for key, value in data.iteritems():
        gw = float(value[0])
        bmi = float(value[1])
        fat = float(value[2])
        print ("{0} {1} {2} {3}".format(key, gw, bmi, fat))
