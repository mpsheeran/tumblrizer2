import progressbar
import pytumblr
import json
import time
import socket


#WILL RETURN 'NONE' IF LOAD FAILS
def importSettingsFromFile(filename='dev_config.json'):
    try:
        with open(filename, 'r') as configFile:
            try:
                configDict = json.load(configFile)
            except:
                print('Whoops, couldn\'t load json from file {}. Aborting.'.format(
                    configFile.name))
                return None

    except IOError:
        print('Error accessing file {}. Whoops!'.format(filename))
        return None

    return configDict


#create a pytumblr client using settings contained in a configdict.
#see importSettingsFromFile for details on how that's built.
def getClient(configDict):
    try:
        client = pytumblr.TumblrRestClient(
            configDict['pytumblr_client_configs']['consumer_key'],
            configDict['pytumblr_client_configs']['consumer_secret'],
            configDict['pytumblr_client_configs']['oauth_token'],
            configDict['pytumblr_client_configs']['oauth_secret']
        )
    except:
        print('Error creating client. Whoops!')
        return None

    return client


#pytumblr.TumblrRestClient tumblrClient
def getAllPostIDs(tumblrClient, targetBlog=None, timeout=.1):
    if (targetBlog is not None):
        blogName = targetBlog
    else:
        blogName = tumblrClient.info()['user']['name']

    totalposts = tumblrClient.posts(blogName)['total_posts']
    postIdDict = {'blog': blogName,
                  'postIDs': []}

    postOffset = 0

    print ('\n{} total posts on {}. Gathering IDs.'.format(totalposts, blogName))

    with progressbar.ProgressBar(max_value=totalposts) as progress:
        while(totalposts - postOffset > 20):

            try:
                retrievedPosts = tumblrClient.posts(blogName, offset=postOffset)['posts']

                for post in retrievedPosts:
                    postIdDict['postIDs'].append(post['id'])

                postOffset = postOffset + 20
                progress.update(len(postIdDict['postIDs']))
                time.sleep(timeout)

            except socket.error:
                print('Unexpected connection error gathering posts. Offset: {}, Last ID: {}'.format(
                    postOffset, len(postIdDict['postIDs'])))

                timeout = timeout + .1
                print('Increasing timeout to {} secs.'.format(timeout))

            except KeyboardInterrupt:
                print('Keyboard interrupt detected. Returning current results.')
                progress.max_value = len(postIdDict['postIDs'])
                break

    for post in tumblrClient.posts(blogName, offset=postOffset)['posts']:
        postIdDict['postIDs'].append(post['id'])

    return postIdDict


def writePostIDsToFile(postIdDict, filename):
    try:
        with open(filename, 'w+') as idFile:
            try:
                json.dump(postIdDict, idFile)

            except:
                print('Error writing file {} - exiting.'.format(filename))
                return False

    except IOError:
        print('\nUnable to read file {} - are you sure it exists?'.format(filename))
        return False

    print('\nfile {} written - {} records'.format(idFile.name, len(postIdDict['postIDs'])))
    return True


def readPostIDsFromFile(filename):
    try:
        with open(filename, 'r') as idFile:
            postIdDict = json.load(idFile)
        print '\nfile {} loaded - {} records'.format(filename, len(postIdDict['postIDs']))
    except IOError:
        print('\nUnable to read file {} - are you sure it exists?'.format(filename))
        return None

    return postIdDict


def changePostStateByID(tumblrClient, postIdDict, desiredState):
    blogName = str(postIdDict['blog'])
    postIdCount = len(postIdDict['postIDs'])

    print('\nBeginning mass post update for {}.tumblr.com. Setting {} posts to state:{}'.format(
        blogName, postIdCount, desiredState))

    with progressbar.ProgressBar(max_value=postIdCount) as progress:
        for id in postIdDict['postIDs']:
            try:
                tumblrClient.edit_post(blogName, id=id, state=desiredState)

            except:
                print('Error updating post {} to {}.'.format(id, desiredState))

            progress.update(postIdDict['postIDs'].index(id))

    #verify success
    print('\nNow verifying post update for {}.tumblr.com. Checking {} posts:'.format(
        blogName, postIdCount))

    errorCount = 0
    with progressbar.ProgressBar(max_value=postIdCount) as progress:
        for id in postIdDict['postIDs']:
            actualState = tumblrClient.posts(blogName, id=id)['posts'][0]['state']
            if (actualState != desiredState):
                print('Post ID {} is {}; expected {}'.format(id, actualState, desiredState))
                errorCount = errorCount + 1
            progress.update(postIdDict['postIDs'].index(id))

    print('\nUpdated {} posts to {} on {} -- {} errors.'.format(postIdCount, desiredState, blogName, errorCount))

    if (errorCount > 0):
        return False
    else:
        return True