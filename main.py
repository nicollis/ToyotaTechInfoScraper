#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import base64

from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def scrape_repair_manuals():
    # Set up Selenium WebDriver
    driver_loc = ChromeDriverManager().install()
    service = Service(driver_loc)
    options = webdriver.ChromeOptions()

    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options, service=service)
    driver.print_page()

    # Login URL
    root_url = "https://techinfo.toyota.com"
    login_url = f"{root_url}/techInfoPortal/appmanager/t3/ti?_nfpb=true&_pageLabel=ti_home_page&goto=https%3A%2F%2Ftechinfo.toyota.com%3A443%2Fagent%2Fcustom-login-response%3Fstate%3DDXn0JOw9_lSKhNw8Dqzw8CKB1pU&original_request_url=https%3A%2F%2Ftechinfo.toyota.com%3A443%2F"

    # Navigate to the login page
    driver.get(login_url)

    # You might need to inspect the page to find the correct ids or name attributes
    username_field = driver.find_element(by=By.NAME, value="username")
    password_field = driver.find_element(by=By.NAME, value="password")
    login_button = driver.find_element(by=By.ID, value="externalloginsubmit")

    # Enter your credentials
    username_field.send_keys("USERNAME") # TODO: Replace with your username
    password_field.send_keys("PASSWORD") # TODO: Replace with your password

    # Submit the form
    login_button.click()  # This works if the form is a traditional HTML form

    # It might be needed to use explicit wait here
    time.sleep(10)

    # URL to scrape after login
    directory_url = "" # TODO: Replace with the URL for the directory you want to scrape (see README.md)
    tree_url = f"{root_url}/t3Portal/resources/jsp/siviewer"
    driver.get(directory_url)

    time.sleep(5)

    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')

    section_links = [(a['title'], a['href'][2:]) for a in soup.find_all('a', href=True) if './nav.jsp' in a['href']]

    process_section(driver, root_url, 'General')

    for title, link in section_links:
        driver.get('/'.join([tree_url, link]))
        time.sleep(5)
        process_section(driver, root_url, title)


    driver.quit()

def process_section(driver, root_url, section_title):
    # Toggles all nodes in the tree
    driver.execute_script("""
            let allIds = [];
            let openedIds = [];

            function dfs(node) {
                // Add all ids to the allIds array
                allIds.push(node.n_id);

                // Check if the b_opened is true, then add the id to openedIds
                if(node.b_opened === true) {
                    openedIds.push(node.n_id);
                }

                // If there are children, then traverse them
                if(node.a_children && node.a_children.length > 0) {
                    for(let i = 0; i < node.a_children.length; i++) {
                        dfs(node.a_children[i]);
                    }
                }
            }

            // Call the function with the root node
            dfs(trees[0]);

            // Goes through all ids and opens the ones not already opened
            allIds.forEach(id => {
                // If the id is not in openedIds, then toggle it
                if (!openedIds.includes(id)) {
                    trees[0].toggle(id);
                }
            });
            """)

    time.sleep(1)

    # Get the page source after JavaScript has been executed
    html = driver.page_source

    soup = BeautifulSoup(html, 'html.parser')

    # Extract all href links
    # links = [a['href'] for a in soup.find_all('a', href=True) if a.text]
    links = [a['href'] for a in soup.find_all('a', href=True) if '/t3Portal/' in a['href']]

    # Loop through each link and save the page as a PDF
    for link in links:
        # Some links might be relative, so we need to ensure they're absolute
        if not link.startswith('http'):
            link = root_url + link

        # We'll use the link as the file name, replacing any characters that could cause problems
        filename = link.replace('https://', '').replace('http://', '').replace('/', '_') + '.pdf'
        driver.get(link)

        title = driver.title

        # Sanitize the title so it's safe to use as a filename
        directory, safe_title = create_filepath(title, section_title)

        pdf_data = driver.execute_cdp_cmd('Page.printToPDF', {"printBackground": True})

        # Check if the directory exists, and if not, create it
        if not os.path.exists(directory):
            os.makedirs(directory)

        if not os.path.isfile(filename):
            with open(f'{directory}/{safe_title}', "wb") as f:
                f.write(base64.b64decode(pdf_data['data']))


def create_filepath(title, section_title):
    root_directory = "./data/Collision Repair"
    title = ''.join(title.split(';')[0])
    parts = title.split(":")

    # List to hold the cleaned parts
    cleaned_parts = []

    for part in parts:
        # Remove non-alphabetic characters and extra whitespace
        cleaned = re.sub('[^a-zA-Z ]', '', part).strip()

        # Title case the cleaned part and add it to the cleaned_parts list
        cleaned_parts.append(cleaned.title())

    # Join the cleaned and title-cased parts with '/' and print the result
    cleaned_path = '/'.join([root_directory, section_title] + cleaned_parts)

    # Separate the directory and filename
    directory, filename = os.path.split(cleaned_path)

    # Add '.pdf' to the filename
    filename += '.pdf'

    return directory, filename




# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    scrape_repair_manuals()
