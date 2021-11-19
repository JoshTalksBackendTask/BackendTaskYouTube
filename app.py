# importing important modules

from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_api import status

import markdown.extensions.fenced_code

from datetime import datetime
import os
from dotenv import load_dotenv
import requests
import json
import asyncio
import time
import threading

from YouTubeData import YouTubeData

# initializing the flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///data/videos.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# declaring the Videos model
class Videos(db.Model):

    sno = db.Column(db.Integer, primary_key=True)
    videoID = db.Column(db.String,unique=True,nullable=False)
    videoTitle = db.Column(db.String,nullable=False)
    description = db.Column(db.Text,nullable=False)
    publishedAt = db.Column(db.String,nullable=False)
    thumbnails = db.Column(db.JSON,nullable=False)
    channelTitle = db.Column(db.String,nullable=False)
    views = db.Column(db.Integer,nullable=False)
    likes = db.Column(db.Integer,nullable=False)
    dislikes = db.Column(db.Integer,nullable=False)
    comments = db.Column(db.Integer,nullable=False)
    tag = db.Column(db.String,nullable=False)
    dateCreated = db.Column(db.DateTime,nullable=False,default=datetime.utcnow)

# initializing the YouTubeData class which imported for fetching the data
ytd = YouTubeData()

# this function will run in background using multithreading
def saveData(tag="official", maxRecords=50):
    try:
        res = ytd.queryVideos(tag,maxRecords)

        if res:
            data = list()
            for dataPoint in res["items"]:
                newData = dict()

                newData["videoId"] = dataPoint["id"]["videoId"]
                newData["title"] = dataPoint["snippet"]["title"]
                newData["publishedAt"] = dataPoint["snippet"]["publishedAt"]
                newData["channelTitle"] = dataPoint["snippet"]["channelTitle"]
                newData["description"] = dataPoint["snippet"]["description"]
                newData["thumbnails"] = dataPoint["snippet"]["thumbnails"]

                videoData = ytd.getVideoDetails(newData["videoId"])["items"][0]["statistics"]

                newData["views"] = int(videoData["viewCount"])
                newData["likes"] = int(videoData["likeCount"])
                newData["dislikes"] = int(videoData["dislikeCount"])
                newData["comments"] = int(videoData["commentCount"])

                video = Videos(
                    videoID=newData["videoId"],
                    videoTitle=newData["title"],
                    publishedAt=newData["publishedAt"],
                    description = newData["description"],
                    thumbnails = newData["thumbnails"],
                    channelTitle = newData["channelTitle"],
                    views = newData["views"],
                    likes = newData["likes"],
                    dislikes = newData["dislikes"],
                    comments = newData["comments"],
                    tag = tag)
                
                db.session.add(video)
                db.session.commit()

                data.append(newData)
            
            time.sleep(20)

            saveData()
    except Exception:
        return -1

    return 1


# creating the database path if it doesnot exist
if not os.path.exists("/data/videos.db"):
    if not os.path.exists("data"):
        os.mkdir("data") 
    db.create_all()




    
    


# the index route which give the user how to use this api
@app.route("/",methods=["GET"])
def index():
    readme_file = open("Readme.md", "r")
    md_template_string = markdown.markdown(
        readme_file.read(), extensions=["fenced_code"]
    )

    return md_template_string

# this route not only saves the data into the datbase for the given query but also displays the data in desired tabular manner to the user
@app.route("/fetchData",methods=["POST","GET"])
def fetchData():

    if request.method == "POST":

        try:
            res = ytd.queryVideos(request.args.get("tag"),int(request.args.get("maxRecords"))*10)

            data = list()

            for dataPoint in res["items"]:
                newData = dict()

                newData["videoId"] = dataPoint["id"]["videoId"]
                newData["title"] = dataPoint["snippet"]["title"]
                newData["publishedAt"] = dataPoint["snippet"]["publishedAt"]
                newData["channelTitle"] = dataPoint["snippet"]["channelTitle"]
                newData["description"] = dataPoint["snippet"]["description"]
                newData["thumbnails"] = dataPoint["snippet"]["thumbnails"]

                videoData = ytd.getVideoDetails(newData["videoId"])["items"][0]["statistics"]

                newData["views"] = int(videoData["viewCount"]) if "viewCount" in [key for key in videoData] else 0
                newData["likes"] = int(videoData["likeCount"]) if "likeCount" in [key for key in videoData] else 0
                newData["dislikes"] = int(videoData["dislikeCount"]) if "dislikeCount" in [key for key in videoData] else 0
                newData["comments"] = int(videoData["commentCount"]) if "commentCount" in [key for key in videoData] else 0

                video = Videos(
                    videoID=newData["videoId"],
                    videoTitle=newData["title"],
                    publishedAt=newData["publishedAt"],
                    description = newData["description"],
                    thumbnails = newData["thumbnails"],
                    channelTitle = newData["channelTitle"],
                    views = newData["views"],
                    likes = newData["likes"],
                    dislikes = newData["dislikes"],
                    comments = newData["comments"],
                    tag = request.args.get("tag"))
                
                db.session.add(video)
                db.session.commit()

                data.append(newData)
        
        except Exception:
            return {"response":"Bad response"}, status.HTTP_400_BAD_REQUEST


        return {"response":"Data added successfully"}
    
    else:
        tag = request.args.get("tag")
        maxRecords = int(request.args.get("maxRecords"))
        page = int(request.args.get("page"))

        reqVideos = Videos.query.filter_by(tag=tag).order_by(Videos.publishedAt).all()

        data = list()

        # print(reqVideos)

        totRecords = len(reqVideos)

        totPages = int(totRecords/maxRecords)

        pageStart = ((page-1)*maxRecords)+1
        pageEnd = page*maxRecords

        # print(pageStart, pageEnd, totPages, totRecords)

        if pageStart < totRecords:
            for i in range(pageStart, pageEnd+1):
                data.append(reqVideos[i])

        return render_template('response.html',data=data)
    
# using the or operator and querying the required result
@app.route("/searchData",methods=["GET"])
def searchData():
    title = request.args.get("title")
    description = int(request.args.get("description"))

    reqVideos1 = Videos.query.filter_by(videoTitle=title).order_by(Videos.publishedAt).all()
    reqVideos2 = Videos.query.filter_by(description=description).order_by(Videos.publishedAt).all()

    data = reqVideos1

    data.extend(reqVideos2)

    data = list(set(data))

    return render_template('response.html',data=data)

# using the multithreading here
thread = threading.Thread(target = saveData)
thread.start()

app.run(debug=True)

    