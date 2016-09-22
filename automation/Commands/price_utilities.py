# get links and prices in this format: {link: price}
#import jellyfish
import collections
from bs4 import BeautifulSoup
from re import sub
import re
from decimal import Decimal
#import urlparse
import os, time
import urllib
from operator import itemgetter
import math
#import analyze_utitilities

def to_number(s_money):
    '''convert a string to a number'''
    #print("This is number:",s_money)
    c = s_money
    if ',' in s_money:
        # convert all commas to dot
        s_money = s_money.replace(',','.')
        b = [m.start() for m in re.finditer('\.', s_money)] #array of . position
        #a = '1.028.550.00'
        c = s_money.replace('.','',len(b) - 1)
        #print c
    #return to_number_advance(s_money)
    #tmp = s_money
    #convert to us-number standard
    #if there is , ==> remove all .
    # then replace , by .
    return float(sub(r'[^\d.]', '', c))

def get_everage_price(html):
    '''get average price of the file given'''
    price_list = []
#    av = 0
    total = 0
    html = BeautifulSoup(html,'lxml')
    prices2 = html.select('span[class="price"]')
    for p in prices2:
        total = total + to_number(p.text)
        price_list.append(to_number(p.text))
    #print('Total is:'+ str(total))
    #print("evarage is:" + str(total/len(prices2)))
    return (total/len(prices2)),price_list

def everage_price_of_a_product_type(product, base, files, email):
    '''
    base: base folder of files, path in text format i.e., /home/vino/folder
    product-string: "food"
    files: list of files
    email:
    NOTE: this function is a mess, do not use it
    '''
    nolog = []
    login = []
    #nolog_total = []
    #login_total = []
    print("Product: " + product)
    for f in files:
        if product in f:
            print "file:" + f
            av,_ = get_everage_price(f)
            if 'nologin' in f:
                nolog.append(av)
            else:
                login.append(av)
    #write average price to file:
    f = open(os.path.join(base,product+'.'+email+'.txt'),'w')

    f.write(email)
    for i in login:
        f.write('|'+str(i))
    f.write('\nnologin')
    for i in nolog:
        f.write('|' + str(i))
    f.close()
    return login, nolog

def get_all_products_prices_links(html_content):
    """
    This function extracts all links and prices in google shopping pages.
    Return a dictionary in this format dict {link@_@link_text:price}\n
    html_content: html text, this is a string
    """
    html = BeautifulSoup(html_content,'lxml')
    k = html.select('h3 a[jsaction="spop.c"]')
    #print("DEBUG:Length of h3:"+str(len(k)))
    #print(k[0])
    links = []
    for i in k:
        href = i['href']
        text = i.getText().strip()
        #print("Href text:"+text)
        sep = '@_@'
        text = sep + text
        if href.startswith('/url?url='):
            l = href.split("url=")[1]
            if '%' in l :
                l2 = href.split('%')[0].split('url=')[1]
                links.append(l2.strip()+text)
                #print("l2 is:" + l2)
            else:
                links.append(l+text)
        elif href.startswith('/shopping'):
            links.append(href.split("?")[0].strip() + text)
            #print i['href'].split("?")[0]
        elif href.startswith('/aclk?'):
            decode = urllib.unquote(href).decode('utf-8')
            if 'ds_dest_url=' in decode:
                links.append(decode.split('ds_dest_url=')[-1].split('?utm_source')[0].strip() + text)
            elif 'adurl=' in decode:
                links.append(decode.split('adurl=')[-1].strip() + text)#.split('?utm_source')[0]
            else:
                print('what the hell::') + decode
        else: #start by http://www or https://
            #print("=="+href)
            links.append(href.split("?")[0].strip()+text)
    prices = html.select('span[class="price"]')
    prices2 = []
    for p in prices:
    #print p.getText()
        prices2.append(to_number(p.getText().strip()))
    odict = collections.OrderedDict(zip(links, prices2))
    return odict


