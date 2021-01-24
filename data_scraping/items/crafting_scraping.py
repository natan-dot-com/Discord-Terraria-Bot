import os,sys,inspect
current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(parent_dir)
sys.path.insert(0, parent_dir) 
from json_manager import *
from item_hash import *
from bs4 import BeautifulSoup
import requests
import json
import re

CRAFTINGS_PATH = 'json_new/craftings.json'
CRAFTING_TABLE_SIZE = 64
ITEM_TABLE_SIZE = 8192
STRING_DICT_KEY = 'name'
RETURN_DICT_KEY = 'id'

itemList = LoadJSONFile('json_new/items.json')
craftingTableList = LoadJSONFile('json_new/tables.json')

itemHash = hashTable(ITEM_TABLE_SIZE, STRING_DICT_KEY)
for itemInstance in itemList:
    itemHash.hashString(itemInstance[STRING_DICT_KEY], itemInstance)

craftingTableHash = hashTable(CRAFTING_TABLE_SIZE, STRING_DICT_KEY)
for tableInstance in craftingTableList:
    craftingTableHash.hashString(tableInstance[STRING_DICT_KEY], tableInstance)

def getCraftingRecipes(firstItemID, lastItemID):
    craftRecipeList = []
    for item in itemList[firstItemID:lastItemID:]:
        print("Finding " + item['name'])
        URL = "https://terraria.gamepedia.com/" + item['name'].replace(" ", "_")
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, 'html.parser')
        craftingTable = soup.find("div", class_="crafts")
            
        if craftingTable and re.search("Recipes*", str(soup.find("h3").find("span", class_="mw-headline"))):
            rows = craftingTable.findAll("tr")
            for row in rows[1::]:
                craftDict = {
                    "craft_id": "",
                    "craft_result": "",
                    "craft_qty": "",
                    "table": [],
                    "recipe": []
                }
                
                # Finding data about what item it's being crafted
                if row.find("td", class_="result"):
                    # What item is being crafted
                    result_code = row.find("td", class_="result")
                    if result_code:
                        result = result_code.img['alt']
                        
                    # The quantity that's being crafted
                    craft_qty = result_code.find("span", class_="note-text")
                    if not craft_qty:
                        qty = '1'
                    else:
                        qty = ' '.join(re.findall("\((\d+)\)", craft_qty.text))
                # If nothing about it is defined on table line, will use the result obtained previously
                itemID = itemHash.dehashString(result, RETURN_DICT_KEY)
                if itemID != NOT_FOUND:
                    craftDict["craft_result"] = itemID
                    
                craftDict["craft_qty"] = qty
                
                # Finding all ingredients with its respective quantities relative to the recipe
                if row.find("td", class_="ingredients"):
                    ingredientsList = row.find("td", class_="ingredients").findAll("li")
                    for ingredientInstance in ingredientsList:
                        ingredientsDict = {
                            "ingredient": "",
                            "ingredient_qty": ""
                        }
                        
                        ingredientName = ingredientInstance.img['alt']
                        if ingredientName:
                            ingredientID = itemHash.dehashString(ingredientName, RETURN_DICT_KEY)
                            if ingredientID != NOT_FOUND:
                                ingredientsDict["ingredient"] = ingredientID
                                
                        ingredientQty = ingredientInstance.find("span", class_="note-text")
                        if ingredientQty:
                            ingredientsDict["ingredient_qty"] = ' '.join(re.findall("\((\d+)\)", ingredientQty.text))
                        else:
                            ingredientsDict["ingredient_qty"] = '1'
                            
                        craftDict["recipe"].append(ingredientsDict)
                        
                # Finding all the crating stations in which the recipe can be made
                if row.find("td", class_="station"):
                    stationList = row.find("td", class_="station").findAll("span", class_="i")
                    if not stationList:
                        stationList = ["By Hand"]
                # If nothing about it is defined on table line, will use the result obtained previously
                for stationInstance in stationList:
                    if not stationInstance == "By Hand":
                        craftingTable = stationInstance.span.span.a.text
                    else:
                        craftingTable = stationInstance
                        
                    if craftingTable:
                        tableID = craftingTableHash.dehashString(craftingTable, RETURN_DICT_KEY)
                        if tableID != NOT_FOUND:
                            craftDict["table"].append(tableID)
                        
                craftRecipeList.append(craftDict)
                #print(json.dumps(craftDict, indent=4))
        else:
            print(item["name"] + " recipe not found")
    return craftRecipeList

#testList = getCraftingRecipes(1, 10)
SaveJSONFile(CRAFTINGS_PATH, craftsList)
