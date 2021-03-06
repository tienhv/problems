from Errors import CommandExecutionError

class CommandSequence:
    """A CommandSequence wraps a series of commands to be performed
    on a visit to one top-level site into one logical
    "site visit," keyed by a visit id. An example of a CommandSequence
    that visits a page and dumps cookies modified on that visit would be:

    sequence = CommandSequence(url)
    sequence.get()
    sequence.dump_profile_cookies()
    task_manager.execute_command_sequence(sequence)

    CommandSequence guarantees that a series of commands will be performed
    by a single browser instance.
    """

    def __init__(self, url, reset=False):
        """Nothing to do here"""
        self.url = url
        self.reset = reset
        self.commands_with_timeout = []
        self.total_timeout = 0
        self.contains_get_or_browse = False

    def get(self, sleep=0, timeout=60):
        """ goes to a url """
        self.total_timeout += timeout
        command = ('GET', self.url, sleep)
        self.commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True

    def browse(self, num_links = 2, sleep=0, timeout=60):
        """ browse a website and visit <num_links> links on the page """
        self.total_timeout += timeout
        command = ('BROWSE', self.url, num_links, sleep)
        self.commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True

    def dump_flash_cookies(self, timeout=60):
        """ dumps the local storage vectors (flash, localStorage, cookies) to db """
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the dump storage vectors command", self)
        command = ('DUMP_FLASH_COOKIES',)
        self.commands_with_timeout.append((command, timeout))

    def dump_profile_cookies(self, timeout=60):
        """ dumps from the profile path to a given file (absolute path) """
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the dump storage vectors command", self)
        command = ('DUMP_PROFILE_COOKIES',)
        self.commands_with_timeout.append((command, timeout))

    def dump_profile(self, dump_folder, close_webdriver=False, compress=True, timeout=120):
        """ dumps from the profile path to a given file (absolute path) """
        self.total_timeout += timeout
        command = ('DUMP_PROF', dump_folder, close_webdriver, compress)
        self.commands_with_timeout.append((command, timeout))

    def extract_links(self, timeout=30):
        """Extracts links found on web page and dumps them externally"""
        self.total_timeout += timeout
        if not self.contains_get_or_browse:
            raise CommandExecutionError("No get or browse request preceding "
                                        "the dump storage vectors command", self)
        command = ('EXTRACT_LINKS',)
        self.commands_with_timeout.append((command, timeout))

    def login_google(self, timeout=30):
        """Login Google with id and pass in configuration browser_params"""
        self.total_timeout += timeout
        #if not self.contains_get_or_browse:
        #    raise CommandExecutionError("No get or browse request preceding "
        #                                "the dump storage vectors command", self)
        command = ('LOGIN',)
        self.commands_with_timeout.append((command, timeout))


    def load_profile(self, close_webdriver=False, compress=True, timeout=120):
        """load from the profile path to a given file (absolute path)"""
        self.total_timeout += timeout
        command = ('LOAD_PROFILE')
        self.commands_with_timeout.append((command, timeout))

    def search_google_shopping(self, timeout=300):
        """Search one term on google shopping"""
        self.total_timeout += timeout
        #if not self.contains_get_or_browse:
        #    raise CommandExecutionError("No get or browse request preceding "
        #                                "the dump storage vectors command", self)
        command = ('SEARCH_GOOGLE_SHOP',)
        self.commands_with_timeout.append((command, timeout))

    def single_search_google_shopping(self, term, training, timeout=300):
        self.total_timeout += timeout
        #if not self.contains_get_or_browse:
        #    raise CommandExecutionError("No get or browse request preceding "
        #                                "the dump storage vectors command", self)
        command = ('SINGLE_SEARCH_GOOGLE_SHOP',term, training)
        self.commands_with_timeout.append((command, timeout))

    def single_search_google_shopping_by_index(self, index, training, timeout=300):
        self.total_timeout += timeout
        #if not self.contains_get_or_browse:
        #    raise CommandExecutionError("No get or browse request preceding "
        #                                "the dump storage vectors command", self)
        command = ('SINGLE_SEARCH_GOOGLE_SHOP_BY_INDEX', index, training)
        self.commands_with_timeout.append((command, timeout))


    def multiple_search_google_shopping(self, number_of_links_to_click, training, sleep_time=20, timeout=36000):
        self.total_timeout += timeout
        #if not self.contains_get_or_browse:
        #    raise CommandExecutionError("No get or browse request preceding "
        #                                "the dump storage vectors command", self)
        command = ('MULTIPLE_SEARCH_GOOGLE_SHOP',number_of_links_to_click, training, sleep_time)
        self.commands_with_timeout.append((command, timeout))

    def browse_site_by_index(self, index, sleep=0, timeout=60):
        """ goes to a url """
        self.total_timeout += timeout
        command = ('BROWSE_TRAINING_SITE_BY_INDEX', index, sleep)
        self.commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True

    def dummy(self, sleep=0, timeout=60):
        """ this is for testing purpose, do not use """
        self.total_timeout += timeout
        command = ('DUMMY', self.url, sleep)
        self.commands_with_timeout.append((command, timeout))
        self.contains_get_or_browse = True
