import os
import time
import traceback
from datetime import datetime

import pyautogui
from PIL import Image
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

IMAGE_CATEGORY: str = 'keyboard'
OLX_CATEGORY_SOURCE: str = 'https://www.olx.pl/d/elektronika/komputery/akcesoria-komputerowe/klawiatury/'
PAUSE_TIME: int = 2
IMAGES_LOCATION = os.environ.get('HOME') + '/Downloads/'

driver = webdriver.Chrome(service=Service('./chromedriver'))
driver.get(OLX_CATEGORY_SOURCE)
logger.info(driver.title)

# ACCEPT COOKIES
WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'onetrust-accept-btn-handler'))).click()
driver.maximize_window()

number_of_pages = driver.find_elements(
    By.XPATH, '//li[@data-testid="pagination-list-item"]/a'
)[-1].get_attribute('innerHTML')
item_links = []
for page in range(1, int(number_of_pages) + 1):
    driver.get(f'{OLX_CATEGORY_SOURCE}?page={page}')
    driver.implicitly_wait(PAUSE_TIME)  # wait for page to load
    try:
        all_items = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@class='css-19ucd76']/a"))
        )
        item_links.extend([item.get_attribute('href') for item in all_items])
    except Exception as e:
        logger.error(f'Error occurred while processing page {page}: {e}')
        traceback.print_exc()
        continue

unique_items = set(item_links)
logger.info(f'Number of items: {len(item_links)}, unique items: {len(unique_items)}')
logger.info(f'Unique items source: \n {unique_items}')

number_of_images = 0
for item in unique_items:
    try:
        driver.get(item)
        driver.implicitly_wait(PAUSE_TIME)

        # Find all images for the item
        h1 = driver.find_element(By.TAG_NAME, 'h1').get_attribute('innerHTML')

        images = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, f'//*[@alt="{h1}"]'))
        )
        img_sources = [img.get_attribute('src') if img.get_attribute('src')
                       else img.get_attribute('data-src') for img in images]
        logger.info(f'Number of images found for "{h1}": {len(img_sources)}')
        number_of_images += len(img_sources)

        # Save all images
        for src in img_sources:
            driver.get(src)
            time.sleep(PAUSE_TIME)
            window_size = pyautogui.size()
            pyautogui.click(x=window_size.width / 2, y=window_size.height / 2)
            pyautogui.hotkey('command', 's')
            time.sleep(PAUSE_TIME)
            file_name = f'{IMAGE_CATEGORY}_{datetime.now().strftime("%y-%m-%d-%H%M%S%f")}'
            pyautogui.write(file_name)
            time.sleep(PAUSE_TIME)
            pyautogui.press('enter')
            time.sleep(PAUSE_TIME)

            # Convert webp to png
            file_location = IMAGES_LOCATION + file_name
            wait = 0
            while True:
                try:
                    im = Image.open(f'{file_location}.webp').convert('RGB')
                    im.save(f'{file_location}.jpg', 'jpeg')
                    os.remove(f'{file_location}.webp')
                except FileNotFoundError:
                    wait += 1
                    if wait > 2:
                        logger.error(f'Fail to save image: {src}')
                        break
                    time.sleep(PAUSE_TIME)  # In case if image downloading takes more time
                else:
                    break

    except Exception as e:
        logger.error(f'Error occurred while downloading item: {item}. {e}')
        traceback.print_exc()
        continue

logger.info(f'Image scrapping finished successfully. Images expected: {number_of_images}.')
driver.close()
