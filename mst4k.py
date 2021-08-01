import os
import shlex
import json
import re

import requests
import discord
from bs4 import BeautifulSoup
from dotenv import load_dotenv

POLL_MOVIE_COUNT = 10
REMOVAL_YEET_COUNT = 5
BOT_CALL_PREFIX = "mst4k "
USER_ROLE = "director"

load_dotenv()
client = discord.Client()
poll_url = ""

def get_movies():
    if not os.path.exists("movies.json"):
        return {'queued':[], 'backlog':[], 'seen':[]}
    with open("movies.json") as f:
        try:
            return json.load(f)
        except ValueError as e:
            return {'queued':[], 'backlog':[], 'seen':[]}
        
def update_movies(movies):
    with open("movies.json", "w") as f:
        json.dump(movies, f, indent=4)

def move_backlog():
    movies = get_movies()
    queue_length = len(movies['queued'])
    backlog_length = len(movies['backlog']) 
    while(queue_length < POLL_MOVIE_COUNT and backlog_length > 0):
        movies['queued'].append(movies['backlog'][0])
        del movies['backlog'][0]
        queue_length += 1
        backlog_length -= 1
    update_movies(movies)
    
def make_poll(movie_queue):
    global poll_url
    
    data = {}
    data['address'] = ""
    data['poll-1[question]'] = "films"
    for index, movie in enumerate(movie_queue):
        key = 'poll-1[option' + str(index+1) + ']'
        value = movie['title']
        if movie['yeets'] != 0:
            value += " - " + str(movie['yeets']) + " yeet(s)"
        data[key] = value
    data['poll-1[voting-system]'] = 3
    data["poll-1[ranking]"] = ""
    data['voting-limits-dropdown'] = 2

    response = requests.post("https://youpoll.me", data)    
    poll_url = response.url
    
def get_winner_loser():
    global poll_url
    response = requests.get(poll_url+"/r")
    soup = BeautifulSoup(response.content, 'html.parser')
    rows = soup.find_all('tr', {'class':'poll-table-wrapper'})
    winner = rows[0].find('td', {'class':'word-wrap text-column'}).get_text()
    loser = rows[-1].find('td', {'class':'word-wrap text-column'}).get_text()
    winner_title = re.sub(r' - \d+ yeet\(s\)', '', winner)
    loser_title = re.sub(r' - \d+ yeet\(s\)', '', loser)
    return winner_title, loser_title

def set_seen(movie_title):
    movies = get_movies()
    movie_index = -1
    for index, movie in enumerate(movies['queued']):
        if movie['title'] == movie_title:
            movie_index = index
    if movie_index != -1:
        movies['seen'].append(movies['queued'][movie_index]['title'])
        del movies['queued'][movie_index]
        update_movies(movies)
    
def yeet(movie_title):
    movies = get_movies()
    movie_index = -1
    for index, movie in enumerate(movies['queued']):
        if movie['title'] == movie_title:
            movie_index = index
    if movie_index != -1:
        yeets = movies['queued'][movie_index]['yeets'] + 1
        if yeets < REMOVAL_YEET_COUNT:
            movies['queued'][movie_index]['yeets'] = yeets
            movies['backlog'].append(movies['queued'][movie_index])         
        del movies['queued'][movie_index]
        update_movies(movies)
        return yeets

def get_list_text(movies):
    text = ""
    for movie in movies:
        text += "**" + movie['title'] + ":** " + movie['desc'] + "\n\n"
    return text

async def send(text, channel):
    index = 0
    while(index < len(text)):
        await channel.send(text[index:index+2000])
        index += 2000

def add(arguments_string):
    arguments = shlex.split(arguments_string)
    if len(arguments) != 2:
        return "wrong number of arguments"
    movies = get_movies()
    movies['backlog'].insert(0, {'title':arguments[0],'desc':arguments[1],'yeets': 0})
    update_movies(movies)
    return arguments[0] + " added"
    
def poll():
    global poll_url
    if poll_url != "":
        return "poll already running at " + poll_url
    move_backlog()
    movie_queue = get_movies()['queued']
    if len(movie_queue) == 0:
        return "no movies in queue"
    make_poll(movie_queue)
    return get_list_text(movie_queue) + poll_url
    
def tally():
    global poll_url
    if poll_url == "":
        return "no poll to tally"
    winner, loser = get_winner_loser()
    set_seen(winner)
    yeet_count = yeet(loser)
    poll_url = ""
    text_response = "**" + winner + " wins!**\n"
    text_response += loser + " now yeeted " + str(yeet_count) + " time(s)"
    if yeet_count >= REMOVAL_YEET_COUNT:
        text_response += "*~!PERMAYEET!~*"
    return text_response
    
def cancel():
    global poll_url
    if poll_url == "":
        return "no poll to cancel"
    poll_url = ""
    return "poll cancelled"

@client.event
async def on_message(message):
    if message.author == client.user:
        return   
    if not message.content.startswith(BOT_CALL_PREFIX):
        return
    if not USER_ROLE in (role.name for role in message.author.roles):
        return           
    
    content_no_prefix = message.content.removeprefix(BOT_CALL_PREFIX)
    parameters = content_no_prefix.split(" ", 1)
    command = parameters[0]
    
    if(command == "add"):
        await send(add(parameters[1]), message.channel)
    elif(command == "poll"):    
        await send(poll(), message.channel)
    elif(command == "tally"):
        await send(tally(), message.channel)
    elif(command == "cancel"):
        await send(cancel(), message.channel)
    elif(command == "list"):
        await send(get_list_text(get_movies()['queued']) + poll_url, message.channel)
    elif(command == "backlog"):
        await send(get_list_text(get_movies()['backlog']), message.channel)
        
client.run(os.getenv('BOT_TOKEN'))