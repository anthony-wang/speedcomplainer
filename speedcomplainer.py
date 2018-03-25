# uses python2

import os
import sys
import time
from datetime import datetime
import daemon
import signal
import threading
import twitter
import json
from collections import OrderedDict # so that tweet messages are imported in order
import random
from logger import Logger
import urllib, json
from HTMLParser import HTMLParser

shutdownFlag = False
debug = True
chuckMode = False

def main(filename, argv):
    print "======================================"
    print "  Starting Speed Complainer!          "
    print "  Let's get noisy!                    "
    print "======================================"

    global shutdownFlag
    signal.signal(signal.SIGINT, shutdownHandler)

    if debug:
        print 'current time: %s' % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    monitor = Monitor()

    while not shutdownFlag:
        try:
            monitor.run()

            for i in range(0, 5):
                if shutdownFlag:
                    break
                time.sleep(1)

        except Exception as e:
            print 'Error: %s' % e
            sys.exit(1)

    sys.exit()

def shutdownHandler(signo, stack_frame):
    global shutdownFlag
    print 'Got shutdown signal (%s: %s).' % (signo, stack_frame)
    shutdownFlag = True


class Monitor():
    def __init__(self):
        self.lastPingCheck = None
        self.lastSpeedTest = None
        self.lastChuckJoke = None
        self.lastTweet = None

        self.timeFudgeFactor = 3

        self.pingCheckInterval = 1 * 60 - self.timeFudgeFactor
        self.speedTestInterval = 10 * 60 - self.timeFudgeFactor
        self.chuckJokeInterval = 10 * 60 - self.timeFudgeFactor
        self.TweetInterval = 30 * 60 - self.timeFudgeFactor

    def run(self):
        if not self.lastPingCheck or (datetime.now() - self.lastPingCheck).total_seconds() >= self.pingCheckInterval:
            if debug:
                print 'checking ping...'
            self.runPingTest()
            self.lastPingCheck = datetime.now()

        if not self.lastSpeedTest or (datetime.now() - self.lastSpeedTest).total_seconds() >= self.speedTestInterval:
            if debug:
                print 'checking speed...'
            self.runSpeedTest()
            self.lastSpeedTest = datetime.now()
            
        if chuckMode and not self.lastChuckJoke and (datetime.now() - self.lastChuckJoke).total_seconds() >= self.chuckJokeInterval:
            if debug:
                print 'getting a Chuck joke...'
            self.runChuckJoke()

    def runPingTest(self):
        pingThread = PingTest()
        pingThread.start()

    def runSpeedTest(self):
        speedThread = SpeedTest()
        speedThread.start()

    def runChuckJoke(self):
        if debug:
            print 'going Chuck....'
        if chuckMode:
            chuckThread = ChuckJoke()
            chuckThread.start()


class PingTest(threading.Thread):
    def __init__(self, numPings=3, pingTimeout=2, maxWaitTime=10):
        super(PingTest, self).__init__()
        self.numPings = numPings
        self.pingTimeout = pingTimeout
        self.maxWaitTime = maxWaitTime
        self.config = json.load(open('./config.json'))
        self.logger = Logger(self.config['log']['type'], { 'filename': self.config['log']['files']['ping'] })

    def run(self):
        pingResults = self.doPingTest()
        if debug:
            print 'checking ping done'
            print 'ping results: %s' % (pingResults)
        self.logPingResults(pingResults)

    def doPingTest(self):
        # NOTE: the ping command is OS-specific!
        if sys.platform.startswith('linux'):
            # The below works on Linux
            response = os.system("ping -c %s -W %s -w %s 8.8.4.4 > /dev/null 2>&1" % (self.numPings, (self.pingTimeout * 1000), self.maxWaitTime))
        elif sys.platform.startswith('darwin'):
            # The below works on MacOS X
            response = os.system("ping -c %s -W %s -t %s 8.8.4.4 > /dev/null 2>&1" % (self.numPings, (self.pingTimeout * 1000), self.maxWaitTime))
        elif sys.platform.startswith('win32'):
            # The below works on Windows
            response = os.system("ping -n %s -w %s 8.8.4.4 > NUL 2>&1" % (self.numPings, (self.pingTimeout * 1000)))

        success = 0
        if debug:
            print 'ping test response (0 == success): %s' % (response)
        if response == 0:
            success = 1
        return { 'date': datetime.now(), 'success': success }

    def logPingResults(self, pingResults):
        self.logger.log([pingResults['date'].strftime('%Y-%m-%d %H:%M:%S'), str(pingResults['success'])])


