#!/usr/bin/env python
# -*- coding: utf-8 -*-

from vk_oauth import VK
import webbrowser
import os, sys, re
import requests
from transliterate import translit
import pdb

VK_ACCESS_TOKEN = VK.get_access_token()

def clean_search_query(query, ):
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

def download_audio(query, extra_params=None, succeded=None, failed=None):
	original_query = query
	query = clean_search_query(query)

	params = {"access_token": VK_ACCESS_TOKEN, "q":query, "count":10, "sort":2}
	if extra_params:
		params.update(extra_params)

	r = requests.get("https://api.vk.com/method/audio.search", params=params)
	response = r.json()
	# pdb.set_trace()

	error = response.get("error")
	if error != None:
		print "ERROR %d: %s" % (error["error_code"], error["error_msg"])
		if error["error_code"] == 6: # Too many requests per second
			print "retrying... %s" % (query)
			download_audio(query, succeded=succeded, failed=failed)
		elif error["error_code"] == 14: # Captcha needed
			c_sid = error["captcha_sid"]
			c_key = None
			
			webbrowser.open(error["captcha_img"])
			c_key = raw_input("captcha: ")

			print "retrying... %s" % (query)
			download_audio(query, extra_params={"captcha_sid":c_sid, "captcha_key":c_key}, succeded=succeded, failed=failed)
			
	else:
		max_items = 10
		items = response["response"]
		if len(items) > 0 and items[0] != 0:
			if len(items) < max_items:
				max_items = len(items)

			max_bitrate = 0
			max_bitrate_item = None
			for item in items[1:max_items]:
				size = int(requests.head(item["url"]).headers["content-length"])
				bitrate = size * 8 / 1000 / item["duration"]
				item["bitrate"] = bitrate
				if bitrate > max_bitrate:
					max_bitrate = bitrate
					max_bitrate_item = item

			item = max_bitrate_item
			# pdb.set_trace()

			filename = ("%s_-_%s" % (item["artist"], item["title"])).replace(" ", "_")
			filename = translit(filename, reversed=True)
			filename = re.sub(r'[^a-zA-Z0-9-_]','', filename)
			filename = filename + '.mp3'
			
			dirname = "files"
			if not os.path.exists(dirname):
				os.makedirs(dirname)

			filepath = os.path.join(dirname, filename)

			if succeded != None:
				succeded.append({"query":query.encode("utf-8"),
					"artist":item["artist"].encode("utf-8"),
					"title":item["title"].encode("utf-8"),
					"filename":filepath,
					"original_query":original_query.encode("utf-8")})
			
			print "succeded: %s" % (query)
			# os.system("curl -o %s %s" % (filepath, item["url"]))
			os.system("wget -c %s -O %s" % (item["url"], filepath))
		else:
			if failed != None:
				failed.append({"query":query.encode("utf-8"),
					"original_query":original_query.encode("utf-8")})
			print "failed: %s" % (query)

