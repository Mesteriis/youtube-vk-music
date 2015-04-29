#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os, sys
import requests
import json
from vk_downloader import download_audio

parser = argparse.ArgumentParser(description='Get track list from YouTube and search VK for mp3.')
parser.add_argument('playlist_ids', metavar='playlist_ids', nargs='+', help='YouTube playlists ids')
args = parser.parse_args()

SUCCEEDED = []
FAILED = []

MAX_RESULTS = 50

def get_songs(playlist_id, songs=None, start_index=1):
	url = "https://gdata.youtube.com/feeds/api/playlists/" + playlist_id
	params = {"start-index": start_index, "max-results": MAX_RESULTS, "v":2, "alt":"json"}

	r = requests.get(url, params=params)
	if r.status_code != requests.codes.ok:
		print "request not valid: %s" % r.url
		return []
	
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

def main():
	print "script started..."

	all_songs = []
	for playlist_id in args.playlist_ids:
		songs = get_songs(playlist_id)
		print "number of songs in playlist %s: %s" % (playlist_id, len(songs))
		all_songs.extend(songs)
	
	print "total songs: %s" % len(all_songs)

	# http://stackoverflow.com/questions/9427163/remove-duplicate-dict-in-list-in-python
	unique_songs = [dict(t) for t in set([tuple(d.items()) for d in all_songs])]
	print "unique songs: %s" % len(unique_songs)

	for index, song in enumerate(unique_songs):
		print "song: %d/%d (succeded: %d, failed:%d)" % (index, len(unique_songs), len(SUCCEEDED), len(FAILED))
		# query = song["artist"]+ " " + song["title"]
		query = song["title"]
		download_audio(query, succeded=SUCCEEDED, failed=FAILED)

	fp = open("report.json", "w")
	json.dump({"SUCCEEDED":{"count":len(SUCCEEDED), "items":SUCCEEDED}, "FAILED":{"count":len(FAILED), "items":FAILED}}, fp, indent=4, ensure_ascii=False)
	fp.close()

	print "done."

if __name__ == "__main__":
	main()