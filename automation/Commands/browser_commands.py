from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import MoveTargetOutOfBoundsException
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

import collections
import random
import time
#import numpy
import os
import traceback # for debugging purpose


from ..SocketInterface import clientsocket
from ..MPLogger import loggingclient
from utils.lso import get_flash_cookies
from utils.firefox_profile import get_cookies  # todo: add back get_localStorage,
from utils.webdriver_extensions import scroll_down, wait_until_loaded, get_intra_links

import logging
# Library for core WebDriver-based browser commands

# Library for handling Google Shopping page
import price_utilities

GOOGLE_SHOP_URL = 'https://shopping.google.com/?&hl=en'
DEFAULT_CONDITION_CLICK_PRICE = 3  # click on the 3 most expensive links
PRICE_FILE = '_price.txt'
MEAN_VISIT = 30 # mean of waiting time between each search (google shopping search)
input_shop_id = 'gbqfq' # id of search button on Google Shopping

NUM_MOUSE_MOVES = 10  # number of times to randomly move the mouse as part of bot mitigation
RANDOM_SLEEP_LOW = 1  # low end (in seconds) for random sleep times between page loads (bot mitigation)
RANDOM_SLEEP_HIGH = 7  # high end (in seconds) for random sleep times between page loads (bot mitigation)