def get_top_n_most_expensive_product(odict, condition):
    '''
    odict: the return value from get_all_products_prices_links()
    condition: a number link to click, -3( 3 cheapeast) or 3 (3 most expensieve)
    '''
    #step 1
    #sorting the dictionary
    from collections import OrderedDict
    desending = OrderedDict(sorted(odict.items(), key=itemgetter(1),reverse=True))#sort desending
    asending = OrderedDict(sorted(odict.items(), key=itemgetter(1)))
    new_dict = OrderedDict()
    try:
        condition = int(condition)
    except:
        print('condition is not an interger')
    if type(condition) is int: # get n-top price with links
        if abs(condition) >=len(odict):
            print('Index is more than size of dictionary')
            return new_dict
        for i in range(0,abs(condition)):
            if condition > 0:
                #print(condition)
                new_dict[desending.keys()[i]] = desending.values()[i]
            if condition < 0:
                #print(condition)
                new_dict[asending.keys()[i]] = asending.values()[i]
    else:
        print "Condition is wrong. Get the highest one"
        #get highest one here
    #print new_dict
    return new_dict



def ncdg_prepare(file_list):
    '''
    file_list: list of file to calculate the ideal li
    '''
    #step 1: generate ideal price list, descending ordering
    t_set = set()
    for file_ in file_list:
        '''
        get the list of price order in the file

        '''
        f = open(file_,'rt')
        html = f.read().strip()
        f.close()
        odict = get_all_products_prices_links(html)
        for k,v in odict.items():
            #print k,v
            #str1 = unicode(k, 'utf-8',errors='ignore')
            #str2 = unicode(v, 'utf-8',errors='ignore')
            #s = str1 + "@_@" + str2
            s = k + "@_@" + str(v)
            t_set.add(s)

    prices = [] #this is ideal price list, descending order
    for i in t_set:
        prices.append(float(i.split("@_@")[-1]))
    #return t_set
    prices = sorted(prices, reverse = True)

    return prices

def cdg_calculate(prices):
    gain_score = 0.0
    if len(prices) > 1:
        for i in range(1,len(prices)):
            #print (prices[i])
            gain_score += float(prices[i])/(math.log(i+1,2))
            #gain_score =  (math.pow(2, float(prices[i]))-1)/(math.log(i+1,2))
        gain_score = float(prices[0]) + gain_score
    elif len(prices) == 1: #only one element
        return float(prices[0])
    elif len(prices) <=0:
        print('Exception occurs. There is no price')
    return gain_score

def ncdg_calculate(file_, file_list):
    """
    Calucate ncdg \n
    file_: file to calculate the ncdg \n
    file_list: list of file to make reference point when calucate ncdg, this list
    must include {_file}
    """

    f = open(file_,'rt')
    html = f.read().strip()
    f.close()

    prices_dict = get_all_products_prices_links(html)
    prices = prices_dict.values()
    #prices = sorted(prices_dict.values(),reverse=False)
    prices_ideals = ncdg_prepare(file_list)

    #print prices

    ncdg = cdg_calculate(prices)/cdg_calculate(prices_ideals)
    return ncdg


def leven_kendal(page1, page2):
    pass

def test_dcn():
    file1 = 'xxx.concord watch.shopping_testing.0.html'
    file2 = 'xxxtesting.0.html'

    f = [file1,file2]

    print ncdg_calculate(file1,f)
    #print ncdg
    #x,y = analyze_utitilities.Measurements.editdist_and_kendalltau(file1,file2)
    #print x,y

def main_test():
    ##########
    INPUT_ID = "lst-ib"
    ##########

    from selenium.webdriver.common.keys import Keys                     # to press keys on a webpage
    from selenium import webdriver
    driver = webdriver.Firefox()
    url = 'https://www.google.com/?&hl=en'
    driver.get(url)
    driver.find_element_by_id(INPUT_ID).clear()
    driver.find_element_by_id(INPUT_ID).send_keys('chocolate')
    driver.find_element_by_id(INPUT_ID).send_keys(Keys.RETURN)
    time.sleep(1)
    _url_shop = driver.current_url + "&tbm=shop" ##&num=30 is the maximum number
    driver.get(_url_shop)
    time.sleep(1)
    #driver.get(_url_shop)
    html = driver.page_source.encode('utf8') # need unicode for writing
    # get all product
    odict = get_all_products_prices_links(html)
    ## search for the hight prices
    ## get the links of the height prices
    get_top_n_most_expensive_product(odict, 3)
    #sleep(10)
#main_test()
