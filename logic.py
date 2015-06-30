#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import twitter_api_func as twapi
import pickle
import numpy as np
import tokenization as tknz
import datetime
from collections import OrderedDict
import psycopg2 as mdb
import logging
import pandas as pd
import sklearn
import logscaler
from logscaler import LogScaler
logging.basicConfig(level=logging.DEBUG)

dbuser="ubuntu"

def get_random_users(n=5, prediction = True):
    con = mdb.connect(dbname="tweets",user=dbuser)
    with con.cursor() as cur:
        cur.execute(u"SELECT name, screen_name, profile_pic_url, "
        "prediction FROM users WHERE prediction IS NOT NULL AND name "
        "IS NOT NULL AND screen_name IS NOT NULL "
        "AND profile_pic_url IS NOT NULL")
        data = np.array(cur.fetchall())
        #print data.shape
        #print data[[0,1,2],3]
        data = data[data[:,3] == str(prediction), :]
        indices = np.random.random_integers(0, data.shape[0], n)
        return [ { 'name': r[0].decode('utf-8') ,'screen_name': r[1].decode('utf-8'), 'profile_image_url': r[2] } for r in data[indices] if r is not None ]

def get_random_users_reprocess(n=5, prediction = True):
    pass

def get_tweets_by_user(screen_name):
    api = twapi.get_api()
    logging.debug(screen_name)
    user_tweets = api.user_timeline(screen_name=screen_name, count=4)
    logging.debug("Number of tweets retrieved: {}".format(len(user_tweets)))
    return user_tweets
    

def vectorize_tweeter(screen_name_or_id, tweets, query_date=datetime.datetime.now()):
    """Look up tweeter by screen name. Produce feature matrix from
    their user information and timeline. Returns untransformed 
    features in a pandas dataframe"""
    
    features = { 'age' : None, 'friends_count': None, 'followers_count': None,
    'name': None, 'profile_image_url': None }
    features_df = None
    
    try:
        api = twapi.get_api()
        user_corpus = [tweet.text for tweet in tweets]
        #scaler = pickle.load(file("app/static/models/scaler.pickle","r"))
        user = api.get_user(screen_name_or_id)
        now = pd.to_datetime(datetime.datetime.now())
        logging.debug("Original created at: {}".format(user.created_at))
        logging.debug("Converted created at: {}".format(pd.to_datetime(user.created_at)))
        age = now - pd.to_datetime(user.created_at)
        if age.days > 365:
            user_age = "%0.1f years" % (float(age.days) / 365.)
        elif age.days < 365:
            user_age = "%d months" % (age.days / 30)
        
        age = pd.Series(age).astype(np.int64).values[0]
        
        features = { 'user_age_str' :  user_age,
                     'user_age' : age,
                     'friends_count' : user.friends_count,
                     'followers_count' : user.followers_count,
                     'friend_follow': np.log(float(user.followers_count) / \
                        float(user.friends_count + 1) + 0.001),
                     'name': user.name,
                     'profile_image_url': user.profile_image_url.replace(u"_normal", u"_bigger") }
        colnames=('followers_count', 'friends_count', 
                    'user_age', 'friend_follow')
        features_df=pd.DataFrame(OrderedDict([ (k, [features[k]]) for k in colnames ]))
        logging.debug(features_df)
        
    except:
        logging.warning("Exception: ", exc_info=True)
    
    finally:
        return (features, features_df)
    
def load_model(model_path=None):
    if model_path is None:
        #model_path="app/static/models/svm1434693300.pkl"
        #model_path="app/static/models/logreg_1435302860.pkl"
        model_path="app/static/models/logreg_1435362548.pkl"
    model = pickle.load(file(model_path, "r"))
    return model
