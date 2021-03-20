from os import chdir
import os
from platform import system
if system() == "Linux":
    chdir("../")

import discord
import re
from discord.ext import commands
from package.json_manager import *
from package.item_hash import *
from package.bot_config import *
from package.search import *
from package.utility_dictionaries import *
from package.utility_functions import *
from package.embed_functions import *
from package.permissions import *
from package.string_similarity import getSimilarStrings

bot = commands.Bot(command_prefix=botPrefix, description=botDescription, help_command=None)
itemList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + MAIN_NAME_FILE + JSON_EXT)
tableList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + TABLE_NAME_FILE + JSON_EXT)
rarityList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + RARITY_NAME_FILE + JSON_EXT)
recipesList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + RECIPE_NAME_FILE + JSON_EXT)
tablesList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + TABLE_NAME_FILE + JSON_EXT)
setList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + SET_NAME_FILE + JSON_EXT)
itemHash = loadDependencies(itemList)
setHash = loadDependencies(setList, SET_HASH_SIZE, LABEL_SET_NAME)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await bot.change_presence(activity=discord.Game(name=botPrefix + "help"))

@bot.command()
async def help(ctx):
    
    if ctx.author == bot.user:
        return

    embed = discord.Embed(color=helpColor, title="Command List")
    embed.set_thumbnail(url=helpThumbNail)
    for command, commandDescription in zip(commandList.keys(), commandList.values()):
        embedInsertField(embed, commandDescription, command, inline=False)  
    await ctx.send(embed=embed)

