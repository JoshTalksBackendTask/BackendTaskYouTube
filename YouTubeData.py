from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import urllib.parse as parser
import re
import os
import pickle
from datetime import datetime, timedelta

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]

class YouTubeData():

    def __init__(self):
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "0"
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.client_secrets_file = "credentials1.json"
        self.creds = None

        self.youtube = self.authYouTube()
        self.nextPageToken = ""
        self.prevQuery = "official"
    

    def authYouTube(self):

        """
            It looks for the credentials.json file and tries to authenticate using that file, this will open your default browser the first time you run it, so you accept the permissions. After that, it'll save a new file token.pickle that contains the authorized credentials.
        """

        if os.path.exists("token.pickle"):
            with open("token.pickle","rb") as token:
                self.creds = pickle.load(token)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_file, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open("token.pickle","wb") as token:
                pickle.dump(self.creds,token)
            
        
        return build(self.api_service_name, self.api_version, credentials=self.creds)
    
    def queryVideos(self, query, maxRecords):
        
        """
            Queries all the videos with given specific query from the time user 
        """

        timeQuery = datetime.now()
        timeQuery = timeQuery.strftime("%Y-%m-%dT%H:%M:%S%z")+"Z"
        

        self.nextPageToken = "" if self.prevQuery != query else self.nextPageToken

        request = self.youtube.search().list(
                                            part="snippet", 
                                            maxResults=maxRecords,
                                            order="date",
                                            publishedAfter=timeQuery, 
                                            q=query,
                                            pageToken=self.nextPageToken,
                                            type="video"
                                        )

        res = request.execute()

        self.nextPageToken = res["nextPageToken"]
        
        return res

    
    def getVideoDetails(self, videoID):

        """
            It returns the complete details of the parsed video id
        """
        res = self.youtube.videos().list(part="statistics",id=videoID).execute()
        
        return res
    
    

if __name__=="__main__":

    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw&ab_channel=jawed"

    ytd = YouTubeData()

    res = ytd.queryVideos("surfing")

    # print(res)
    print(type(res))

    # parse video ID from URL    
    video_id = ytd.getVideoID(video_url)

    # make API call to get video info
    response = ytd.getVideoDetails(video_id)
    print(response,type(response))

    # print extracted video infos
    # ytd.printVideoInfo(response)
