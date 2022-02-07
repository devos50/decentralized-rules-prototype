"""
Create a scenario for the evaluation of the tagging mechanism.
"""
import csv
import os
import random
import shutil

import numpy as np

BAD_TAG_THRESHOLD = -3

NUM_HONEST_USERS = 10      # Users that create high-quality tags
NUM_BAD_TAGGER_USERS = 1   # Users that create low-quality tags
NUM_SPAMMERS = 1           # Users that vote -1 on all tags

NUM_MOVIES = 10
TAKE_RANDOM_MOVIES = True  # If false, we will take the top X tagged movies
DURATION = 900  # Experiment duration in seconds
MAX_X = 300

# Parameters for the estimation of user tag creation/deletion behaviour
MU = 2.386474
SIGMA = 2.107494

bad_tagger_ids = list(range(NUM_HONEST_USERS, NUM_HONEST_USERS + NUM_BAD_TAGGER_USERS))
popular_movie_ids = []
movie_ids_we_have_tags_for = set()
movies_to_include = []
min_max_tag_timestamps_per_movie = {}
experiment_start_time = 1E20
experiment_end_time = -1
votes_per_movie = {}
initial_tag_timestamps = {}
user_tag_creation = {}
tags_included_in_experiment = []


def get_user_that_tagged(movie_id, tag, get_uniform_random=False):
    if get_uniform_random:
        return random.randint(0, NUM_HONEST_USERS - 1)

    while True:
        s = np.random.lognormal(MU, SIGMA, 1)
        if s[0] > MAX_X:
            continue

        # Determine the lucky user
        bin_size = MAX_X / NUM_HONEST_USERS
        user_id = int(s[0] / bin_size)

        if user_id in user_tag_creation and (movie_id, tag) in user_tag_creation[user_id]:
            continue  # This user already interacted with the tag.

        return user_id


def set_user_tagged(user_id, movie_id, tag):
    if user_id not in user_tag_creation:
        user_tag_creation[user_id] = set()
    user_tag_creation[user_id].add((movie_id, tag))


# Get the list of popular movies
with open("data/tags_per_movie.csv") as in_file:
    csv_reader = csv.reader(in_file)
    next(csv_reader)
    for row in csv_reader:
        popular_movie_ids.append(row[0])


# Read the initial timestamps
with open("data/initial_tag_timestamp.csv") as in_file:
    csv_reader = csv.reader(in_file)
    next(csv_reader)
    for row in csv_reader:
        movie_id = row[0]
        tag = row[1]
        tag_timestamp = int(row[2])

        if movie_id not in min_max_tag_timestamps_per_movie:
            min_max_tag_timestamps_per_movie[movie_id] = [1E20, -1]
        min_max_tag_timestamps_per_movie[movie_id][0] = min(min_max_tag_timestamps_per_movie[movie_id][0], tag_timestamp)
        min_max_tag_timestamps_per_movie[movie_id][1] = max(min_max_tag_timestamps_per_movie[movie_id][1], tag_timestamp)

        if (movie_id, tag) not in initial_tag_timestamps:
            initial_tag_timestamps[(movie_id, tag)] = 1E20
        if tag_timestamp < initial_tag_timestamps[(movie_id, tag)]:
            initial_tag_timestamps[(movie_id, tag)] = tag_timestamp

# Store the votes on movies
with open("data/tag_votes.csv") as in_file:
    csv_reader = csv.reader(in_file)
    next(csv_reader)
    for row in csv_reader:
        movie_id = row[0]
        movie_ids_we_have_tags_for.add(movie_id)
        tag = row[1]
        if movie_id not in votes_per_movie:
            votes_per_movie[movie_id] = {}
        votes_per_movie[movie_id][tag] = (int(row[2]), int(row[3]))

# Determine which movies to include
if TAKE_RANDOM_MOVIES:
    movies_to_include = random.sample(list(movie_ids_we_have_tags_for), NUM_MOVIES)
else:
    movies_to_include = popular_movie_ids[:NUM_MOVIES]

# Determine the experiment start/end times
for movie_id in movies_to_include:
    min_time, max_time = min_max_tag_timestamps_per_movie[movie_id]
    if min_time < experiment_start_time:
        experiment_start_time = min_time
    if max_time > experiment_end_time:
        experiment_end_time = max_time


print("Experiment start time: %d" % experiment_start_time)
print("Experiment end time: %d" % experiment_end_time)

