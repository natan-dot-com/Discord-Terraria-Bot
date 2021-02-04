#

import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir) 
from scraping_tools import *
from json_manager import *
from bs4 import BeautifulSoup
import requests
import threading
import math
from multithreading_starter import *

ITEMS_FURNITURE_PATH = GLOBAL_JSON_PATH + "items_furnitures.json"
URL = "https://terraria.gamepedia.com/"
BRICKS_IMAGE_PATH = "data_scraping/bricks_img/{}.png"

log = open("log.txt", "w")
itemList = LoadJSONFile(ITEM_FILE_PATH)
furnituresList = []

def furniturescraping(init, fin):
    for itemInstance in itemList[init:fin]:
        if itemInstance[SCRAPING_TYPE] == "Furniture":
            newURL = URL + itemInstance[SCRAPING_NAME].replace(" ", "_")
            page = requests.get(newURL)
            soup = BeautifulSoup(page.content, "html.parser")
            print("processing {}".format(newURL))

            tableBoxes = soup.find_all("div", class_="infobox item")
            tableBox = tableBoxes[0]
            for tableBoxTmp in tableBoxes:
                if tableBoxTmp.find("div", class_="title").text == itemInstance[SCRAPING_NAME]:
                    tableBox = tableBoxTmp
            furnituresList.append(get_statistics(tableBox, itemInstance=itemInstance))


start_threads(__file__, furniturescraping.__name__, len(itemList), 8)
SaveJSONFile(ITEMS_FURNITURE_PATH, sortListOfDictsByKey(furnituresList, SCRAPING_ITEM_ID))
exit(0)