@bot.command()
async def item(ctx, *args):

    # Checks empty argument
    arg = " ".join(args)
    if ctx.author == bot.user or not arg:
        return ARG_NOT_FOUND
    
    # Hash search the current item
    print("User {} has requested a craft recipe for {}.".format(str(ctx.author), arg))
    itemID = itemHash.search(arg, LABEL_ID)
    if itemID == NOT_FOUND:
        titleMessage = "Couldn't find item '" + arg + "' in the data base."
        errorEmbed = discord.Embed(title=titleMessage, color=0xFFFFFF)

        notFoundTitle =  "Didn't you mean...?"
        notFoundMessage = ""
        similarStrings = getSimilarStrings(arg, itemList)
        if similarStrings:
            for string in similarStrings:
                notFoundMessage += string + "\n" 
        else:
            notFoundMessage = "Couldn't retrieve any suggestions from data base."
        errorEmbed.add_field(name=notFoundTitle, value=notFoundMessage)
        await ctx.send(embed = errorEmbed)

        return ITEM_NOT_FOUND

    # Gets respective item info dictionary
    itemType = itemList[int(itemID)-1][LABEL_TYPE]
    itemFilePath = GLOBAL_JSON_PATH + DIR_ITEMS_DATA + itemFileManager[itemType] + JSON_EXT
    itemDict = binarySearch(LoadJSONFile(itemFilePath), itemID)
    if itemDict == NOT_FOUND:
        return ITEM_NOT_FOUND

    # Starts building each embed panel 
    embedList = []

    itemName = itemList[int(itemID)-1][LABEL_NAME]
    imageFilename = itemName.replace(" ", "_") + STATIC_IMAGE_EXT
    dominantImageColor = pickDominantColor(imageFilename)
    hasSource = False

    # Main info embed panel construction
    mainPage = discord.Embed(color=dominantImageColor, title="General informations about '" + itemName + "':")
    mainImage = discord.File(GLOBAL_IMAGE_PATH + imageFilename, filename="image.png")
    mainPage.set_thumbnail(url="attachment://image.png")

    exceptionLabels = [
        LABEL_ITEM_ID
    ]
    for itemCategory in itemDict.keys():
        if itemCategory in exceptionLabels:
            continue

        if itemCategory == LABEL_SOURCE:
            hasSource = True
            break

        elif itemCategory == LABEL_SET_ID:
            embedInsertField(mainPage, setList[int(itemDict[itemCategory])-1][LABEL_SET_NAME], LABEL_SET_NAME, inline=True)

        elif itemCategory == LABEL_RARITY:
            embedInsertRarityField(mainPage, itemDict[itemCategory], rarityList)

        else:
            embedInsertField(mainPage, itemDict[itemCategory], itemCategory, inline=True)

    embedList.append(mainPage)

    # If item has source dict (i.e. if embed will have more than one page)
    if hasSource:

        # LABEL_SOURCE dict analysis
        nonEmptyLists = []
        for sourceCategory in itemDict[LABEL_SOURCE]:
            if itemDict[LABEL_SOURCE][sourceCategory]:
                nonEmptyLists.append(sourceCategory)


        # Source embed panels creation
        recipesList = [] 
        npcList = []
        sellingList = []
        grabBagDropList = []
        bagList = []
        for existentCategory in nonEmptyLists:
            newEmbed = None

            # Recipes embed panel cration
            if existentCategory == SOURCE_RECIPES:
                if not recipesList:
                    recipesList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + RECIPE_NAME_FILE + JSON_EXT)
                titleMessage = "Showing craft recipes for '" + itemName + "':"
                newEmbed = discord.Embed(title=titleMessage, color=dominantImageColor)
                createRecipesPanel(itemList, tableList, recipesList, itemDict[LABEL_SOURCE][SOURCE_RECIPES], newEmbed)

            # NPC's selling offers embed panel creation
            elif existentCategory == SOURCE_NPC:
                if not npcList:
                    npcList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + NPC_NAME_FILE + JSON_EXT)
                if not sellingList:
                    sellingList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + SELLING_LIST_NAME_FILE + JSON_EXT)
                titleMessage = "Showing selling offers for '" + itemName + "':"
                newEmbed = discord.Embed(title=titleMessage, color=dominantImageColor)
                createSellingPanel(npcList, sellingList, itemDict[LABEL_SOURCE][SOURCE_NPC], newEmbed, itemName)

            elif existentCategory == SOURCE_DROP:
                continue

            # Grab bags' drops embed panel creation
            elif existentCategory == SOURCE_GRAB_BAG:
                if not grabBagDropList:
                    grabBagDropList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + BAGS_DROP_NAME_FILE + JSON_EXT)
                if not npcList:
                    npcList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + NPC_NAME_FILE + JSON_EXT)
                if not bagList:
                    bagList = LoadJSONFile(GLOBAL_JSON_PATH + DIR_ID_REFERENCES + BAGS_NAME_FILE + JSON_EXT)
                titleMessage = "Showing bag drops from '" + itemName + "':"
                newEmbed = discord.Embed(title=titleMessage, color=dominantImageColor)
                createBagDropPanel(npcList, bagList, grabBagDropList, itemDict[LABEL_SOURCE][SOURCE_GRAB_BAG], newEmbed, itemName)

            elif existentCategory == SOURCE_OTHER:
                fieldTitle = "General availability"
                embedInsertField(mainPage, itemDict[LABEL_SOURCE][SOURCE_OTHER], fieldTitle, inline=False)

            if newEmbed:
                newEmbed.set_thumbnail(url="attachment://image.png")
                newEmbed.set_footer(text="Page " + str(2+nonEmptyLists.index(existentCategory)) + "/" + str(1+len(nonEmptyLists)))
                embedList.append(newEmbed)

    if len(embedList) > 1:
        pageAlert = "React to this message to switch between pages!\n"
        mainPage.set_footer(text=pageAlert + "Page 1/" + str(1+len(nonEmptyLists)))

    currentEmbed = 0
    botMessage = await ctx.send(file=mainImage, embed=embedList[currentEmbed])

    # Page system manager (if number of pages greater than one)
    if len(embedList) > 1:
        await embedSetReactions(bot, botMessage, embedList)


# Shows a list of  every item which starts with 'arg'
@bot.command()
async def list(ctx, *args):

    arg = " ".join(args)
    if ctx.author == bot.user or not arg:
        return

    print("User {} has requested a craft recipe for {}.".format(str(ctx.author), arg))
    matchCounter = 0
    matchList = [[]]

    #Regex usage to find every match of the input
    for itemInstance in itemList:
        if re.search("^" + arg + "+", itemInstance[LABEL_NAME], re.IGNORECASE): 
            if len(matchList[len(matchList)-1]) >= pageSize:
                matchList.append([])
            matchList[len(matchList)-1].append(itemInstance[LABEL_NAME])
    
    for matchInstance in matchList:
        matchCounter += len(matchInstance)
    if matchCounter == 0:
        await ctx.send("No items were found containing " + arg)
        return NOT_FOUND

    listDescription = str(matchCounter) + " occurrencies found:\n"
    # Pages creation with 12 lines each
    pageList = []
    for matchInstance in matchList:
        listMessage = ""
        for subInstance in matchInstance:
            listMessage += subInstance + "\n"
            
        newPage = discord.Embed(title ="Search Info about " + arg, colour=discord.Colour.green())
        embedInsertField(newPage, listMessage, listDescription, inline=False)
        embedSetFooter(newPage, "Page " + str(matchList.index(matchInstance) + 1) + "/" + str(len(matchList)))
        pageList.append(newPage)

    #Send Message
    botMessage = await ctx.send(embed = pageList[0])

    # Changing page system via Discord reactions
    if len(pageList) > 1:
        await embedSetReactions(bot, botMessage, pageList)