# We now know which movies to include - create the scenario
tag_actions = []   # Tuple (timestamp, user_id, movie_id, tag, is_create)
for movie_id in movies_to_include:
    for tag, voting_info in votes_per_movie[movie_id].items():
        num_upvotes, num_downvotes = voting_info

        # The sum of upvotes/downvotes cannot exceed the number of users
        if num_upvotes + num_downvotes > NUM_HONEST_USERS:
            continue  # Simply ignore this tag

        print("Considering tag %s with %d upvotes and %d downvotes" % (tag, num_upvotes, num_downvotes))

        lowest_timestamp_for_create_tag = 1E20
        for ind in range(num_upvotes):
            if ind == 0:  # Initial creation - set it to the initial timestamp if available
                if (movie_id, tag) in initial_tag_timestamps:
                    tag_timestamp = initial_tag_timestamps[(movie_id, tag)]
                else:
                    # Initial timestamp if not available - it's random
                    tag_timestamp = random.randint(min_max_tag_timestamps_per_movie[movie_id][0], experiment_end_time)
                    initial_tag_timestamps[(movie_id, tag)] = tag_timestamp

                # Depending on how good/bad the tag is, assign an author
                if (num_upvotes - num_downvotes) < BAD_TAG_THRESHOLD and NUM_BAD_TAGGER_USERS > 0:
                    user_id = random.choice(bad_tagger_ids)
                else:
                    user_id = get_user_that_tagged(movie_id, tag, get_uniform_random=True)

                tags_included_in_experiment.append((movie_id, tag, user_id, num_upvotes, num_downvotes))
            else:
                tag_timestamp = random.randint(initial_tag_timestamps[(movie_id, tag)], experiment_end_time)
                user_id = get_user_that_tagged(movie_id, tag)

            tag_actions.append((tag_timestamp, "create" if (ind == 0) else "vote", user_id, movie_id, tag, True))
            set_user_tagged(user_id, movie_id, tag)
            if tag_timestamp < lowest_timestamp_for_create_tag:
                lowest_timestamp_for_create_tag = tag_timestamp

        for ind in range(num_downvotes):
            user_id = get_user_that_tagged(movie_id, tag)
            tag_timestamp = random.randint(lowest_timestamp_for_create_tag, experiment_end_time)
            tag_actions.append((tag_timestamp, "vote", user_id, movie_id, tag, False))
            set_user_tagged(user_id, movie_id, tag)

# Include the actions of spammers
all_tags = []
for movie_id in movies_to_include:
    for tag, voting_info in votes_per_movie[movie_id].items():
        num_upvotes, num_downvotes = voting_info

        # The sum of upvotes/downvotes cannot exceed the number of users
        if num_upvotes + num_downvotes > NUM_HONEST_USERS:
            continue  # Simply ignore this tag

        all_tags.append((movie_id, tag))

for user_id in range(NUM_HONEST_USERS + NUM_BAD_TAGGER_USERS, NUM_HONEST_USERS + NUM_BAD_TAGGER_USERS + NUM_SPAMMERS):
    tags_to_spam = random.sample(all_tags, int(len(all_tags)))
    for movie_id, tag in tags_to_spam:
        tag_timestamp = random.randint(initial_tag_timestamps[(movie_id, tag)], experiment_end_time)
        tag_actions.append((tag_timestamp, "vote", user_id, movie_id, tag, False))

tag_actions = sorted(tag_actions, key=lambda t: t[0])  # Sort on timestamp

# Write the scenario information
dir_path = os.path.join("data", "scenarios", "scenario_%d" % NUM_HONEST_USERS)
shutil.rmtree(dir_path, ignore_errors=True)
os.mkdir(dir_path)

with open(os.path.join(dir_path, "tag_votes.csv"), "w") as out_file:
    out_file.write("movie_id,tag,creator,upvotes,downvotes,\n")
    for info in tags_included_in_experiment:
        out_file.write("%s,%s,%d,%d,%d\n" % info)

actions_per_user = {}
for timestamp, action, user_id, movie_id, tag, is_create in tag_actions:
    if user_id not in actions_per_user:
        actions_per_user[user_id] = {}
    if action not in actions_per_user[user_id]:
        actions_per_user[user_id][action] = 0
    actions_per_user[user_id][action] += 1

user_types = {}
for user_ind in range(0, NUM_HONEST_USERS):
    user_types[user_ind] = 0
for user_ind in range(NUM_HONEST_USERS, NUM_HONEST_USERS + NUM_BAD_TAGGER_USERS):
    user_types[user_ind] = 1
for user_ind in range(NUM_HONEST_USERS + NUM_BAD_TAGGER_USERS, NUM_HONEST_USERS + NUM_BAD_TAGGER_USERS + NUM_SPAMMERS):
    user_types[user_ind] = 2

with open(os.path.join(dir_path, "users.csv"), "w") as out_file:
    out_file.write("user_id,user_type,tags_created,votes\n")
    for user_ind in range(0, NUM_HONEST_USERS + NUM_BAD_TAGGER_USERS + NUM_SPAMMERS):
        tags_created = 0 if (user_ind not in actions_per_user or "create" not in actions_per_user[user_ind]) else actions_per_user[user_ind]["create"]
        votes = 0 if (user_ind not in actions_per_user or "vote" not in actions_per_user[user_ind]) else actions_per_user[user_ind]["vote"]
        out_file.write("%d,%d,%d,%d\n" % (user_ind, user_types[user_ind], tags_created, votes))

with open(os.path.join(dir_path, "experiment.scenario"), "w") as scenario_file:
    for timestamp, action, user_id, movie_id, tag, is_create in tag_actions:
        relative_timestamp = timestamp - experiment_start_time
        scaled_timestamp = relative_timestamp / (experiment_end_time - experiment_start_time) * DURATION
        scenario_file.write("%f,%s,%d,%s,%s,%d\n" % (scaled_timestamp, action, user_id, movie_id, tag, 1 if is_create else 0))
