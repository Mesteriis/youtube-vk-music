#!/usr/bin/python
# -*- coding: utf-8 -*-

from vk_oauth import VK 
import requests
import json
from urllib import urlencode
import webbrowser
import os
import sys
import re
from transliterate import translit

SUCCEEDED = []
FAILED = []

VK_ACCESS_TOKEN = VK.get_access_token()

MAX_RESULTS = 50

def get_songs(playlist_id, songs=None, start_index=1):
	url = "https://gdata.youtube.com/feeds/api/playlists/" + playlist_id
	params = {"start-index": start_index, "max-results": MAX_RESULTS, "v":2, "alt":"json"}

	r = requests.get(url, params=params)
	response = r.json()

	total_items_count = response["feed"]["openSearch$totalResults"]["$t"]

	if songs == None: songs = []

	if start_index+MAX_RESULTS < total_items_count:
		songs = get_songs(playlist_id, songs, start_index+MAX_RESULTS)
	
	for entry in response["feed"]["entry"]:
		title = entry["title"]["$t"]
		youtube_id = entry["media$group"]["yt$videoid"]["$t"]
		songs.append({"youtube_id":youtube_id, "title":title})

	return songs

def clean_search_query(query):
	# remove parentheses
	while query.find("(") != -1:
		l_index = query.find("(")
		r_index = query.find(")")
		query = query[:l_index] + query[r_index+1:]

	# remove dash
	query = query.replace("-", " ")

	# # remove everything after last dot
	# dot_r_index = query.rfind(".")
	# if dot_r_index != -1:
	# 	query = query[:dot_r_index]

	# remove quotes
	query = query.replace("\"", " ")
	query = query.replace("\'", " ")

	return query

def download_audio(query, extra_params=None):
	original_query = query
	query = clean_search_query(query)

	params = {"access_token": VK_ACCESS_TOKEN, "q":query, "count":1, "sort":2}
	if extra_params:
		params.update(extra_params)

	r = requests.get("https://api.vk.com/method/audio.search", params=params)
	response = r.json()

	error = response.get("error")
	if error != None:
		print "ERROR %d: %s" % (error["error_code"], error["error_msg"])
		if error["error_code"] == 6: # Too many requests per second
			print "retrying... %s" % (query)
			download_audio(query)
		elif error["error_code"] == 14: # Captcha needed
			c_sid = error["captcha_sid"]
			c_key = None
			
			webbrowser.open(error["captcha_img"])
			c_key = raw_input("captcha: ")

			print "retrying... %s" % (query)
			download_audio(query, extra_params={"captcha_sid":c_sid, "captcha_key":c_key})
			
	else:
		items = response["response"][1:]
		if len(items) > 0:
			item = items[0]
			filename = ("%s_-_%s" % (item["artist"], item["title"])).replace(" ", "_")
			filename = translit(filename, reversed=True)
			filename = re.sub(r'[^a-zA-Z0-9-_]','', filename)
			filename = filename + '.mp3'
			
			dirname = "files"
			if not os.path.exists(dirname):
				os.makedirs(dirname)

			filepath = os.path.join(dirname, filename)

			SUCCEEDED.append({"query":query.encode("utf-8"), 
								"artist":item["artist"].encode("utf-8"), 
								"title":item["title"].encode("utf-8"), 
								"filename":filepath,
								"original_query":original_query.encode("utf-8")})
			
			print "succeded: %s" % (query)
			# os.system("curl -o %s %s" % (filepath, item["url"]))
			os.system("wget -c %s -O %s" % (item["url"], filepath))
		else:
			FAILED.append({"query":query.encode("utf-8"), 
							"original_query":original_query.encode("utf-8")})
			print "failed: %s" % (query)

def main():
	print "script started..."

	all_songs = []
	playlist_ids = ["PLsLh1_TkoVPjDo8oollQLV3HvpzEW99sz", "PLkdRFcfZIhm8AQ2TjmmfS6NLUoMBxWch6"]
	# playlist_ids = ["PLF4AB437801A6E842"]

	for playlist_id in playlist_ids:
		songs = get_songs(playlist_id)
		print "number of songs in playlist %s: %s" % (playlist_id, len(songs))
		all_songs.extend(songs)
	
	print "total songs: %s" % len(all_songs)

	# http://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python
	unique_songs = [dict(t) for t in set([tuple(d.items()) for d in all_songs])]
	print "unique songs: %s" % len(unique_songs)

	for index, song in enumerate(unique_songs):
		print "song: %d/%d (succeded: %d, failed:%d)" % (index, len(unique_songs), len(SUCCEEDED), len(FAILED))
		download_audio(song["title"])

	fp = open("report.json", "w")
	json.dump({"SUCCEEDED":{"count":len(SUCCEEDED), "items":SUCCEEDED}, "FAILED":{"count":len(FAILED), "items":FAILED}}, fp, indent=4, ensure_ascii=False)
	fp.close()

	print "done."

if __name__ == "__main__":
	main()