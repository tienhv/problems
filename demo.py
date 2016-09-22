from automation import TaskManager, CommandSequence
import os
import json
# The list of sites that we wish to crawl
NUM_BROWSERS = 1
sites = [#'http://www.example.com',
         #'http://www.princeton.edu',
         "http://ipinfo.info/index.php",
         "http://soi.today",

         #'http://citp.princeton.edu/',
         "https://google.com"]

# Loads the manager preference
def load_params(num_browsers=1):
    """
    Loads num_browsers copies of the default browser_params dictionary.
    Also loads a single copy of the default TaskManager params dictionary.
    """
    #fp = open(os.path.join(os.path.dirname(__file__), 'automation/browser_params.json'))
    fp = open(os.path.join(os.path.dirname(__file__), 'debug.json'))
    preferences = json.load(fp)
    fp.close()

    browser_params = [preferences[str(i)] for i in range(1, len(preferences)+1)]

    fp = open(os.path.join(os.path.dirname(__file__), 'automation/default_manager_params.json'))
    manager_params = json.load(fp)
    fp.close()
    manager_params['num_browsers'] = len(preferences)

    return manager_params, browser_params

#manager_params, browser_params = TaskManager.load_default_params(NUM_BROWSERS)
manager_params, browser_params = load_params()

pass

# Update browser configuration (use this for per-browser settings)
for i in xrange(NUM_BROWSERS):
    browser_params[i]['disable_flash'] = False #Enable flash for all three browsers
browser_params[0]['headless'] = False #Launch only browser 0 headless

# Update TaskManager configuration (use this for crawl-wide settings)
manager_params['data_directory'] = '~/Desktop/wpm'
manager_params['log_directory'] = '~/Desktop/wpm'

# Instantiates the measurement platform
# Commands time out by default after 60 seconds
manager = TaskManager.TaskManager(manager_params, browser_params)

# Visits the sites with all browsers simultaneously
for site in sites:
    command_sequence = CommandSequence.CommandSequence(site)

    command_sequence.get(sleep=3, timeout=60)
    manager.execute_command_sequence(command_sequence, index='**') # ** = synchronized browsers
    import time
    time.sleep(3)
time.sleep(30)
# Shuts down the browsers and waits for the data to finish logging
manager.close()