#=================HELPER function========================
# those functions help to save html file in harddisk, because testing
# run many round with the same test keywords therefore the saving html file must be
# number
def create_folder(directory):
    """create folder to store all files: html, txt"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return

def create_new_file_name(manager_params, browser_params, term):  # folder, term is suffix
    """
    generate file_name for new saving file.
    email: ...
    term.1.html --> 1st testing time
    term.2.html --> 2nd testing time
    """
    i = 0
    #print("st1")
    email = browser_params["id"]
    #print("st2")
    name = email + "." + term + "." + str(i) + ".html"
    #print("st3")
    #print(name)
    #print(email)
    while (os.path.exists(os.path.join(email, name))):
        i = i + 1
        name = email + "." + term + "." + str(i) + ".html"
    return name

def save_html_page(manager_params, browser_params,html, term,saving=True):
    """
    saving html page to disk.
    """
    #saving=False
    create_folder(manager_params['data_directory'])
    #create_folder(browser_params["id"])
    create_folder(os.path.join(manager_params['data_directory'], browser_params["id"]))
    html_name = create_new_file_name(manager_params,browser_params, term)

    if saving is True:
        with open(os.path.join(manager_params['data_directory'],
                               browser_params["id"],
                               html_name), 'w') as temp_file:
            #print('saving html')
            temp_file.write(html)
    return html_name

# usage
#file_name = self.save_html_page(
#    html, self.user_name, term + ".shopping" + f_name,saving=(not training))
#========================================================

def bot_mitigation(webdriver):
    """ performs three optional commands for bot-detection mitigation when getting a site """

    # bot mitigation 1: move the randomly around a number of times
    window_size = webdriver.get_window_size()
    num_moves = 0
    num_fails = 0
    while num_moves < NUM_MOUSE_MOVES + 1 and num_fails < NUM_MOUSE_MOVES:
        try:
            if num_moves == 0: #move to the center of the screen
                x = int(round(window_size['height']/2))
                y = int(round(window_size['width']/2))
            else: #move a random amount in some direction
                move_max = random.randint(0,500)
                x = random.randint(-move_max, move_max)
                y = random.randint(-move_max, move_max)
            action = ActionChains(webdriver)
            action.move_by_offset(x, y)
            action.perform()
            num_moves += 1
        except MoveTargetOutOfBoundsException:
            num_fails += 1
            #print "[WARNING] - Mouse movement out of bounds, trying a different offset..."
            pass

    # bot mitigation 2: scroll in random intervals down page
    scroll_down(webdriver)

    # bot mitigation 3: randomly wait so that page visits appear at irregular intervals
    time.sleep(random.randrange(RANDOM_SLEEP_LOW, RANDOM_SLEEP_HIGH))


def tab_restart_browser(webdriver):
    """
    kills the current tab and creates a new one to stop traffic
    note: this code if firefox-specific for now
    """
    if webdriver.current_url.lower() == 'about:blank':
        return

    switch_to_new_tab = ActionChains(webdriver)
    switch_to_new_tab.key_down(Keys.CONTROL).send_keys('t').key_up(Keys.CONTROL)
    switch_to_new_tab.key_down(Keys.CONTROL).send_keys(Keys.PAGE_UP).key_up(Keys.CONTROL)
    switch_to_new_tab.key_down(Keys.CONTROL).send_keys('w').key_up(Keys.CONTROL)
    switch_to_new_tab.perform()
    time.sleep(0.5)


def get_website(url, sleep, visit_id, webdriver, proxy_queue, browser_params, extension_socket):
    """
    goes to <url> using the given <webdriver> instance
    <proxy_queue> is queue for sending the proxy the current first party site
    """

    tab_restart_browser(webdriver)
    main_handle = webdriver.current_window_handle

    # sends top-level domain to proxy and extension (if enabled)
    # then, waits for it to finish marking traffic in proxy before moving to new site
    if proxy_queue is not None:
        proxy_queue.put(visit_id)
        while not proxy_queue.empty():
            time.sleep(0.001)
    if extension_socket is not None:
        extension_socket.send(visit_id)

    # Execute a get through selenium
    try:
        webdriver.get(url)
        if 'api.ipify.org' in url:
            try:
                print("Ip of "+str(visit_id)+":" + webdriver.find_element_by_tag_name('body').text)
                #print(webdriver.find_element_by_tag_name('body').text)
            except Exception as e:
                print("Exception"+str(visit_id)+" when getting ip")
                pritn(e)
    except TimeoutException:
        pass

    # Sleep after get returns
    time.sleep(sleep)

    # Close modal dialog if exists
    try:
        WebDriverWait(webdriver, .5).until(EC.alert_is_present())
        alert = webdriver.switch_to_alert()
        alert.dismiss()
        time.sleep(1)
    except TimeoutException:
        pass

    # Close other windows (popups or "tabs")
    windows = webdriver.window_handles
    if len(windows) > 1:
        for window in windows:
            if window != main_handle:
                webdriver.switch_to_window(window)
                webdriver.close()
        webdriver.switch_to_window(main_handle)

    if browser_params['bot_mitigation']:
        bot_mitigation(webdriver)

def extract_links(webdriver, browser_params, manager_params):
    link_elements = webdriver.find_elements_by_tag_name('a')
    link_urls = set(element.get_attribute("href") for element in link_elements)

    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
    create_table_query = ("""
    CREATE TABLE IF NOT EXISTS links_found (
      found_on TEXT,
      location TEXT
    )
    """, ())
    sock.send(create_table_query)

    if len(link_urls) > 0:
        current_url = webdriver.current_url
        insert_query_string = """
        INSERT INTO links_found (found_on, location)
        VALUES (?, ?)
        """
        for link in link_urls:
            sock.send((insert_query_string, (current_url, link)))

    sock.close()

def browse_website(url, num_links, sleep, visit_id, webdriver, proxy_queue,
                   browser_params, manager_params, extension_socket):
    """Calls get_website before visiting <num_links> present on the page.

    Note: the site_url in the site_visits table for the links visited will
    be the site_url of the original page and NOT the url of the links visited.
    """
    # First get the site
    get_website(url, sleep, visit_id, webdriver, proxy_queue, browser_params, extension_socket)

    # Connect to logger
    logger = loggingclient(*manager_params['logger_address'])

    # Then visit a few subpages
    for i in range(num_links):
        links = get_intra_links(webdriver, url)
        links = filter(lambda x: x.is_displayed() == True, links)
        if len(links) == 0:
            break
        r = int(random.random()*len(links)-1)
        logger.info("BROWSER %i: visiting internal link %s" % (browser_params['crawl_id'], links[r].get_attribute("href")))

        try:
            links[r].click()
            wait_until_loaded(webdriver, 300)
            time.sleep(max(1,sleep))
            if browser_params['bot_mitigation']:
                bot_mitigation(webdriver)
            webdriver.back()
        except Exception, e:
            pass

def dump_flash_cookies(start_time, visit_id, webdriver, browser_params, manager_params):
    """ Save newly changed Flash LSOs to database

    We determine which LSOs to save by the `start_time` timestamp.
    This timestamp should be taken prior to calling the `get` for
    which creates these changes.
    """
    # Set up a connection to DataAggregator
    tab_restart_browser(webdriver)  # kills traffic so we can cleanly record data
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    # Flash cookies
    flash_cookies = get_flash_cookies(start_time)
    for cookie in flash_cookies:
        query = ("INSERT INTO flash_cookies (crawl_id, visit_id, domain, filename, local_path, \
                  key, content) VALUES (?,?,?,?,?,?,?)", (browser_params['crawl_id'], visit_id, cookie.domain,
                                                          cookie.filename, cookie.local_path,
                                                          cookie.key, cookie.content))
        sock.send(query)

    # Close connection to db
    sock.close()

def dump_profile_cookies(start_time, visit_id, webdriver, browser_params, manager_params):
    """ Save changes to Firefox's cookies.sqlite to database

    We determine which cookies to save by the `start_time` timestamp.
    This timestamp should be taken prior to calling the `get` for
    which creates these changes.

    Note that the extension's cookieInstrument is preferred to this approach,
    as this is likely to miss changes still present in the sqlite `wal` files.
    This will likely be removed in a future version.
    """
    # Set up a connection to DataAggregator
    tab_restart_browser(webdriver)  # kills traffic so we can cleanly record data
    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])

    # Cookies
    rows = get_cookies(browser_params['profile_path'], start_time)
    if rows is not None:
        for row in rows:
            query = ("INSERT INTO profile_cookies (crawl_id, visit_id, baseDomain, name, value, \
                      host, path, expiry, accessed, creationTime, isSecure, isHttpOnly) \
                      VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (browser_params['crawl_id'], visit_id) + row)
            sock.send(query)

    # Close connection to db
    sock.close()
def extract_links_with_extension(webdriver, browser_params, manager_params):
    link_elements = webdriver.find_elements_by_tag_name('a')
    link_urls = set(element.get_attribute("href") for element in link_elements)

    sock = clientsocket()
    sock.connect(*manager_params['aggregator_address'])
    create_table_query = ("""
    CREATE TABLE IF NOT EXISTS links_found_extension (
    crawl_id TEX,
    found_on TEXT,
    location TEXT
    )
    """, ())
    sock.send(create_table_query)

    if len(link_urls) > 0:
        current_url = webdriver.current_url
        insert_query_string = """
        INSERT INTO links_found_extension (crawl_id, found_on, location)
        VALUES (?, ?, ?)
        """
        for link in link_urls:
            sock.send((insert_query_string, (browser_params['crawl_id'],current_url, link)))

    sock.close()
def login_google(webdriver, browser_params, manager_params):
    """ Log in Google with id and password from browser_params
    browser_param["id"]: user name of google account
    browser_params["pass"]: associated password of that accounts
    """
    try:
        # before log in, must go to Google home page, use ncr version because of language of id, like "Email"
        google_url = 'https://www.google.com/ncr'
        #webdriver.maximize_window()
        webdriver.get(google_url)
        webdriver.find_element_by_id("gb_70").click()
        webdriver.find_element_by_id("Email").clear()
        webdriver.find_element_by_id("Email").send_keys(browser_params["id"])
        webdriver.find_element_by_id("next").click()
        time.sleep(5)
        webdriver.find_element_by_id("Passwd")
        webdriver.find_element_by_id("Passwd").clear()
        webdriver.find_element_by_name('Passwd')

        webdriver.find_element_by_id("Passwd").send_keys(browser_params["pass"])
        time.sleep(3)
        webdriver.find_element_by_id("signIn").click()

    except Exception as e:
        #self.log('error', 'logging in to google', browser_params["id"])
        #self.my_log.critical("Log in google unsuccessfully!")
        #print(e)
        traceback.print_exc()
    time.sleep(3)

def browse_training_websites(sleep, visit_id, webdriver, proxy_queue, browser_params, extension_socket):
    """Visit many websites in the browser_params["training_websites"],
        Args:
            sleep (int): sleep time between browsing
    """
    # load the training sites
    training_sites = [site for site in open(browser_params["training_sites"])]
    for url in training_sites:
        if not url.startswith("http"):
            url = "http://" + url
        # sleep a while before moving to another link, between 10 and 60 seconds
        import random # write import here to reduce the code change, our changes will be only one place
        sleep_time = random.randint(10,60)
        get_website(url, sleep_time, visit_id, webdriver, proxy_queue, browser_params, extension_socket)


def single_search_google_shopping(webdriver, term, browser_params, manager_params, number_of_links_to_click=-2, training=True):
    """Search for one term on Google Shopping
    Args:
        term: term to search on Google Shopping
    Return:
        None, return nothing
    """
    driver = webdriver
    driver.set_page_load_timeout(60)
    logger = my_log = loggingclient(*manager_params['logger_address'])
    my_log.debug("BROWSER %i measurement function %s" %(browser_params['crawl_id'],
                                                        browser_params["id"]))
    try:
        time.sleep(1)
        driver.get(GOOGLE_SHOP_URL)
        time.sleep(2)
        my_log.info('BROWSER %i: %s - searching for: %s' %(browser_params['crawl_id'],
                                                           str(browser_params["id"]),term))
        driver.find_element_by_id(input_shop_id).clear()
        driver.find_element_by_id(input_shop_id).send_keys(term)
        driver.find_element_by_id(
            input_shop_id).send_keys(Keys.RETURN)
        time.sleep(5)  # must sleep to wait for loading page
        html = driver.page_source.encode('utf8')  # need unicode for writing
        time.sleep(3) # time to fininish execution of above function
        odict = price_utilities.get_all_products_prices_links(html)
        average_price = -1
        try:
            average_price, _ = price_utilities.get_everage_price(html)
            #TODO: save average_price into database
        except Exception as e:
            average_price = 'NA'
            #print(e)
            traceback.print_exc()
        logger.info("BROWSER %i: Average price is %s" %(browser_params['crawl_id'],
                                                        average_price))
        #----
        #----
        if training is True:
            url = driver.current_url
            clicked_dict1 = click_on_links(browser_params, manager_params, webdriver,
                odict,number_of_links_to_click)
            logger.info("BROWSER {}: Click on those link: {}".format(browser_params['crawl_id'],
                                                                     clicked_dict1))
            #print("finish===================")
            try:
                clicked_dict2 = click_links_in_training_sites(manager_params, webdriver,
                                                              browser_params, odict,
                                                              train = True, no_click = False,
                                                              average_price = 2000000)
                #print (clicked_dict2)
            except Exception as e:
                print('Excecption:',e)
                traceback.print_exc()

        # if this is testing phase, only search and save file
        if training is False:
            #click_links_in_training_sites(odict, train=False)
            name = save_html_page(manager_params, browser_params, html, term, saving=True)
            #print(name)
            logger.info("BROWSER %i: saving file %s" %(browser_params['crawl_id'],
                                                            name))
            #print(False)
            #saving file
    except Exception as e:
        #print(e)
        logger.critical('BROWSER %i: error in google search personas: %s' %
                        (browser_params['crawl_id'],term))
    finally:
        traceback.print_exc()
    #time.sleep(30)
    return

def click_links_in_training_sites(manager_params, webdriver, browser_params, odict, train = True, no_click = False, average_price = 2000000):
    """click on a link if it is on training website's list
    Args:
        - no_click : True, function returns imediately
        - odict: dictionary of get_all_products_prices_links(html_content)
        - train: default is true: True if this is training phase, False if testing phase
        - if train is True: click on the link when link inside visted website list, otherwise not
    Return:
        - a dictionary of links which are inside visited website list
        by default, does not click on any links
    """
    logger = loggingclient(*manager_params['logger_address'])

    clicked_link_dict = collections.OrderedDict()
    if no_click is True: # do not click
        return clicked_link_dict

    driver = webdriver
    links_dict = odict  # price_utilities.get_all_products_prices_links(html_content)
    links = [
        key.lower() for key in links_dict.keys()]  # .split("@_@")[0] {google.com@_@Google Search@_@20}, key is 20
    #print("list of training site:")

    _url = webdriver.current_url
    training_sites = [site.lower() for site in open(browser_params["training_sites"])]
    #print(training_sites)
    #print(links)
    #import time
    #time.sleep(211)
    nu = 0
    # click only for 2 links
    for site in training_sites:
        for link in links:
            if site in link:
                if train is False:
                    clicked_link_dict[link] = links_dict[link]
                if train is True:
                    if links_dict[link] < average_price:
                        return
                    #self.my_log.debug('visit this %s',link)
                    try:
                        if nu>1: # only click on the first link which is also inside the training sites
                            break
                        nu = nu + 1
                        if link.endswith('...'):
                            link = link[:-4].strip()
                        driver.find_elements_by_partial_link_text(
                            link.split("@_@")[-1])[-1].click()
                        time.sleep(5)
                        #.my_log.debug('visite step 2:2nd click')
                        try:
                            driver.find_elements_by_partial_link_text(
                            link.split("@_@")[-1])[-1].click()

                        except TimeoutException:
                            driver.back()
                        time.sleep(5)
                        clicked_link_dict[link] = links_dict[link]
                        scroll_down(driver)
                        time.sleep(2)
                        driver.back()
                    except:
                        driver.get(_url)
                        break
    return clicked_link_dict
def click_on_links(browser_params, manager_params ,driver, odict, number_of_results_to_click):
    """Click on n number of links, depends on value of number_of_results_to_click
    Args:
        number_of_results_to_click: number of links to click; can be postive or negative;
                + positive, i.e., number_of_results_to_click=3: click on top 3 most expensive products
                + negavie , i.e. number_of_results_to_click=-3, click on top 3 cheapest products
    """
    logger = loggingclient(*manager_params['logger_address'])
    # get number_of_results_to_click (-th top cheapest or -th most expensive links and )
    most_expensive = price_utilities.get_top_n_most_expensive_product(
        odict,number_of_results_to_click)
    #print(most_expensive)
    # to store which links are click, and prices of those links
    clicked_link_dict = collections.OrderedDict()

    for k in most_expensive.keys():
        # i.e,. k = shopping/product/12137993817137030622@_@Garden of Life Perfect Food Raw Organic Green Super Food Powder - 8.5 oz jar', 30.25
        link_text = k.split('@_@')[-1].strip()
        if link_text.endswith('...'):
            link_text = link_text[:-4].strip()
        # print(link_text)
        try:
            if len(driver.find_elements_by_partial_link_text(link_text)) < 1:
                continue
            driver.find_elements_by_partial_link_text(
                link_text)[-1].click()
            logger.info('BROWSER %i: Click on: %s' % (browser_params['crawl_id'],
                                                       link_text))
            #logger.debug("Clic")
            time.sleep(3)
            driver.find_elements_by_partial_link_text(link_text)[
                -1].click()  # this is the trick of google, must click twice
            time.sleep(3)
            scroll_down(driver)
            time.sleep(3)
            clicked_link_dict[k] = most_expensive[k]
            driver.back()
        except Exception, e:
            print(e)
            traceback.print_exc()
        finally:
            return clicked_link_dict
def multiple_search_google_shopping(webdriver, browser_params, manager_params,
                                    number_of_links_to_click=-2, training=True,
                                    sleep_time=30):
    # load all search terms
    #TODO: insert to database
    #step 1: create the table here
    #step 2: insert all the values to to the db
    term = ()
    logger = loggingclient(*manager_params['logger_address'])
    if training is True:
        terms = [term.strip() for term in open(browser_params["training_keywords"]) ]
    else:
        terms = [term.strip() for term in open(browser_params["testing_keywords"]) ]
    # search one by one
    logger.info("BROWSER {}:{}".format(browser_params['crawl_id'],terms))
    for term in terms:
        logger.info("BROWSER %i: search term %s"%(browser_params['crawl_id'], term))
        single_search_google_shopping(webdriver, term, browser_params, manager_params,
                                      number_of_links_to_click=number_of_links_to_click,
                                      training=training)
        time.sleep(sleep_time)
        #print("finish term %s"%(term))


def single_search_google_shopping_by_index(webdriver, index_of_term, browser_params,
                                             manager_params,
                                             training=True):
    """Search for one term on Google Shopping
    Args:
        term: term to search on Google Shopping
    Return:
        None, return nothing
    """
    logger = loggingclient(*manager_params['logger_address'])
    if training is True:
        terms = [term.strip() for term in open(browser_params["training_keywords"]) ]
    else:
        terms = [term.strip() for term in open(browser_params["testing_keywords"]) ]
    if index_of_term > len(terms):
        logger.debug("BROWSER {}: index = {} is not valid.".format(browser_params['crawl_id'],
                                                                   index_of_term))
        return
    term = terms[index_of_term]
    number_of_links_to_click=int(browser_params["click_conditions"])
    single_search_google_shopping(webdriver, term, browser_params, manager_params,
                                  number_of_links_to_click=number_of_links_to_click,
                                  training=training)


def browser_website_by_index(index_of_url, sleep, visit_id, webdriver, proxy_queue,
                             browser_params, manager_params,extension_socket):
    logger = loggingclient(*manager_params['logger_address'])
    sites = []
    with open(browser_params["training_sites"]) as train:
        for line in train:
            if not line.startswith("http://"):
                line = "http://"+line
            sites.append(line)
    if index_of_url >= len(sites):
        logger.info("BROWSER {}: {} is invalid".format(browser_params["crawl_id"],
                                                       index_of_url))
        return
    url = sites[index_of_url]
    #logger.info("msg")
    logger.info("BROWSER {}: BROWSE_TRAINING_SITE_BY_INDEX: {}.".format(browser_params['crawl_id'],
                                                               url))
    get_website(url, sleep, visit_id, webdriver, proxy_queue, browser_params, extension_socket)
