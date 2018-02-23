import cookielib
import os
import urllib
import urllib2
import re
import string
from BeautifulSoup import BeautifulSoup

#############################################
username = ""
password = ""
companyID = ""
searchDepth = 5
#############################################



cookie_filename = "parser.cookies.txt"

class LinkedInParser(object):

    def __init__(self, login, password):
        """ Start up... """
        self.login = login
        self.password = password

        # Simulate browser with cookies enabled
        self.cj = cookielib.MozillaCookieJar(cookie_filename)
        if os.access(cookie_filename, os.F_OK):
            self.cj.load()
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cj)
        )
        self.opener.addheaders = [
            ('User-agent', ('Mozilla/5.0 (X11; Linux x86_64; rv:58.0) Gecko/20100101 Firefox/58.0'))
        ]

        # Login
        self.login_page()

        title = self.load_title()
        print title

        self.cj.save()


    def load_page(self, url, data=None):
        """
        Utility function to load HTML from URLs for us with hack to continue despite 404
        """
        # We'll print the url in case of infinite loop
        # print "Loading URL: %s" % url
        try:
            if data is not None:
                response = self.opener.open(url, data)
            else:
                response = self.opener.open(url)
            return ''.join(response.readlines())
        except:
            # If URL doesn't load for ANY reason, try again...
            # Quick and dirty solution for 404 returns because of network problems
            # However, this could infinite loop if there's an actual problem
            return self.load_page(url, data)

    def login_page(self):
        """
        Handle login. This should populate our cookie jar.
        """
        html = self.load_page("https://www.linkedin.com/")
        soup = BeautifulSoup(html)
        try:
            csrf = soup.find(id="loginCsrfParam-login")['value']
        except:
            csrf = ''
        login_data = urllib.urlencode({
            'session_key': self.login,
            'session_password': self.password,
            'loginCsrfParam': csrf,
        })

        html = self.load_page("https://www.linkedin.com/uas/login-submit", login_data)
        return

    def load_title(self):
        html = self.load_page("https://www.linkedin.com/feed/")
        soup = BeautifulSoup(html)
        return soup.find("title")

parser = LinkedInParser(username, password)

def scrape_info():
    print('Starting search....')
    for page in range(0, searchDepth):
        print('OK, looking for results on page ' + str(page+1))
        fullNameList = []
        url = 'https://www.linkedin.com/search/results/people/?facetCurrentCompany=%5B%22'+companyID+'%22%5D&page=' + str(page+1)
        result = parser.load_page(url)
        firstName = re.findall(r'firstName&quot;:&quot;(.*?)&', result)
        lastName = re.findall(r'lastName&quot;:&quot;(.*?)&', result)
        
        for first,last in zip(firstName,lastName):
            fullName = first + ' ' + last
            if fullName not in fullNameList:
                fullNameList.append(fullName)
    return fullNameList

def clean(list):
    cleanList = []
    for name in list:
        name = re.sub(r'[,(].*', '', name) # People have a habit of listing lame creds after their name. Gone!
        name = name.strip()
        if name not in cleanList:
            cleanList.append(name)
    return cleanList
        
def write_files(list):
    rawnames = open('rawnames.txt', 'w')
    flast = open('flast.txt', 'w')
    firstl = open('firstl.txt', 'w')
    firstlast = open('first.last.txt', 'w')
    for name in list:
        try:
            rawnames.write(name + '\n')
            parse = name.split(' ')
            flast.write(parse[0][0] + parse[-1] + '\n')
            firstlast.write(parse[0] + '.' + parse[-1] + '\n')
            firstl.write(parse[0] + parse[-1][0] + '\n')
        except:
            print('Choked on ' + name + ' but continuing...')

def main():
    fullNameList  = scrape_info()
    cleanList = clean(fullNameList)
    write_files(cleanList)
    print('All done! Check out your lovely new files.')

if __name__ == "__main__":
    main()
