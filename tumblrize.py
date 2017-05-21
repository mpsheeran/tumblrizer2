import progressbar
import pytumblr
import json
import time
import socket


def importSettingsFromFile(filename='dev_config.json'):
    try:
        with open(filename, 'r') as configFile:
            try:
                configDict = json.load(configFile)
            except:
                print('\nWhoops, couldn\'t load json from file {}. Aborting.'.format(
                    configFile.name))
                raise

    except IOError:
        print('\nError accessing file {}. Whoops!'.format(filename))
        raise

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
        print('\nError creating client. Whoops!')
        raise

    return client


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
                print('\nUnexpected connection error gathering posts. Offset: {}, Last ID: {}'.format(
                    postOffset, len(postIdDict['postIDs'])))

                if (timeout <= .5):
                    print('\nIncreasing timeout to {} secs.'.format(timeout + .1))
                    timeout = timeout + .1

                else:
                    print('\nMaximum timeout exceeded. Something\'s really wrong. Exiting.')
                    raise

            except KeyboardInterrupt:
                print('\nKeyboard interrupt detected. Returning current results.')
                progress.max_value = len(postIdDict['postIDs'])
                break

            except:
                print('\nUnexpected error gathering posts. Offset: {}, Last ID: {}'.format(
                    postOffset, len(postIdDict['postIDs'])))
                break
    try:
        retrievedPosts = tumblrClient.posts(blogName, offset=postOffset)['posts']
        for post in retrievedPosts:
            postIdDict['postIDs'].append(post['id'])

    except:
        print('\nUnexpected error gathering posts. Offset: {}, Last ID: {}'.format(
            postOffset, len(postIdDict['postIDs'])))

    return postIdDict


def getAllPosts(tumblrClient, targetBlog=None, timeout=.1):
    if (targetBlog is not None):
        blogName = targetBlog
    else:
        blogName = tumblrClient.info()['user']['name']

    totalposts = tumblrClient.posts(blogName)['total_posts']
    postDict = {'blog': blogName,
                'posts': []}

    postOffset = 0

    print ('\n{} total posts on {}. Gathering.'.format(totalposts, blogName))

    with progressbar.ProgressBar(max_value=totalposts) as progress:
        while(totalposts - postOffset > 20):

            try:
                postDict['posts'] = postDict['posts'] + tumblrClient.posts(blogName, offset=postOffset)['posts']

                postOffset = postOffset + 20
                progress.update(len(postDict['posts']))
                time.sleep(timeout)

            except socket.error:
                print('\nUnexpected connection error gathering posts. Offset: {}, Last ID: {}'.format(
                    postOffset, len(postDict['posts'])))

                if (timeout <= .5):
                    print('\nIncreasing timeout to {} secs.'.format(timeout + .1))
                    timeout = timeout + .1

                else:
                    print('\nMaximum timeout exceeded. Something\'s really wrong. Exiting.')
                    raise

            except KeyboardInterrupt:
                print('\nKeyboard interrupt detected. Returning current results.')
                progress.max_value = len(postDict['posts'])
                break

            except:
                print('\nUnexpected error gathering posts. Offset: {}, Last ID: {}'.format(
                    postOffset, len(postDict['posts'])))
                break
    try:
        postDict['posts'] = postDict['posts'] + tumblrClient.posts(blogName, offset=postOffset)['posts']

    except:
        print('\nUnexpected error gathering posts. Offset: {}, Last ID: {}'.format(
            postOffset, len(postDict['posts'])))

    return postDict


def writeDictToJSON(dict, filename):
    try:
        with open(filename, 'w+') as outputFile:
            try:
                json.dump(dict, outputFile)

            except:
                print('\nError dumping JSON to file {} - exiting.'.format(filename))
                raise

    except IOError:
        print('\nUnable to read file {} - are you sure it exists?'.format(filename))
        raise

    print('\nfile {} written'.format(outputFile.name))
    return True


def readPostIDsFromFile(filename):
    try:
        with open(filename, 'r') as idFile:
            postIdDict = json.load(idFile)
        print '\nfile {} loaded - {} records'.format(filename, len(postIdDict['postIDs']))

    except IOError:
        print('\nUnable to read file {} - are you sure it exists?'.format(filename))
        raise

    return postIdDict


#this doesn't have any validation on desiredState
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