# Shows crafting information
@bot.command()
async def craft(ctx, *args):

    arg = " ".join(args)
    if ctx.author == bot.user or not arg:
        return
    print("User {} has requested a craft recipe for {}.".format(str(ctx.author), arg))

    #Find input in hash table
    itemID = itemHash.search(arg, LABEL_ID)
    if itemID == -1:
        await ctx.send("Can't find item '{}' in data base.".format(arg))
        return ITEM_NOT_FOUND

    itemType = itemList[int(itemID)-1][LABEL_TYPE]
    itemFilePath = GLOBAL_JSON_PATH + DIR_ITEMS_DATA + itemFileManager[itemType] + JSON_EXT
    itemName = itemList[int(itemID)-1][LABEL_NAME]
    imageFilename = itemName.replace(" ", "_").lower() + STATIC_IMAGE_EXT
    dominantImageColor = pickDominantColor(imageFilename)
    craftTitle = "Craft information about '{}':".format(itemName)
    embedImage = discord.File(GLOBAL_IMAGE_PATH + imageFilename, filename="image.png")
    itemDict = binarySearch(LoadJSONFile(itemFilePath), itemID)

    embedPage = discord.Embed(color=dominantImageColor, title=craftTitle)
    embedPage.set_thumbnail(url="attachment://image.png")

    itemRecipes = itemDict[LABEL_SOURCE][SOURCE_RECIPES]
    for craftingRecipeIndex in range(len(itemRecipes)):
        ingredients = recipesList[int(itemRecipes[craftingRecipeIndex])-1][RECIPE_IDENTITY]
        resultQuantity = recipesList[int(itemRecipes[craftingRecipeIndex])-1][RECIPE_RESULT_QUANTITY]
        tableId = int(recipesList[int(itemRecipes[craftingRecipeIndex])-1][RECIPE_TABLE])
        tableName = tablesList[tableId-1][LABEL_NAME]
        outputDescription = "Made in {} using:".format(tableName)
        outputMessage = ""

        #Get ingredients infos
        for ingredientIndex in range(len(ingredients)):
            ingredientId = int(ingredients[ingredientIndex][INGREDIENT_NAME])
            ingredientQuantity = ingredients[ingredientIndex][INGREDIENT_QUANTITY]
            outputMessage += "{} ({})\n".format(itemList[ingredientId-1][LABEL_NAME], ingredientQuantity)
        outputMessage += "Producing {} units.".format(resultQuantity)
        embedInsertField(embedPage, outputMessage, outputDescription, inline=False)

    #Send Message
    await ctx.send(file=embedImage, embed=embedPage)

# Shows set information
@bot.command()
async def set(ctx, *args):

    arg = " ".join(args)
    if ctx.author == bot.user or not arg:
        return
    print("User {} has requested set information about {}.".format(str(ctx.author), arg))

    #Find input in hash table
    setID = setHash.search(arg, LABEL_ID)
    if setID == -1:
        await ctx.send("Can't find set '{}' in data base.".format(arg))
        return SET_NOT_FOUND

    setDict = setList[int(setID)-1]
    setName = setDict[LABEL_SET_NAME]
    setPieces = setDict[LABEL_SET_PIECES]
    #imageFileName = setName.replace(" ", "_").lower() + STATIC_IMAGE_EXT
    #dominantImageColor = pickDominantColor(imageFileName)
    setTitle = "General Information about '{}' set:".format(setName)

    #embedImage = discord.File(GLOBAL_IMAGE_PATH + imageFileName, filename="image.png")
    embedPage = discord.Embed(color=0x0a850e, title=setTitle) #will be updated with dominantImageColor
    embedPage.set_thumbnail(url="attachment://image.png")
    
    for setCategory in setDict.keys():
        if setCategory == LABEL_RARITY:
            embedInsertRarityField(embedPage, setDict[setCategory], rarityList, inline=False)
        elif setCategory == LABEL_SET_PIECES:
            setPiecesLabel = "Set pieces from '{}':".format(setName)
            setPiecesValue = ""
            for setPieceIndex in range(len(setPieces)):
                setPiecesValue += setDict[setCategory][setPieceIndex] + ","
            embedInsertField(embedPage, setPiecesValue[:-1].replace(",", "\n"), setPiecesLabel)
        elif setCategory == LABEL_ID or setCategory == LABEL_SET_NAME:
            continue
        else:
            embedInsertField(embedPage, setDict[setCategory].replace(" / ", "\n"), setCategory, inline=False)
    #Send Message
    #await ctx.send(file=embedImage, embed=embedPage)
    await ctx.send(embed=embedPage)

