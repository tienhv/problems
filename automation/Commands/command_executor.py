import browser_commands
import profile_commands


def execute_command(command, webdriver, proxy_queue, browser_settings, browser_params, manager_params, extension_socket):
    """
    executes BrowserManager commands by passing command tuples into necessary helper function
    commands are of form (COMMAND, ARG0, ARG1, ...)
    the only imports in this file should be imports to helper libraries
    """
    if command[0] == 'GET':
        browser_commands.get_website(url=command[1], sleep=command[2], visit_id=command[3],
                                     webdriver=webdriver, proxy_queue=proxy_queue,
                                     browser_params=browser_params, extension_socket=extension_socket)

    if command[0] == 'BROWSE':
        browser_commands.browse_website(url=command[1], num_links=command[2], sleep=command[3],
                                        visit_id=command[4], webdriver=webdriver,
                                        proxy_queue=proxy_queue, browser_params=browser_params,
                                        manager_params=manager_params, extension_socket=extension_socket)

    if command[0] == 'DUMP_FLASH_COOKIES':
        browser_commands.dump_flash_cookies(start_time=command[1], visit_id=command[2],
                                            webdriver=webdriver, browser_params=browser_params,
                                            manager_params=manager_params)

    if command[0] == 'DUMP_PROFILE_COOKIES':
        browser_commands.dump_profile_cookies(start_time=command[1], visit_id=command[2],
                                              webdriver=webdriver, browser_params=browser_params,
                                              manager_params=manager_params)

    if command[0] == 'DUMP_PROF':
        return
        profile_commands.dump_profile(browser_profile_folder=browser_params['profile_path'],
                                      manager_params=manager_params,
                                      browser_params=browser_params,
                                      tar_location=command[1], close_webdriver=command[2],
                                      webdriver=webdriver, browser_settings=browser_settings,
                                      compress=command[3],
                                      save_flash=browser_params['disable_flash'] is False)


    if command[0] == 'EXTRACT_LINKS':
        browser_commands.extract_links(webdriver, browser_params, manager_params)
        #======
        browser_commands.extract_links_with_extension(webdriver, browser_params, manager_params)
    if command[0] == 'LOGIN':
        #browser_commands.extract_links(webdriver, browser_params, manager_params)
        browser_commands.login_google(webdriver, browser_params, manager_params)

    if command[0] == 'LOAD_PROFILE':
        # Do not use this command! There is built-in function that
        # can be activated by browser_params.json
        profile_commands.load_profile(browser_profile_folder=browser_params['profile_path'],
                                      manager_params=manager_params,
                                      browser_params=browser_params)
    #if command[0] == 'SEARCH_GOOGLE_SHOP':
    #    browser_commands.search_google_shopping(webdriver=webdriver,
    #                                            browser_params=browser_params,
    #                                            manager_params=manager_params,
    #                                            number_of_links_to_click=3,
    #                                            training=True)
    if command[0] == 'SINGLE_SEARCH_GOOGLE_SHOP':
        browser_commands.single_search_google_shopping(webdriver=webdriver,
                                                term = command[1],
                                                browser_params=browser_params,
                                                manager_params=manager_params,
                                                number_of_links_to_click=command[2],
                                                training=command[3])
    if command[0] == 'SINGLE_SEARCH_GOOGLE_SHOP_BY_INDEX':
        browser_commands.single_search_google_shopping_by_index(webdriver=webdriver,
                                                index_of_term = command[1],
                                                browser_params=browser_params,
                                                manager_params=manager_params,
                                                training=command[2])
    # usage:

    if command[0] == 'MULTIPLE_SEARCH_GOOGLE_SHOP':
        browser_commands.multiple_search_google_shopping(webdriver=webdriver,
                                                browser_params=browser_params,
                                                manager_params=manager_params,
                                                number_of_links_to_click=command[1],
                                                training=command[2])

    if command[0] == 'BROWSE_TRAINING_SITE_BY_INDEX':
        browser_commands.browser_website_by_index(index_of_url=command[1], sleep=command[2], visit_id=command[3],
                                     webdriver=webdriver, proxy_queue=proxy_queue,
                                     browser_params=browser_params,manager_params=manager_params, extension_socket=extension_socket)
