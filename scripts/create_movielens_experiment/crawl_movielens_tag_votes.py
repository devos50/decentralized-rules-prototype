"""
Collect the votes on tags from MovieLens and write them to tag_votes.csv.

tag_votes.csv is organised as follows:
- movie ID
- tag string
- number of upvotes
- number of downvotes
"""
import csv
import os
import random
import time

import requests

TAGS_PER_MOVIE_FILE = "data/tags_per_movie.csv"
TAG_VOTES_FILE = "data/tag_votes.csv"
movie_queue = []
completed_movies = set()

print("Load movie IDs...")
with open(TAGS_PER_MOVIE_FILE) as tags_per_movie_file:
    csv_reader = csv.reader(tags_per_movie_file)
    for row in csv_reader:
        movie_queue.append(row[0])

total_movies = len(movie_queue)

print("Load completed movies...")
with open(TAG_VOTES_FILE) as tag_votes_file:
    csv_reader = csv.reader(tag_votes_file)
    next(csv_reader)  # Skip header
    for row in csv_reader:
        completed_movies.add(row[0])

for completed_movie_id in completed_movies:
    if completed_movie_id in movie_queue:
        movie_queue.remove(completed_movie_id)

print("Total movies: %d, left in the queue: %d" % (total_movies, len(movie_queue)))


def write_tag_votes(json_response):
    movie_id = json_response["data"]["movieId"]
    print("Writing tags for movie %s" % movie_id)
    with open("data/tag_votes.csv", "a") as tag_votes_file:
        for tag in json_response["data"]["scoredTags"]:
            tag_str = tag["tag"].replace(",", " ")
            num_upvotes = int(tag["tagCountsViewModel"]["positive"])
            num_downvotes = int(tag["tagCountsViewModel"]["negative"]) + (int(tag["tagCountsViewModel"]["total"]) - int(tag["tagCountsViewModel"]["score"]))
            if num_upvotes == 0:
                num_upvotes = 1  # There should always be one user that created the tag

            tag_votes_file.write("%s,%s,%d,%d\n" % (movie_id, tag_str, num_upvotes, num_downvotes))


print("Start crawl...")
cookies = {'ml4_session': os.environ["ML4_SESSION"]}
for movie_id in movie_queue:
    print("Requesting tag votes for movie %s" % movie_id)
    response = requests.get("https://movielens.org/api/movies/%s/tags" % movie_id, cookies=cookies)
    json_response = response.json()
    if json_response["status"] == "success":
        write_tag_votes(json_response)
        delay = 10 + random.random() * 10
        print("Sleeping for %f sec" % delay)
        time.sleep(delay)