# This functions works when it wants.
# Useless now but i will maintain it for future code reference
# Add emojis to bot server
@bot.command()
async def add_emojis(ctx, *args):

    if ctx.author == bot.user or not str(ctx.author.id) in ADMIN_LIST:
        await ctx.send("Permission Denied.")
        return
    
    await ctx.send("Starting adding emojis. This may take a few moments...")
    emojiFilePath = EMOJI_DIR + EMOJI_NAME_FILE + JSON_EXT
    emojiList = {}
    emojiCount = 0
    rarityFilePath = GLOBAL_JSON_PATH + DIR_ID_REFERENCES + IMAGE_DIR_RARITY
    for filename in os.listdir(rarityFilePath):
        with open(rarityFilePath + filename, "rb") as image:
            emojiFileName, emojiFileFormat = os.path.splitext(filename)
            emojiName = emojiPrefix + emojiFileName.lower()
            if emojiFileFormat != DYNAMIC_IMAGE_EXT:
                f = image.read()
                b = bytearray(f)
                guildEmoji = getGuildEmoji(emojiName, ctx.guild.emojis)
                if guildEmoji == EMOJI_NOT_FOUND:
                    print("Emoji {} is NOT!!!! on server {}".format(emojiName, ctx.guild))
                    emoji = await ctx.guild.create_custom_emoji(image=b, name=emojiName)
                    emojiList[emojiName] = emoji.id
                    emojiCount += 1     
                else:
                    print("Emoji {} is already on server {}".format(emojiName, ctx.guild))
                    emojiList[emojiName] = emoji.id
                    
    
    SaveJSONFile(emojiFilePath, emojiList)
    await ctx.send("Done adding emojis. A total of {} emojis were added.".format(emojiCount))

# Delete emojis from bot server
@bot.command()
async def remove_emojis(ctx, *args):

    if ctx.author == bot.user or not str(ctx.author.id) in ADMIN_LIST:
        await ctx.send("Permission Denied.")
        return
    
    await ctx.send("Starting removing server emojis. This may take a few moments...")
    emojiFilePath = EMOJI_DIR + EMOJI_NAME_FILE + JSON_EXT
    emojiList = LoadJSONFile(emojiFilePath)
    emojiCount = 0
    rarityFilePath = GLOBAL_JSON_PATH + DIR_ID_REFERENCES + IMAGE_DIR_RARITY
    for filename in os.listdir(rarityFilePath):
        with open(rarityFilePath + filename, "rb") as image:
            emojiFileName, emojiFileFormat = os.path.splitext(filename)
            emojiName = emojiPrefix + emojiFileName.lower()
            if emojiFileFormat != DYNAMIC_IMAGE_EXT:
                f = image.read()
                b = bytearray(f)
                guildEmoji = getGuildEmoji(emojiName, ctx.guild.emojis)
                if guildEmoji == EMOJI_NOT_FOUND:
                    print("Emoji {} not found on server {}".format(emojiName, ctx.guild))
                else:
                    print("Emoji {} found on server {}".format(emojiName, ctx.guild))
                    await guildEmoji.delete()
                    if emojiName in emojiList.keys():
                        emojiList.pop(emojiName)
                    emojiCount += 1     
    
    SaveJSONFile(emojiFilePath, emojiList)
    await ctx.send("Done removing emojis. A total of {} emojis were removed.".format(emojiCount))

bot.run(BotToken)
