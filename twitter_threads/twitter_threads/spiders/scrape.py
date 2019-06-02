import scrapy
import tweepy
import json
from datetime import date, timedelta

class ThreadSpider(scrapy.Spider):
    name = "threads"

    def start_requests(self):

        # initialize tweepy
        authfile = './AUTH_dkv'
        (consumer_key, consumer_secret, access_token, access_token_secret) = open(authfile, 'r').read().strip().split('\n')
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, retry_count=10, retry_delay=20, retry_errors=set([503]))
        self.outfile = open('twitter_threads.txt', 'a')

        yesterday = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')

        for tweet in tweepy.Cursor(self.api.search, q="#fv19 OR #dkpol -filter:retweets", start_date=yesterday, tweet_mode="extended").items():
            json = tweet._json
            lang = json['lang']
            retweets = json['retweet_count']
            favorites = json['favorite_count']
            if lang == 'da' and retweets >= 3 and favorites >= 6:
                user = json['user']['screen_name']
                tweet_id = tweet.id
                yield scrapy.Request(url=f'https://twitter.com/{user}/status/{tweet_id}', callback=self.parse)

    def parse(self, response):
        convo = []
        convo += response.css('div.permalink-in-reply-tos div.tweet::attr(data-tweet-id)').getall()
        convo += response.css('div.permalink-tweet-container div.tweet::attr(data-tweet-id)').getall()
        convo += response.css('div.permalink-replies div.tweet::attr(data-tweet-id)').getall()

        root = self.api.get_status(convo.pop(0))._json
        thread = {'root': root, 'children': []}
        for tweet_id in convo:
            thread['children'].append(self.api.get_status(tweet_id)._json)

        self.outfile.write(json.dumps(thread) + '\n')


        
        