class ChuckJoke(threading.Thread):
    def __init__(self, joke=""):
        super(ChuckJoke, self).__init__()
        if debug:
            print 'Chuck - init'
        self.joke = ""
        self.config = json.load(open('./config.json'))
        self.logger = Logger(self.config['log']['type'], { 'filename': self.config['log']['files']['chuck'] })
        if debug:
            print 'got a Chuck joke'
    
    def run(self):
        chucksJoke = self.doGetJoke()
        self.logChuckJoke(chucksJoke)

    def doGetJoke(self):
        if debug:
            print 'Chuck - trying to get a Chuck Norris joke'
        url = "https://api.icndb.com/jokes/random"
        response = urllib.urlopen(url)
        data = json.loads(response.read())
        if debug:
            print 'Chuck - joke: %s' % data['value']['joke'] 
        self.joke = data['value']['joke']
        # return {'joke' : data['value']['joke'] }
        return data['value']['joke']

    def logChuckJoke(self, joke):
        self.logger.log([str(datetime.now()), str(joke)])


class SpeedTest(threading.Thread):
    def __init__(self):
        super(SpeedTest, self).__init__()
        # parse config JSON file while preserving order (important for matching speed thresholds for tweet messages)
        self.config = json.load(open('./config.json'), object_pairs_hook=OrderedDict)
        self.logger = Logger(self.config['log']['type'], { 'filename': self.config['log']['files']['speed'] })

    def run(self):
        speedTestResults = self.doSpeedTest()
        if debug:
            print 'checking speed done'
            print 'speed test: %s' % (speedTestResults)
        self.logSpeedTestResults(speedTestResults)
        self.tweetResults(speedTestResults)

    def doSpeedTest(self):
        # run a speed test
        # result = os.popen("/usr/local/bin/speedtest-cli --simple").read()
        result = os.popen("speedtest-cli --simple").read()
        if 'Cannot' in result:
            return { 'date': datetime.now(), 'uploadResult': 0, 'downloadResult': 0, 'ping': 0 }

        # Result:
        # Ping: 529.084 ms
        # Download: 0.52 Mbit/s
        # Upload: 1.79 Mbit/s

        resultSet = result.split('\n')
        pingResult = resultSet[0]
        downloadResult = resultSet[1]
        uploadResult = resultSet[2]

        pingResult = float(pingResult.replace('Ping: ', '').replace(' ms', ''))
        downloadResult = float(downloadResult.replace('Download: ', '').replace(' Mbit/s', '').replace(' Mbits/s', ''))
        uploadResult = float(uploadResult.replace('Upload: ', '').replace(' Mbit/s', '').replace(' Mbits/s', ''))

        print 'speed test results: (DL %#.2f : UL %#.2f : ping %#.3f).' % (downloadResult, uploadResult, pingResult)

        return { 'date': datetime.now(), 'uploadResult': uploadResult, 'downloadResult': downloadResult, 'ping': pingResult }

    def logSpeedTestResults(self, speedTestResults):
        self.logger.log([speedTestResults['date'].strftime('%Y-%m-%d %H:%M:%S'),
            str(speedTestResults['downloadResult']),
            str(speedTestResults['uploadResult']),
            str(speedTestResults['ping'])])

    def tweetResults(self, speedTestResults):
        thresholdMessages = self.config['tweetThresholds']
        message = None
        if debug:
            print 'finally in tweeting mode' 

        for (threshold, messages) in thresholdMessages.items():
            threshold = float(threshold)
            if debug:
                print 'threshold: %f' % (threshold)
                print 'speedTestResults: DL %s : UL %s : ping %s' % (speedTestResults['downloadResult'], speedTestResults['uploadResult'], speedTestResults['ping'])
                # print ChuckJoke.joke
            if speedTestResults['downloadResult'] < threshold:
                if debug:
                    print 'DL rate %f is lower than the threshold %f' % (speedTestResults['downloadResult'], threshold)
                message = (messages[random.randint(0, len(messages) - 1)]
                            .replace('{tweetTo}', self.config['tweetTo'])
                            .replace('{internetSpeed}', self.config['internetSpeed'])
                            .replace('{internetUpSpeed}', self.config['internetUpSpeed'])
                            .replace('{fractionOfSpeed}', "%.2f" % (round(float(speedTestResults['downloadResult']) / float(self.config['internetSpeed']) * 100, 2)))
                            .replace('{downloadResult}', str(speedTestResults['downloadResult']))
                            .replace('{uploadResult}', str(speedTestResults['uploadResult'])))
                message = message + ' ' + str(self.config['appendText']) + '.'
                break

        # add some Chuck Norris to the tweet
        if chuckMode:
            instance = ChuckJoke()
            message = message + ' And by the way: "' + str(instance.doGetJoke()) + '"'

        # truncate message if it's over Twitter's max character limit. Not necessary using when using the "PostUpdates" method from twitter API
        # if len(message) > 500:
        #     message = message[500] + '...'

        # unescape HTML characters in tweet message. Fails when it encounters ampersands '&' in the message...
        # message = HTMLParser.HTMLParser().unescape(message)

        if debug:
            print 'generated message: %s' % (message)

        if not Monitor().lastTweet or (datetime.now() - Monitor().lastTweet).total_seconds() >= Monitor().TweetInterval:
            if debug:
                print 'last tweet: %s' % (Monitor().lastTweet)
                print 'tweet interval: %s' % (Monitor().TweetInterval)
                print 'checking ping...'
            Monitor().lastTweet = datetime.now()

            if message:
                api = twitter.Api(consumer_key=self.config['twitter']['twitterConsumerKey'],
                                consumer_secret=self.config['twitter']['twitterConsumerSecret'],
                                access_token_key=self.config['twitter']['twitterToken'],
                                access_token_secret=self.config['twitter']['twitterTokenSecret'])
                if api:
                    status = api.PostUpdates(message, continuation=u'\u2026')

                    if debug:
                        print 'tweeted message message: %s...' % (message)
                        print 'api: %s' % (api)


class DaemonApp():
    def __init__(self, pidFilePath, stdout_path='/dev/null', stderr_path='/dev/null'):
        self.stdin_path = '/dev/null'
        self.stdout_path = stdout_path
        self.stderr_path = stderr_path
        self.pidfile_path = pidFilePath
        self.pidfile_timeout = 1

    def run(self):
        main(__file__, sys.argv[1:])


if __name__ == '__main__':
    main(__file__, sys.argv[1:])

    workingDirectory = os.path.basename(os.path.realpath(__file__))
    stdout_path = '/dev/null'
    stderr_path = '/dev/null'
    fileName, fileExt = os.path.split(os.path.realpath(__file__))
    pidFilePath = os.path.join(workingDirectory, os.path.basename(fileName) + '.pid')
    from daemon import runner
    dRunner = runner.DaemonRunner(DaemonApp(pidFilePath, stdout_path, stderr_path))
    dRunner.daemon_context.working_directory = workingDirectory
    dRunner.daemon_context.umask = 0o002
    dRunner.daemon_context.signal_map = { signal.SIGTERM: 'terminate', signal.SIGUP: 'terminate' }
    dRunner.do_action()
