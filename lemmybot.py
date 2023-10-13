from pythorhead import Lemmy
import os
from dotenv import load_dotenv

import traceback
from datetime import datetime
import time

# basedcount_bot Libraries
from commands import based, myBasedCount, basedCountUser, mostBased, removePill, myCompass
from flairs import checkFlair
from passwords import bot, bannedWords
from cheating import checkForCheating, sendCheatReport
from backupDrive import backupDataBased

load_dotenv()
username = os.environ.get('USER_NAME')
password = os.environ.get('PASSWORD')
lemmy = Lemmy("https://lemmy.basedcount.com")
lemmy.log_in(username, password)
community_id = lemmy.discover_community("pcm")

counted_comments = []

version = 'Bot v2.19.2.LEMMY'
infoMessage = 'I am a bot created to keep track of how based users are. '\
'Check out the [FAQ](https://reddit.com/r/basedcount_bot/comments/iwhkcg/basedcount_bot_info_and_faq/). '\
'I also track user [pills](https://reddit.com/r/basedcount_bot/comments/l23lwe/basedcount_bot_now_tracks_user_pills/).\n\n'\
'If you have any suggestions or questions, please message them to me with the subject '\
'of "Suggestion" or "Question" to automatically forward them to a human operator.\n\n'\
'> based - adj. - to be in possession of viewpoints acquired through logic or observation '\
'rather than simply following what your political alignment dictates, '\
'often used as a sign of respect but not necessarily agreement\n\n'\
+version+'\n\n'\
'**Commands: /info | /mybasedcount | /basedcount username | /mostbased | /removepill pill | /mycompass politicalcompass.org or sapplyvalues.github.io url**'

# Vocabulary
excludedAccounts = ['basedcount_bot', 'flairchange_bot']
excludedParents = ['basedcount_bot']
botName_Variations = ['basedcount_bot']

based_Variations = ['based', 'baste', 'basado', 'basiert',
					'basato', 'fundiert', 'fondatum', 'bazita',
					'מבוסס', 'oparte', 'bazowane', 'basé', 'baseado',
					'gebaseerd', 'bazirano', 'perustuvaa', 'perustunut',
					'основано', '基于', 'baseret', 'بايسد, ',
					'na základě', 'basert', 'bazirano', 'baserad',
					'basat', 'ベース', 'bazat', 'berdasar', 'Базирано',
					'gebasseerd', 'Oj +1 byczq +1', 'Oj+1byczq+1']

pillExcludedStrings_start = ['based', 'baste', 'and ', 'but ', 'and-', 'but-', ' ', '-', 'r/', '/r/',
					'basado', 'basiert',
					'basato', 'fundiert', 'fondatum', 'bazita',
					'מבוסס', 'oparte', 'bazowane', 'basé', 'baseado',
					'gebaseerd', 'bazirano', 'perustuvaa', 'perustunut',
					'основано', '基于', 'baseret', 'بايسد, ',
					'na základě', 'basert', 'bazirano', 'baserad',
					'basat', 'ベース', 'bazat', 'berdasar', 'Базирано',
					'gebasseerd', 'Oj +1 byczq +1', 'Oj+1byczq+1']

pillExcludedStrings_end = [' and', ' but', ' ', '-']

myBasedCount_Variations = ['/mybasedcount']
basedCountUser_Variations = ['/basedcount']
mostBased_Variations = ['/mostbased']

run = True


# |-----------|
# |   Inbox   |
# |-----------|

def checkMail():
        pass
