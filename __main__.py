import tumblrize
import argparse


def main():
    parser = argparse.ArgumentParser()

    ###############################
    #### ARGUMENT DEFINITIONS #####
    ###############################

    #positional args
    parser.add_argument(
        "action",
        help="ACTION: the action you want to perform",
        choices=["scrapepostids", "readpostids", "scrapeposts", "makepostsprivate", "makepostspublished"]
    )

    #optional args
    parser.add_argument(
        "-b", "--blogName",
        help="set target blog"
    )

    parser.add_argument(
        "-o", "--outputFile",
        help="override default output file name"
    )

    parser.add_argument(
        "-i", "--inputFile",
        help="set input file name. only accepts JSON at the moment."
    )

    parser.add_argument(
        "-c", "--configFile",
        help="use an alternate config file. be careful."
    )

    parser.add_argument(
        "-e", "--excludeIDs",
        help="define a comma-separated list of excluded IDs"
    )

    # Parse them args
    arguments = parser.parse_args()

    ###############################
    #### OPTIONAL ARG HANDLING ####
    ###############################

    if (arguments.excludeIDs is not None):
        excludedIDs = map(int, arguments.excludeIDs.split(','))
    else:
        excludedIDs = None

    if (arguments.configFile is not None):
        configs = tumblrize.importSettingsFromFile(arguments.configFile)
    else:
        configs = tumblrize.importSettingsFromFile()

    if (configs is None):
        print ('Error loading configuration file. Closing.')
        return False

    tumblrClient = tumblrize.getClient(configs)

    if (tumblrClient is None):
        print ('Error creating client. Closing.')
        return False

    tumblrClientInfo = tumblrClient.info()

    #handle auth failures here
    if ('errors' in tumblrClientInfo):
        print("errors encountered while authenticating. Please confirm your API keys. Exiting.")
        print("error detail:")
        print(tumblrClientInfo['errors'])
        return False

    if (arguments.action == 'scrapepostids'):
        if (arguments.blogName is not None):
            blogName = arguments.blogName
            postIdDict = tumblrize.getAllPostIDs(tumblrClient, blogName)
        else:
            blogName = str(tumblrClientInfo['user']['name'])
            postIdDict = tumblrize.getAllPostIDs(tumblrClient)

        if (arguments.outputFile is not None):
            result = tumblrize.writeDictToJSON(postIdDict, '{}.json'.format(arguments.outputFile))
            return result
        else:
            writeFileName = '{}_post_ids.json'.format(blogName)
            result = tumblrize.writeDictToJSON(postIdDict, writeFileName)
            return result

    elif (arguments.action == 'scrapeposts'):
        if (arguments.blogName is not None):
            blogName = arguments.blogName
            postDict = tumblrize.getAllPosts(tumblrClient, blogName)
        else:
            blogName = str(tumblrClientInfo['user']['name'])
            postDict = tumblrize.getAllPosts(tumblrClient)

        if (arguments.outputFile is not None):
            result = tumblrize.writeDictToJSON(postDict, '{}.json'.format(arguments.outputFile))
            return result
        else:
            writeFileName = '{}_posts.json'.format(blogName)
            result = tumblrize.writeDictToJSON(postDict, writeFileName)
            return result

    elif (arguments.action == 'readpostids'):
        if (arguments.inputFile is None):
            print('Error! You must define an input file to perform this action. Exiting.')
            return False

        else:
            postIdDict = tumblrize.readPostIDsFromFile(arguments.inputFile)

            if (excludedIDs is not None):
                print('Excluding {}'.format(excludedIDs))
                postIdDict['postIDs'] = [item for item in postIdDict['postIDs'] if item not in excludedIDs]

            blogName = postIdDict['blog']
            idList = postIdDict['postIDs']
            for id in idList:
                print('{}/{}'.format(blogName, id))
            return True

    elif (arguments.action in ['makepostsprivate', 'makepostspublished']):
        if (arguments.inputFile is None):
            print('Error! You must define an input file to perform this action. Exiting.')
            quit()
        else:
            if (arguments.action == 'makepostsprivate'):
                desiredState = 'private'
            elif (arguments.action == 'makepostspublished'):
                desiredState = 'published'
            else:
                #How did we get here?
                return False

            postIdDict = tumblrize.readPostIDsFromFile(arguments.inputFile)
            if (excludedIDs is not None):
                print('Excluding {}'.format(excludedIDs))
                postIdDict['postIDs'] = [item for item in postIdDict['postIDs'] if item not in excludedIDs]

            if (postIdDict is None):
                print('Unable to read post IDs. Exiting.')
                return False

            #check to make sure client blog matches target blog
            if (tumblrClient.info()['user']['name'] != postIdDict['blog']):
                print('This action can only be performed on the authed blog ({}). Exiting.'.format(
                    configs['blog']))
                return False

            result = tumblrize.changePostStateByID(tumblrClient, postIdDict, desiredState)
            return result

    else:
        print('How did we get here?')

if __name__ == "__main__":
    main()
