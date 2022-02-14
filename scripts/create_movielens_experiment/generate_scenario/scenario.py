import csv
import os
import random
import shutil
from typing import List, Tuple, Dict

import numpy as np

from scripts.create_movielens_experiment.generate_scenario import BAD_TAG_THRESHOLD, MU, SIGMA, MAX_X
from scripts.create_movielens_experiment.generate_scenario.action import ScenarioAction
from scripts.create_movielens_experiment.generate_scenario.scenario_settings import ScenarioSettings
from scripts.create_movielens_experiment.generate_scenario.tag import Tag


class Scenario:

    def __init__(self, settings: ScenarioSettings):
        self.settings = settings
        self.actions = []
        self.popular_movie_ids = []
        self.min_max_tag_timestamps_per_movie = {}
        self.initial_tag_timestamps = {}
        self.movie_ids_we_have_tags_for = set()
        self.votes_per_movie = {}
        self.user_tag_creation = {}
        self.total_users = settings.num_honest_users + settings.num_bad_taggers
        self.tags_included_in_experiment = []
        self.movies_to_include = []
        self.tags_info: Dict[Tuple[str, str], Tag] = {}

        self.users_by_type = {
            "honest": list(range(settings.num_honest_users)),
            "bad_tagger": list(range(settings.num_honest_users, settings.num_honest_users + settings.num_bad_taggers))
        }

        self.experiment_start_time = 1E20
        self.experiment_end_time = -1

    def get_user_that_tagged(self, movie_id, tag, get_uniform_random=False):
        if get_uniform_random:
            return random.randint(0, self.settings.num_honest_users - 1)

        while True:
            s = np.random.lognormal(MU, SIGMA, 1)
            if s[0] > MAX_X:
                continue

            # Determine the lucky user
            bin_size = MAX_X / self.settings.num_honest_users
            user_id = int(s[0] / bin_size)

            if user_id in self.user_tag_creation and (movie_id, tag) in self.user_tag_creation[user_id]:
                continue  # This user already interacted with the tag.

            return user_id

    def set_user_tagged(self, user_id, movie_id, tag):
        if user_id not in self.user_tag_creation:
            self.user_tag_creation[user_id] = set()
        self.user_tag_creation[user_id].add((movie_id, tag))

    def load_data(self):
        """
        Load the required data to generate the experiment.
        """
        with open("../data/tags_per_movie.csv") as in_file:
            csv_reader = csv.reader(in_file)
            next(csv_reader)
            for row in csv_reader:
                self.popular_movie_ids.append(row[0])

        # Read the initial timestamps
        with open("../data/initial_tag_timestamp.csv") as in_file:
            csv_reader = csv.reader(in_file)
            next(csv_reader)
            for row in csv_reader:
                movie_id = row[0]
                tag = row[1]
                tag_timestamp = int(row[2])

                if movie_id not in self.min_max_tag_timestamps_per_movie:
                    self.min_max_tag_timestamps_per_movie[movie_id] = [1E20, -1]
                self.min_max_tag_timestamps_per_movie[movie_id][0] = min(self.min_max_tag_timestamps_per_movie[movie_id][0],
                                                                         tag_timestamp)
                self.min_max_tag_timestamps_per_movie[movie_id][1] = max(self.min_max_tag_timestamps_per_movie[movie_id][1],
                                                                         tag_timestamp)

                if (movie_id, tag) not in self.initial_tag_timestamps:
                    self.initial_tag_timestamps[(movie_id, tag)] = 1E20
                if tag_timestamp < self.initial_tag_timestamps[(movie_id, tag)]:
                    self.initial_tag_timestamps[(movie_id, tag)] = tag_timestamp

        # Store the votes on movies
        with open("../data/tag_votes.csv") as in_file:
            csv_reader = csv.reader(in_file)
            next(csv_reader)
            for row in csv_reader:
                movie_id = row[0]
                self.movie_ids_we_have_tags_for.add(movie_id)
                tag = row[1]
                if movie_id not in self.votes_per_movie:
                    self.votes_per_movie[movie_id] = {}
                self.votes_per_movie[movie_id][tag] = (int(row[2]), int(row[3]))

    def generate(self):
        """
        Generate the scenario and create the actions.
        """
        self.load_data()

        # Determine which movies to include
        if self.settings.sample_random_movies:
            self.movies_to_include = random.sample(sorted(list(self.movie_ids_we_have_tags_for)), self.settings.num_movies)
        else:
            self.movies_to_include = self.popular_movie_ids[:self.settings.num_movies]

        # Determine the experiment start/end times
        for movie_id in self.movies_to_include:
            min_time, max_time = self.min_max_tag_timestamps_per_movie[movie_id]
            if min_time < self.experiment_start_time:
                self.experiment_start_time = min_time
            if max_time > self.experiment_end_time:
                self.experiment_end_time = max_time

        print("Experiment start time: %d" % self.experiment_start_time)
        print("Experiment end time: %d" % self.experiment_end_time)

        # We now know which movies to include - create the scenario
        for movie_id in self.movies_to_include:
            for tag, voting_info in self.votes_per_movie[movie_id].items():
                num_upvotes, num_downvotes = voting_info

                # The sum of upvotes/downvotes cannot exceed the number of users
                if num_upvotes + num_downvotes > self.settings.num_honest_users:
                    continue  # Simply ignore this tag

                print("Considering tag %s with %d upvotes and %d downvotes" % (tag, num_upvotes, num_downvotes))

                lowest_timestamp_for_create_tag = 1E20
                for ind in range(num_upvotes):
                    if ind == 0:  # Initial creation - set it to the initial timestamp if available
                        if (movie_id, tag) in self.initial_tag_timestamps:
                            tag_timestamp = self.initial_tag_timestamps[(movie_id, tag)]
                        else:
                            # Initial timestamp if not available - it's random
                            tag_timestamp = random.randint(self.min_max_tag_timestamps_per_movie[movie_id][0],
                                                           self.experiment_end_time)
                            self.initial_tag_timestamps[(movie_id, tag)] = tag_timestamp

                        # Depending on how good/bad the tag is, assign an author
                        if (num_upvotes - num_downvotes) < BAD_TAG_THRESHOLD and self.settings.num_bad_taggers > 0:
                            user_id = random.choice(self.users_by_type["bad_tagger"])
                        else:
                            user_id = self.get_user_that_tagged(movie_id, tag, get_uniform_random=True)

                        self.tags_included_in_experiment.append((movie_id, tag, user_id, num_upvotes, num_downvotes))
                        self.tags_info[(movie_id, tag)] = Tag(movie_id, tag, user_id, set(), set())
                    else:
                        tag_timestamp = random.randint(self.initial_tag_timestamps[(movie_id, tag)], self.experiment_end_time)
                        user_id = self.get_user_that_tagged(movie_id, tag)
                        self.tags_info[(movie_id, tag)].upvotes.add(user_id)

                    action = ScenarioAction("create" if (ind == 0) else "vote", tag_timestamp, user_id, movie_id, tag, True)
                    self.actions.append(action)
                    self.set_user_tagged(user_id, movie_id, tag)
                    if tag_timestamp < lowest_timestamp_for_create_tag:
                        lowest_timestamp_for_create_tag = tag_timestamp

                for ind in range(num_downvotes):
                    user_id = self.get_user_that_tagged(movie_id, tag)
                    tag_timestamp = random.randint(lowest_timestamp_for_create_tag, self.experiment_end_time)
                    action = ScenarioAction("vote", tag_timestamp, user_id, movie_id, tag, False)
                    self.actions.append(action)
                    self.set_user_tagged(user_id, movie_id, tag)
                    self.tags_info[(movie_id, tag)].downvotes.add(user_id)

    def get_included_tags(self) -> List[Tuple[int, str]]:
        return [(tup[0], tup[1]) for tup in self.tags_included_in_experiment]

    def add_attack(self, profile):
        profile.apply(self)

    def write(self):
        """
        Write the scenario to the various files.
        """
        self.actions = sorted(self.actions, key=lambda a: a.timestamp)  # Sort on timestamp

        attack_mixes = []
        for user_type, user_ids in self.users_by_type.items():
            if user_type == "honest" or user_type == "bad_tagger":
                continue
            attack_mixes.append("%d_%s" % (len(user_ids), user_type))

        dir_name = "scenario_%d_%d" % (self.settings.num_honest_users, self.settings.num_bad_taggers)
        if attack_mixes:
            dir_name += "_" + "_".join(attack_mixes)
        dir_path = os.path.join("../data", "scenarios", dir_name)
        shutil.rmtree(dir_path, ignore_errors=True)
        os.mkdir(dir_path)

        with open(os.path.join(dir_path, "tag_votes.csv"), "w") as out_file:
            out_file.write("movie_id,tag,creator,upvotes,downvotes,\n")
            for info in self.tags_included_in_experiment:
                out_file.write("%s,%s,%d,%d,%d\n" % info)

        actions_per_user = {}
        for action in self.actions:
            if action.user_id not in actions_per_user:
                actions_per_user[action.user_id] = {}
            if action.command not in actions_per_user[action.user_id]:
                actions_per_user[action.user_id][action.command] = 0
            actions_per_user[action.user_id][action.command] += 1

        with open(os.path.join(dir_path, "users.csv"), "w") as out_file:
            out_file.write("user_id,user_type,tags_created,votes\n")
            for user_type, user_ids in self.users_by_type.items():
                for user_ind in user_ids:
                    tags_created = 0 if (
                                user_ind not in actions_per_user or "create" not in actions_per_user[user_ind]) else \
                    actions_per_user[user_ind]["create"]
                    votes = 0 if (user_ind not in actions_per_user or "vote" not in actions_per_user[user_ind]) else \
                    actions_per_user[user_ind]["vote"]
                    out_file.write("%d,%s,%d,%d\n" % (user_ind, user_type, tags_created, votes))

        with open(os.path.join(dir_path, "experiment.scenario"), "w") as scenario_file:
            for action in self.actions:
                relative_timestamp = action.timestamp - self.experiment_start_time
                scaled_timestamp = relative_timestamp / (self.experiment_end_time - self.experiment_start_time) * self.settings.duration
                scenario_file.write(
                    "%f,%s,%d,%s,%s,%d\n" % (scaled_timestamp, action.command, action.user_id, action.movie_id, action.tag, action.is_upvote))