'''
	inbox = reddit.inbox.unread(limit=30)
	for message in inbox:
		if run == False:
				closeBot()
		message.mark_read()
		currentTime = datetime.now().timestamp()
		if ((message.created_utc > (currentTime-180)) and (message.was_comment is False)):
			content = str(message.body)
			author = str(message.author)

# --------- Check Questions and Suggestions and then reply
			if ('suggestion' in str(message.subject).lower()) or ('question' in str(message.subject).lower()):
				if str(message.subject).lower() in 'suggestion':
					message.reply('Thank you for your suggestion. I have forwarded it to a human operator.')
				if str(message.subject).lower() in 'question':
					message.reply('Thank you for your question. I have forwarded it to a human operator, and I should reply shortly with an answer.')
				reddit.redditor(bot.admin).message(str(message.subject) + ' from ' + author, content)

# --------- Check for user commands
			if '/info' in content.lower():
					message.reply(infoMessage)

			for v in myBasedCount_Variations:
				if v in content.lower():
					replyMessage = myBasedCount(author)
					message.reply(replyMessage)
					break

			for v in basedCountUser_Variations:
				if v in content.lower():
					replyMessage = basedCountUser(content)
					message.reply(replyMessage)
					break

			for v in mostBased_Variations:
				if v in content.lower():
					replyMessage = mostBased()
					message.reply(replyMessage)
					break

			if content.lower().startswith('/removepill'):
				replyMessage = removePill(author, content)
				message.reply(replyMessage)

			if content.lower().startswith('/mycompass'):
				replyMessage = myCompass(author, content)
				message.reply(replyMessage)
'''

class Comment():
     def __init__(self) -> None:
          pass

def readComments():
    try:
        print('Searching...')
        
        posts = lemmy.post.list(community_id=community_id, limit=1)
        print("Post Name: " + posts[0]['post']['name'])
        print("Post Author: " + str(posts[0]['post']['creator_id']))
        print("Post ID: " + str(posts[0]['post']['id']))
        comments = lemmy.comment.list(community_id=community_id, post_id=posts[0]['post']['id'], max_depth=30)
        print("Comment Body: " + comments[0]['comment']['content'])
        print("Comment Author: " + comments[0]['creator']['actor_id'])
        print("Comment ID: " + str(comments[0]['comment']['id']))

        # Weird check to see if Lemmy actually sent a comments list
        if "comments" in comments:
            comments = comments["comments"]

            # Get initial data to see if action is necessary
            for comment in comments:
                if run == False:
                    closeBot()
                checkMail()

                # Get data from comment
                author = comment["creator"]["name"]
                if author not in excludedAccounts:
                    commenttext = comment["comment"]["content"]
                    comment_id = comment["comment"]["id"]
                    post_id = comment["comment"]["post_id"]

                    # Check if already counted
                    newComment = True
                    for counted in counted_comments:
                         if comment_id == counted:
                            newComment = False
                            break
                              
                    # Comment is new
                    if newComment:
                        counted_comments.append(comment_id)

                        # Remove bot mentions from comment text
                        for v in botName_Variations:
                            if v in commenttext:
                                commenttext.replace(v, '')

