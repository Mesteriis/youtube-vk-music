#!/usr/bin/env python

import argparse
import os, sys
from vk_downloader import download_audio
import json
import pdb

parser = argparse.ArgumentParser(description='')
parser.add_argument('file_name', metavar='file_name', help='')
args = parser.parse_args()

SUCCEEDED = []
FAILED = []

def main():
	print "script started..."

	items = [line.strip() for line in open(args.file_name)]
	print "total songs: %s" % len(items)

	for index, item in enumerate(items):
		print "song: %d/%d (succeded: %d, failed:%d)" % (index, len(items), len(SUCCEEDED), len(FAILED))
		query = item.decode("utf-8")
		download_audio(query, succeded=SUCCEEDED, failed=FAILED)

	fp = open("report.json", "w")
	json.dump({"SUCCEEDED":{"count":len(SUCCEEDED),"items":SUCCEEDED},"FAILED":{"count":len(FAILED),"items":FAILED}},
		fp, indent=4, ensure_ascii=False)
	fp.close()

	print "done."

if __name__ == "__main__":
	main()