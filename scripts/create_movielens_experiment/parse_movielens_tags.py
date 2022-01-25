"""
Gather various statistics from the Movielens tags dataset.
See https://grouplens.org/datasets/movielens/25m/
"""
import csv
from collections import defaultdict

TAGS_FILE = "/Users/martijndevos/Downloads/ml-25m/tags.csv"

tags_per_user = defaultdict(lambda: 0)
tags_per_movie = defaultdict(lambda: 0)
total_votes = 0

with open(TAGS_FILE) as tags_file:
    parsed_header = False
    csv_reader = csv.reader(tags_file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    next(csv_reader)

    for csv_line in csv_reader:
        user_id, movie_id, tag, timestamp = csv_line
        tags_per_user[user_id] += 1
        total_votes += 1
        tags_per_movie[movie_id] += 1

# Write data
print("Writing data...")
with open("data/tags_per_user.csv", "w") as out_file:
    out_file.write("user_id,num_tags\n")
    for user_id, num_tags in sorted(tags_per_user.items(), key=lambda x: x[1], reverse=True):
        out_file.write("%s,%s\n" % (user_id, num_tags))

with open("data/tags_per_movie.csv", "w") as out_file:
    out_file.write("movie_id,num_tags\n")
    for movie_id, num_tags in sorted(tags_per_movie.items(), key=lambda x: x[1], reverse=True):
        out_file.write("%s,%s\n" % (movie_id, num_tags))

print("Total votes: %d" % total_votes)
print("Unique users that tagged: %d" % len(tags_per_user))
print("Unique movies: %d" % len(tags_per_movie))
