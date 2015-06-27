#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import os
import re
from flask import render_template , request, url_for, redirect
from app import app
import logging
logging.basicConfig(level=logging.DEBUG)

import psycopg2 as mdb
import tweepy

from logic import vectorize_tweeter, load_model, get_tweets_by_user, \
    get_random_users

dbuser="ubuntu"
db= mdb.connect(dbname="tweets", user=dbuser)
the_model = load_model()  
    
@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('app_dashboard'))

@app.route("/app/")
def app_dashboard():
    random_users = get_random_users()
    return render_template('dashboard.html', users=random_users)

@app.route("/user", methods=["GET"])
def redirect_to_user():
    screen_name = request.args.get('screen_name')
    logging.debug(screen_name)
    return redirect(url_for('twitter_user_view', screen_name=screen_name))

@app.route("/user/<screen_name>")
def twitter_user_view(screen_name=None):
    
    if screen_name == "":
        screen_name=None
    try:
        tweets = get_tweets_by_user(screen_name)
        logging.debug(screen_name)
        feature_dict, feature_df = vectorize_tweeter(screen_name, tweets)
        will_churn=the_model.predict(feature_df)
        error_txt = None
    except tweepy.TweepError:
        return render_template("user-not-found.html")
    except Exception as e:
        error_txt="Error"
        logging.debug("Error: ", exc_info=True)
        
    return render_template('twitter-user.html',
                           twitter_name=feature_dict['name'],
                           screen_name=screen_name,
                           tweet_list=tweets,
                           user=feature_dict,
                           will_churn=will_churn,
                           error_txt=error_txt)


@app.template_filter('twitterate')
def make_twitter_links(value):
    """jinja2 filter. find @xxx in value, replace with in-app link"""
    at_pattern = r"""@(\[A-Za-z0-9_]+)"""
    re.sub(at_pattern, """<a href="/user/\1">@\1</a>""", value)
