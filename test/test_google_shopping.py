import pytest
import time
import os
import utilities
import sys
import json
sys.path.append("..")
from automation import CommandSequence
from automation import TaskManager


url_a = utilities.BASE_TEST_URL + '/simple_a.html'
url_b = utilities.BASE_TEST_URL + '/simple_b.html'
url_c = utilities.BASE_TEST_URL + '/simple_c.html'

class TestSimpleCommands():
    """Test if searching on Google Shopping is correct
    """
    NUM_BROWSERS = 1

    def load_params(self, num_browsers=1):
        """
        Loads num_browsers copies of the default browser_params dictionary.
        Also loads a single copy of the default TaskManager params dictionary.
        """
        fp = open(os.path.join(os.path.dirname(__file__), '../automation/browser_params.json'))
        preferences = json.load(fp)
        fp.close()

        browser_params = [preferences[str(i)] for i in range(1, len(preferences)+1)]

        fp = open(os.path.join(os.path.dirname(__file__), '../automation/default_manager_params.json'))
        manager_params = json.load(fp)
        fp.close()
        manager_params['num_browsers'] = len(preferences)

        return manager_params, browser_params

    def get_config(self, data_dir):
        #manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        manager_params, browser_params = self.load_params()

        #for browser in browser_params:
        #    browser['headless'] = True
        manager_params['data_directory'] = data_dir
        manager_params['log_directory'] = data_dir
        manager_params['db'] = os.path.join(manager_params['data_directory'],
                                            manager_params['database_name'])
        return manager_params, browser_params

    def test(self,tmpdir):
        # Run the test crawl
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        # Set up two sequential get commands to two URLS
        cs = CommandSequence.CommandSequence("http://www.google.com")
        cs.get(sleep=3)
        #cs.get()
        #cs.login_google()
        #cs.search_google_shopping()
        #cs.single_search_google_shopping("food",training=False)
        #time.sleep(2)
        #cs.single_search_google_shopping("baby powder", number of link, trainig...)
        cs.multiple_search_google_shopping(-1, training=False,sleep_time=2)
        manager.execute_command_sequence(cs, index="**")
        #manager.get("http://www.google.com")
        time.sleep(15)
        manager.close(post_process=False)
        print("finish....")
    def run_search_google_training_by_multiple_commands(self,tmpdir):
        """visit all the training site. each visit is a single command
        """
        # get the size of training sites, and visit one by one using index in their list;
        # this is to avoid the problem of there is error when visit one site could stop whole
        # visiting process (in case of using single CommandSequence);
        # all the browser must have the same number of visting site
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        #manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        with open(browser_params[0]['training_keywords']) as _f:
            _sites = [site for site in _f]
        nu_sites = len(_sites)
        cs = CommandSequence.CommandSequence("http://www.example.com")
        #cs2 = CommandSequence.CommandSequence("none") # url is a place holder
        #cs.get(sleep=3)
        #cs2.login_google()
        #manager.execute_command_sequence(cs2, index="**")

        for i in range(0, nu_sites):
            cs.single_search_google_shopping_by_index(i,-1,training=True)
        manager.execute_command_sequence(cs, index="**")
        #manager.get("http://www.google.com")
        time.sleep(5)
        manager.close()
        print("finish....")

    def browser_training_site(self, tmpdir):
        manager_params, browser_params = self.get_config(str(tmpdir))
        manager = TaskManager.TaskManager(manager_params, browser_params)

        #manager_params, browser_params = TaskManager.load_default_params(self.NUM_BROWSERS)
        with open(browser_params[0]['training_sites']) as _f:
            _sites = [site for site in _f]
        nu_sites = len(_sites)
        cs = CommandSequence.CommandSequence("http://www.example.com")
        #cs.get()
        for i in range(len(_sites)):
            cs.browse_site_by_index(i, 3)
        manager.execute_command_sequence(cs, index="**")
        #manager.get("http://www.google.com")
        time.sleep(10)
        manager.close()

#browser_params["id"] must be initalized, this is mandantory
comm = TestSimpleCommands()
#comm.test("../automation")
#comm.run_search_google_training_by_multiple_commands("../automation")
comm.browser_training_site("../automation")
