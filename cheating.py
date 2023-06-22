# Anti-cheating functions

# basedcount_bot Libraries
from passwords import bot, mongoPass
from pymongo import MongoClient

def connectMongo_History():
    cluster = MongoClient(mongoPass)
    dataBased = cluster['dataBased']
    return dataBased['basedHistory']


def checkForCheating(user, parentAuthor):
    basedHistory = connectMongo_History()
    basedHistory.find_one_and_update({"name": user}, {"$inc": {parentAuthor: 1}}, upsert=True)


def sendCheatReport():
    basedHistory = connectMongo_History()
    userProfile = basedHistory.find({})

    # Add Suspicious Users
    content = ''
    for user in userProfile:
        for key in user:
            if (key != '_id' and key != 'name' and user[key] > 5):
                content += f"{user['name']} based {key} {user[key]} times.\n"

    # Send Cheat Report to Admin
    if content != '':
        pass
        #reddit.redditor(bot.admin).message('Cheat Report', content)

    basedHistory.delete_many({})