# --------------------- Based Check
                        for v in based_Variations:
                            if (commenttext.lower().startswith(v))and not (commenttext.lower().startswith('based on ') or commenttext.lower().startswith('based off ')):

                                # Get data from parent comment/submission
                                path = comment["comment"]["path"]
                                path_elements = path.split(".")
                                parent_comment_id = int(path_elements[-2])

                                # Parent is a comment
                                try:
                                    parentComment = lemmy.post.get_comment(post_id=parent_comment_id)
                                    parentAuthor = parentComment['comment_view']['creator']['name']
                                    parentText = parentComment["comment_view"]["comment"]["content"]
                                
                                # Parent is a post, still throws error
                                except:
                                    parentComment = lemmy.post.get(post_id=post_id)
                                    parentAuthor = parentComment['post_view']['creator']['name']
                                    parentText = 'submission is a post'
                                #flair = str(checkFlair(parentFlair))
                                flair = 'Lemmy_No_Flairs'

                                # Make sure bot isn't the parent
                                comment_flair_text = 'Lemmy_No_Flairs'
                                if (parentAuthor not in excludedParents) and (parentAuthor not in author) and (comment_flair_text != 'None'):

                                    # Check for cheating
                                    cheating = False
                                    for v in based_Variations:
                                        if parentText.lower().startswith(v) and (len(parentText) < 50):
                                            cheating = True
                                    if cheating:
                                        break
                                    
                                    # Check for pills
                                    pill = 'None'
                                    if 'pilled' in commenttext.lower():
                                        pill = commenttext.lower().partition('pilled')[0]
                                        if (len(pill) < 70) and ('.' not in pill):

                                            # Clean pill string beginning
                                            pillClean = 0
                                            while pillClean < len(pillExcludedStrings_start):
                                                for pes in pillExcludedStrings_start:
                                                    if pill.startswith(pes):
                                                        pill = pill.replace(pes, '', 1)
                                                        pillClean = 0
                                                    else:
                                                        pillClean += 1

                                            # Clean pill string ending
                                            pillClean = 0
                                            while pillClean < len(pillExcludedStrings_end):
                                                for pes in pillExcludedStrings_end:
                                                    if pill.endswith(pes):
                                                        pill = pill[:-1]
                                                        pillClean = 0
                                                    else:
                                                        pillClean += 1

                                            # Make sure pill is acceptable
                                            pillBan = False
                                            for w in bannedWords:
                                                if w in pill:
                                                    pillBan = True

                                            # Build pill dict entry using comment info
                                            if (pillBan==False):
                                                pillInfo = {}
                                                pillInfo['name'] = pill
                                                pillInfo['commentID'] = 'https://forum.basedcount.com/comment/' + str(comment_id)
                                                pillInfo['fromUser'] = author
                                                pillInfo['date'] = comment["comment"]["published"]
                                                pillInfo['amount'] = 1

                                                pill = pillInfo
                                            else:
                                                pill = 'None'
                                        else:
                                            pill = 'None'

                                    # Calculate Based Count and build reply message
                                    if flair != 'Unflaired':
                                        replyMessage = based(parentAuthor, flair, pill)

                                        # Build list of users and send Cheat Report to admin
                                        checkForCheating(author, parentAuthor)

                                    # Reply
                                    else:
                                        replyMessage = "Don't base the Unflaired scum!"
                                    if replyMessage:
                                            #lemmy.post.write_comment(post_id, commentid, f"{parentAuthor}'s Based Count has increased by 1.")
                                            print(f"{parentAuthor}'s Based Count has increased by 1.")
                                    break
                        
# --------------------- Commands
                        if commenttext.lower().startswith('/info'):
                            #lemmy.post.write_comment(post_id, commentid, infoMessage)
                            print(infoMessage)

                        for v in myBasedCount_Variations:
                            if v in commenttext.lower():
                                replyMessage = myBasedCount(author)
                                #lemmy.post.write_comment(post_id, commentid, replyMessage)
                                print(replyMessage)
                                break

                        for v in basedCountUser_Variations:
                            if commenttext.lower().startswith(v):
                                replyMessage = basedCountUser(commenttext)
                                #lemmy.post.write_comment(post_id, commentid, replyMessage)
                                print(replyMessage)
                                break

                        for v in mostBased_Variations:
                            if v in commenttext.lower():
                                replyMessage = mostBased()
                                #lemmy.post.write_comment(post_id, commentid, replyMessage)
                                print(replyMessage)
                                break

                        if commenttext.lower().startswith('/removepill'):
                            replyMessage = removePill(author, commenttext)
                            #lemmy.post.write_comment(post_id, commentid, replyMessage)
                            print(replyMessage)

                        if commenttext.lower().startswith('/mycompass'):
                            replyMessage = myCompass(author, commenttext)
                            #lemmy.post.write_comment(post_id, commentid, replyMessage)
                            print(replyMessage)
                
        else:
            print("No comments found.")

    except:
        print('Oopsie poopsie!')
    
    time.sleep(10)


# Execute
def main():
	# Start
	try:
		checkMail()
		readComments()
		print('End Cycle')
	# Record info if an error is encountered
	except Exception:
		print('Error occurred:' + str(datetime.today().strftime('%Y-%m-%d')))
		traceback.print_exc()
	#main()


def closeBot():
	#sendCheatReport()
	print('Shutdown complete.')
	exit()
main()

#while run:
	#main()
