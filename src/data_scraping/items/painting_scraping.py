# Load 3-level parent directories
from importlib import import_module
import path_manager
if __name__ == '__main__' and __package__ == None:
    __package__ = path_manager.importParents(level=3)
    import_module(__package__)

# Setting the root directory as working directory for Linux systems
from platform import system
from pathlib import Path
import os
systemOS = system()
if systemOS == "Linux":
    os.chdir("../../../")

from ...package.scraping_tools import *
from ...package.json_manager import *
from bs4 import BeautifulSoup
import re
import requests

scrappingData = ["Painting", "Name", "Placed", "Tooltip", "Description"]
IMAGE_EXTENSION = ".png"
PAINTINGS_ICONS_DIRECTORY = "paintings_icons/"
PAINTINGS_DIRECTORY = "paintings/"
PAINTING_JSON_PATH = GLOBAL_JSON_PATH + PAINTING_NAME_FILE + JSON_EXT
dictList = []

itemList = LoadJSONFile(GLOBAL_JSON_PATH + PAINTING_NAME_FILE + JSON_EXT)

URL = "https://terraria.gamepedia.com/Paintings"
html = requests.get(URL)
soup = BeautifulSoup(html.content, 'html.parser')
tables = soup.findAll("table", class_="terraria")
for table in tables:
    rows = table.findAll("tr")
    index = getTableColumns(rows[0].findAll("th"), scrappingData)
    for row in rows[1::]:
        cols = row.findAll("td")
        paintingDict = {
            SCRAPING_ITEM_ID: "",
            IMAGE_PLACED: "",
            SCRAPING_TOOLTIP: "",
            SCRAPING_DESCRIPTION: "",
            SCRAPING_SOURCE: SOURCE_SOURCES_DICT
        }
        if index["Name"] != NOT_FOUND:
            paintingDict[SCRAPING_ITEM_ID] = re.search("\d+", cols[index["Name"]].find("div", class_="id").text).group()
            print("Getting information from ID " + paintingDict[SCRAPING_ITEM_ID])
            
        if index["Painting"] != NOT_FOUND:
            imagePath = PAINTINGS_ICONS_DIRECTORY + cols[index["Painting"]].img['alt'].replace(" ", "_") + IMAGE_EXTENSION
            writeImage(cols[index["Painting"]].img['src'], GLOBAL_JSON_PATH + imagePath)
            
        if index["Placed"] != NOT_FOUND:
            imagePath = PAINTINGS_DIRECTORY + cols[index["Painting"]].img['alt'].replace(" ", "_") + "_Placed" + IMAGE_EXTENSION
            writeImage(cols[index["Placed"]].img['src'], GLOBAL_JSON_PATH + imagePath)
            paintingDict[IMAGE_PLACED] = imagePath
            
        if index["Tooltip"] != NOT_FOUND:
            paintingDict[SCRAPING_TOOLTIP] = cols[index["Tooltip"]].text.replace("\n", "")
            
        if index["Description"] != NOT_FOUND:
            paintingDict[SCRAPING_DESCRIPTION] = cols[index["Description"]].text.replace("\n", "").replace("\"", "")
           
        removeEmptyFields(paintingDict)
        dictList.append(paintingDict)
SaveJSONFile(PAINTING_JSON_PATH, sorted(dictList, key = lambda i: int(i[SCRAPING_ITEM_ID])))
