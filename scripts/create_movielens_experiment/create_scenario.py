"""
Create a scenario for the evaluation of the tagging mechanism.
"""
import csv
import random

import numpy as np

NUM_HONEST_USERS = 20
NUM_SPAMMERS = 5
NUM_MOVIES = 100
TAKE_RANDOM_MOVIES = True  # If false, we will take the top X tagged movies
DURATION = 300  # Experiment duration in seconds
MAX_X = 300

# Parameters for the estimation of user tag creation/deletion behaviour
MU = 2.386474
SIGMA = 2.107494

popular_movie_ids = []
movie_ids_we_have_tags_for = set()
movies_to_include = []
min_max_tag_timestamps_per_movie = {}
experiment_start_time = 1E20
experiment_end_time = -1
votes_per_movie = {}
initial_tag_timestamps = {}
user_tag_creation = {}


def get_user_that_tagged(movie_id, tag, get_uniform_random=True):
    if get_uniform_random:
        return random.randint(0, NUM_HONEST_USERS)

    while True:
        s = np.random.lognormal(MU, SIGMA, 1)
        if s[0] > MAX_X:
            continue

        # Determine the lucky user
        bin_size = MAX_X / NUM_HONEST_USERS
        user_id = int(s[0] / bin_size)

        if user_id in user_tag_creation and (movie_id, tag) in user_tag_creation[user_id]:
            continue

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

# Create the scenario
tag_actions = []   # Tuple (timestamp, user_id, movie_id, tag, is_create)
for movie_id in movies_to_include:
    for tag, voting_info in votes_per_movie[movie_id].items():
        num_upvotes, num_downvotes = voting_info
        print("Considering tag %s with %d upvotes and %d downvotes" % (tag, num_upvotes, num_downvotes))

        # The sum of upvotes/downvotes cannot exceed the number of users
        if num_upvotes + num_downvotes > NUM_HONEST_USERS:
            continue  # Simply ignore this tag

        lowest_timestamp_for_create_tag = 1E20
        for ind in range(num_upvotes):
            if ind == 0:  # Initial creation - set it to the initial timestamp if available
                if (movie_id, tag) in initial_tag_timestamps:
                    tag_timestamp = initial_tag_timestamps[(movie_id, tag)]
                else:
                    # Initial timestamp if not available - it's random
                    tag_timestamp = random.randint(min_max_tag_timestamps_per_movie[movie_id][0], experiment_end_time)
                    initial_tag_timestamps[(movie_id, tag)] = tag_timestamp
            else:
                tag_timestamp = random.randint(initial_tag_timestamps[(movie_id, tag)], experiment_end_time)

            user_id = get_user_that_tagged(movie_id, tag, get_uniform_random=(ind == 0))
            tag_actions.append((tag_timestamp, user_id, movie_id, tag, True))
            set_user_tagged(user_id, movie_id, tag)
            if tag_timestamp < lowest_timestamp_for_create_tag:
                lowest_timestamp_for_create_tag = tag_timestamp

        for ind in range(num_downvotes):
            user_id = get_user_that_tagged(movie_id, tag)
            tag_timestamp = random.randint(lowest_timestamp_for_create_tag, experiment_end_time)
            tag_actions.append((tag_timestamp, user_id, movie_id, tag, False))
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

for user_id in range(NUM_HONEST_USERS, NUM_HONEST_USERS + NUM_SPAMMERS):
    tags_to_spam = random.sample(all_tags, int(len(all_tags)))
    for movie_id, tag in tags_to_spam:
        tag_timestamp = random.randint(initial_tag_timestamps[(movie_id, tag)], experiment_end_time)
        tag_actions.append((tag_timestamp, user_id, movie_id, tag, False))

tag_actions = sorted(tag_actions, key=lambda t: t[0])  # Sort on timestamp

# Write the scenario
with open("data/scenarios/tag_experiment_%d.scenario" % NUM_HONEST_USERS, "w") as scenario_file:
    for timestamp, user_id, movie_id, tag, is_create in tag_actions:
        relative_timestamp = timestamp - experiment_start_time
        scaled_timestamp = relative_timestamp / (experiment_end_time - experiment_start_time) * DURATION
        scenario_file.write("%f,%d,%s,%s,%d\n" % (scaled_timestamp, user_id, movie_id, tag, 1 if is_create else 0))
