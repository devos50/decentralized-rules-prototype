import os
import random
import shutil
from asyncio import sleep, get_event_loop, ensure_future
from typing import Dict, List, Set

import networkx as nx

from core import GENESIS_HASH
from core.content import Content
from core.rule import Rule, RuleType
from core.tag import Tag
from core.user import User, UserType
from core.vote import Vote
from simulation.scenario import Scenario, ScenarioAction
from simulation.settings import RuleCoverageDistribution, ContentPopularityDistribution

random.seed(42)


class Experiment:

    def __init__(self, settings):
        self.settings = settings
        self.rules = []
        self.content = []
        self.content_popularity = {}
        self.users: List[User] = []
        self.users_by_type: Dict[UserType: List[User]] = {}
        self.round = 0
        self.scenario = None

        # We keep track of the tags that are inaccurate and should be classified as such by end users.
        # Only used for experimental evaluation. In a deployed system, this information is not available.
        self.inaccurate_tags: Set[int] = set()

        # For post-experiment processing
        self.rules_reputation_per_round = {}
        self.tags_reputation_per_round = {}
        self.user_reputation_per_round = {}

        if settings.scenario_dir:
            self.scenario = Scenario(settings.scenario_dir)
            self.scenario.parse()

    def setup_scenario(self):
        # Create the users
        for user_type, users in self.scenario.users_by_type.items():
            for user_ind in users:
                user = User("%d" % user_ind, user_type=UserType(user_type))
                self.users.append(user)

        # Schedule the scenario actions
        loop = get_event_loop()
        for action in self.scenario.actions:
            loop.call_at(action.timestamp, lambda a=action: self.execute_user_action(a))

    def execute_user_action(self, action: ScenarioAction):
        user = self.get_user_by_id(action.user_id)
        if action.command == "create":
            tag = user.create_tag(action.movie_id, action.tag)

            # Other users that are going to vote on this tag do not have the required tag in their database.
            # The gossip algorithm does not guarantee that users receive it the moment their vote is scheduled.
            # Therefore, we proactively share it with users that are going to vote on this tag.
            linked_votes = user.trust_db.select_vote_dag_tips()
            vote = Vote(hash(user), tag.cid, tag.name, True, tag.authors, tag.rules, linked_votes)
            for other_action in self.scenario.actions:
                if other_action.command == "vote" and other_action.movie_id == action.movie_id and other_action.tag == action.tag:
                    other_user = self.get_user_by_id(other_action.user_id)
                    #print("Sharing tag %s with %s" % (tag, other_user))
                    other_user.process_incoming_vote(vote)

            # Also give this tag to the spammers
            if 2 in self.scenario.users_by_type:
                for user_id in self.scenario.users_by_type[2]:
                    other_user = self.get_user_by_id(user_id)
                    other_user.process_incoming_vote(vote)

        elif action.command == "vote":
            tag = user.tags_db.get_tag(hash((action.movie_id, action.tag)))
            assert tag, "Tag (%s, %s) should exist in the database of %s!" % (action.movie_id, action.tag, user)
            user.vote(tag, action.is_upvote)

    def get_user_by_id(self, user_id: int):
        for user in self.users:
            if hash(user) == user_id:
                return user
        return None

    def get_rule_by_id(self, rule_id):
        for rule in self.rules:
            if rule.rule_id == rule_id:
                return rule
        return None

    def create_rules(self):
        # Create honest rules
        for rule_ind in range(1, self.settings.num_honest_rules + 1):
            # Randomly pick a honest user that has created the rule
            rule_author = random.choice(self.users_by_type[UserType.HONEST])

            coverage = self.settings.rule_coverage
            if self.settings.rule_coverage_distribution == RuleCoverageDistribution.RANDOM_UNIFORM:
                coverage = random.random()

            rule = Rule(hash(rule_author), rule_ind, "Tag %d" % rule_ind, coverage=coverage, error_rate=self.settings.rule_error_rate)
            print("%s creates rule %s with coverage %f" % (rule_author, rule.rule_id, rule.coverage))
            rule.determine_applicable_content(self.settings.num_content_items)
            self.rules.append(rule)

            # Update the inaccurate tags
            for invalid_content_id in rule.applicable_content_ids_incorrect:
                tag_hash = hash((invalid_content_id, rule.output_tag))
                self.inaccurate_tags.add(tag_hash)

        # TODO fix this
        # Have each spam rule promotor create a spam rule
        # for rule_ind, adversary in enumerate(self.users_by_type[UserType.PROMOTE_SPAM_RULES]):
        #     rule = Rule(hash(adversary), len(self.rules) + 1, "Spam %d" % (rule_ind + 1), coverage=1, error_rate=1, rule_type=RuleType.SPAM)
        #     rule.determine_applicable_content(self.settings.num_content_items)
        #     self.rules.append(rule)

    def create_content(self):
        """
        Prepare content and determine the popularity of content, according to some distribution.
        """
        self.content = [ind for ind in range(self.settings.num_content_items)]

        zipf_denom = 0
        if self.settings.content_popularity_distribution == ContentPopularityDistribution.ZIPF:
            for content_ind in range(self.settings.num_content_items):
                zipf_denom += 1 / ((content_ind + 1) ** self.settings.zipf_exponent)

        for content_ind in range(self.settings.num_content_items):
            if self.settings.content_popularity_distribution == ContentPopularityDistribution.FIXED:
                self.content_popularity[content_ind] = 1 / self.settings.num_content_items
            elif self.settings.content_popularity_distribution == ContentPopularityDistribution.ZIPF:
                self.content_popularity[content_ind] = (1 / ((content_ind + 1) ** self.settings.zipf_exponent)) / zipf_denom

    def create_users(self):
        # Create users with different profiles
        for user_type, user_num in self.settings.num_users.items():
            for user_ind in range(len(self.users) + 1, len(self.users) + user_num + 1):
                user = User("%d" % user_ind, user_type=user_type)

                if user_type == UserType.HONEST:
                    content_of_user = random.sample(self.content, int(len(self.content) * self.settings.content_availability))
                    for content_item in content_of_user:
                        user.content_db.add_content(Content("%d" % content_item, self.content_popularity[content_item]))
                else:
                    # Adversarial users have all content.
                    for content_item in self.content:
                        user.content_db.add_content(Content("%d" % content_item, self.content_popularity[content_item]))

                self.users.append(user)
                if user.type not in self.users_by_type:
                    self.users_by_type[user.type] = []
                self.users_by_type[user.type].append(user)

        # Create rules
        self.create_rules()

        # Share and apply rules
        for user in self.users:
            user_rules = [rule.get_copy() for rule in self.rules]
            user.rules_db.add_rules(user_rules)
            user.apply_rules_to_content()

        # Create tags and share them with other users (to bootstrap the network)
        for user in self.users:
            created_tags = self.create_tags(user)
            for other_user in self.users:
                if user == other_user:
                    continue

                for tag in created_tags:
                    content = other_user.content_db.get_content(tag.cid)
                    if content:
                        added_tag = content.add_tag(tag.name, author_id=hash(user))
                        other_user.tags_db.add_tag(added_tag)

        # Create votes
        for user in self.users:
            self.create_votes(user)

    def cast_honest_user_vote(self, user, tag_to_vote_on: Tag):
        # Check if we already voted on this tag
        already_cast = False
        if tag_to_vote_on.cid in user.votes_db.votes_for_content:
            for vote in user.votes_db.votes_for_content[tag_to_vote_on.cid]:
                if tag_to_vote_on.name == vote.tag and vote.user_id == hash(user):
                    already_cast = True
                    break

        if already_cast:
            return

        # Downvote if the tag is inaccurate
        vote = True
        if hash(tag_to_vote_on) in self.inaccurate_tags:
            vote = False

        # Users sometimes vote wrong - if so, we invert the vote
        if random.random() < self.settings.user_vote_error_rate:
            print("User %s misvotes on tag %s (vote: %s)!" % (user, tag_to_vote_on.name, "-1" if vote else "+1"))
            vote = not vote

        vote_num = 1 if vote else -1
        print("%s votes %s%d on %s (cid: %s, rules: %s, authors: %s)" % (user, "+" if vote else "", vote_num,
                                                                         tag_to_vote_on.name, tag_to_vote_on.cid,
                                                                         tag_to_vote_on.rules, tag_to_vote_on.authors))
        user.vote(tag_to_vote_on, vote)

    def create_tags(self, user: User) -> List[Tag]:
        """
        Have the specified user create some initial tags.
        """
        created_tags: List[Tag] = []
        if user.type == UserType.HONEST:
            # TODO with a uniform distribution of content
            all_content = list(user.content_db.get_all_content())
            # TODO assume that each content item receives one tag
            num_items_to_tag = min(len(all_content), int(len(all_content) * self.settings.initial_tags_created_per_user))
            content_to_tag = random.sample(all_content, num_items_to_tag)
            for content in content_to_tag:
                tag_id = hash(user) * 10000 + hash(content)
                tag = user.tag(content, "Tag %d" % tag_id)
                created_tags.append(tag)
        elif user.type == UserType.TAG_SPAMMER:
            # Spammers create inaccurate tags on all content they find
            for content in user.content_db.get_all_content():
                tag_id = hash(user) * 10000 + hash(content)
                tag = user.tag(content, "Tag %d" % tag_id)
                created_tags.append(tag)

                self.inaccurate_tags.add(hash(tag))

        return created_tags

    def create_votes(self, user):
        """
        Create votes for the specified user
        """
        print("Creating votes for %s" % user)
        num_votes = 0

        if user.type == UserType.HONEST:
            rules_created = user.rules_db.get_rule_ids_created_by_user(hash(user))

            # We will take a subset of the content and cast votes
            all_content = list(user.content_db.get_all_content())
            content_to_vote_on = random.sample(all_content, int(len(all_content) * self.settings.initial_user_engagement))
            for content in content_to_vote_on:
                for tag in content.tags:
                    if hash(user) not in tag.authors and not set(rules_created).intersection(tag.rules):
                        # Only upvote the tags/rules created by other users.
                        self.cast_honest_user_vote(user, tag)
                        num_votes += 1
        elif user.type == UserType.RANDOM_VOTES:
            # We simply vote randomly
            for content_item in user.content_db.get_all_content():
                for tag in content_item.tags:
                    user.vote(tag, bool(random.randint(0, 1)))
                    num_votes += 1
        elif user.type == UserType.PROMOTE_SPAM_RULES:
            # Vote honestly for accurate rules to gain goodwill with others, but promote bad rules
            for content_item in user.content_db.get_all_content():
                for tag in content_item.tags:
                    # Is this tag generated by a rule that is bad? If so, promote it. Otherwise, vote honestly.
                    generated_by_spam_rule = False
                    honest_vote = False
                    for rule_id in tag.rules:
                        rule = user.rules_db.get_rule(rule_id)
                        if rule.type == RuleType.SPAM:
                            generated_by_spam_rule = True

                        if hash(tag.cid) in rule.applicable_content_ids_correct:
                            honest_vote = True
                            break

                    if generated_by_spam_rule:
                        user.vote(tag, True)
                    else:
                        # Vote honestly
                        user.vote(tag, honest_vote)
                    num_votes += 1

        print("Created %d votes for user %s" % (num_votes, user))

    def connect_users(self):
        # Create a strongly connected graph
        for user_a in self.users:
            for user_b in self.users:
                if user_a == user_b:
                    continue
                user_a.connect(user_b)

    def write_similarity_graph(self):
        G = nx.DiGraph()
        for user in self.users:
            if not G.has_node(hash(user)):
                G.add_node(hash(user), type=user.type, color="red" if user.type != UserType.HONEST else "black")

            if user.type != UserType.HONEST:
                continue  # We don't care about the outgoing trust edges of adversaries

            if hash(user) not in user.trust_db.similarity_scores:
                print("No information on %s to write similarity graph" % user)
                continue

            for to_user_id, similarity in user.trust_db.max_flows.items():
                if to_user_id == hash(user):
                    continue  # Do not add edges to yourself
                if not G.has_node(to_user_id):
                    other_user = self.get_user_by_id(to_user_id)
                    G.add_node(to_user_id, type=user.type,
                               color="red" if other_user.type != UserType.HONEST else "black")
                edge_color = "black"
                if similarity < -0.5:
                    edge_color = "red"
                elif similarity > 0.5:
                    edge_color = "darkgreen"

                line_thick = max(0.2, abs(similarity) * 1.5)

                G.add_edge(hash(user), to_user_id, weight=similarity, color=edge_color, penwidth=line_thick)

        nx.nx_pydot.write_dot(G, os.path.join("data", self.scenario.scenario_name, "similarity_flows.dot"))

    def write_similarities(self):
        with open(os.path.join("data", self.scenario.scenario_name, "similarities.csv"), "w") as similarities_file:
            similarities_file.write("user_type,user_id,other_user_id,similarity\n")
            for user in self.users:
                if hash(user) not in user.trust_db.similarity_scores:
                    print("No information on %s to write similarity scores" % user)
                    continue

                for to_user_id, similarity in user.trust_db.similarity_scores[hash(user)].items():
                    similarities_file.write(
                        "%s,%s,%s,%.3f\n" % (user.type.value, hash(user), to_user_id, similarity))

    def write_similarity_flows(self):
        with open(os.path.join("data", self.scenario.scenario_name, "similarity_flows.csv"), "w") as similarity_flows_file:
            similarity_flows_file.write("user_type,user_id,other_user_id,transient_similarity\n")
            for user in self.users:
                for to_user_id, similarity_flow in user.trust_db.max_flows.items():
                    similarity_flows_file.write(
                        "%s,%s,%s,%.3f\n" % (user.type.value, hash(user), to_user_id, similarity_flow))

    def write_reputations(self):
        # Write the reputation of tags
        with open(os.path.join("data", self.scenario.scenario_name, "tag_reputations.csv"), "w") as reputations_file:
            reputations_file.write("round,user_id,tag_id,is_accurate,reputation\n")
            for round in self.tags_reputation_per_round:
                for user_id in self.tags_reputation_per_round[round]:
                    user = self.get_user_by_id(user_id)
                    if user.type != UserType.HONEST:
                        continue
                    for tag_id in self.tags_reputation_per_round[round][user_id]:
                        is_inaccurate = tag_id in self.inaccurate_tags
                        reputations_file.write(
                            "%d,%s,%d,%d,%.3f\n" % (round, user_id, tag_id, 0 if is_inaccurate else 1, self.tags_reputation_per_round[round][user_id][tag_id]))

        # Write the reputation of users
        with open(os.path.join("data", self.scenario.scenario_name, "user_reputations.csv"), "w") as reputations_file:
            reputations_file.write("round,user_type,other_user_type,user_id,other_user_id,reputation\n")
            for round in self.user_reputation_per_round:
                for user_id in self.user_reputation_per_round[round]:
                    user = self.get_user_by_id(user_id)
                    if user.type != UserType.HONEST:
                        continue
                    for other_user_id in self.user_reputation_per_round[round][user_id]:
                        other_user = self.get_user_by_id(other_user_id)
                        reputations_file.write(
                            "%d,%s,%s,%s,%s,%.3f\n" % (round, user.type.value, other_user.type.value, user_id, other_user_id, self.user_reputation_per_round[round][user_id][other_user_id]))

        # Write the reputation of rules
        with open(os.path.join("data", self.scenario.scenario_name, "rules_reputations.csv"), "w") as reputations_file:
            reputations_file.write("round,user_id,rule_id,rule_type,reputation\n")
            for round in self.rules_reputation_per_round:
                for user_id in self.rules_reputation_per_round[round]:
                    user = self.get_user_by_id(user_id)
                    if user.type != UserType.HONEST:
                        continue
                    for rule_id in self.rules_reputation_per_round[round][user_id]:
                        rule = self.get_rule_by_id(rule_id)
                        reputations_file.write(
                            "%d,%s,%s,%d,%.3f\n" % (round, user_id, rule.rule_id, rule.type.value,
                                                    self.rules_reputation_per_round[round][user_id][rule_id]))

    def write_tags(self):
        """
        For each user, write all the tags in the database with the appropriate weights.
        """
        with open(os.path.join("data", self.scenario.scenario_name, "tags.csv"), "w") as tags_file:
            tags_file.write("user_id,content_id,tag,is_accurate\n")
            for user in self.users:
                created_tags = user.tags_db.get_tags_created_by_user(hash(user))
                for tag in created_tags:
                    is_inaccurate = hash(tag) in self.inaccurate_tags
                    tags_file.write("%d,%s,%s,%d\n" % (hash(user), tag.cid, tag.name, 0 if is_inaccurate else 1))

        with open(os.path.join("data", self.scenario.scenario_name, "tag_weights.csv"), "w") as tags_file:
            tags_file.write("user_id,content_id,tag,is_accurate,reputation,weight\n")
            for user in self.users:
                if user.type != UserType.HONEST:
                    continue

                for content in user.content_db.get_all_content():
                    for tag in content.tags:
                        is_inaccurate = hash(tag) in self.inaccurate_tags
                        tags_file.write("%d,%s,%s,%d,%f,%f\n" % (hash(user), hash(content), tag.name, 0 if is_inaccurate else 1, tag.reputation_score, tag.weight))

    def write_votes(self):
        """
        For every user, write their votes.
        """
        with open(os.path.join("data", self.scenario.scenario_name, "votes.csv"), "w") as votes_file:
            votes_file.write("user_id,content_id,tag,vote\n")
            for user in self.users:
                for vote in user.votes_db.get_votes_for_user(hash(user)):
                    votes_file.write("%d,%s,%s,%d\n" % (hash(user), vote.cid, vote.tag, 1 if vote.is_accurate else -1))

    def write_vote_dag(self):
        user = self.get_user_by_id(0)
        user.votes_db.vote_dag.nodes[GENESIS_HASH]["color"] = "green"
        user.votes_db.vote_dag.nodes[GENESIS_HASH]["label"] = "gen"
        for node in user.votes_db.vote_dag.nodes:
            if node == GENESIS_HASH:
                continue
            vote = user.votes_db.votes[node]
            user_vote = self.get_user_by_id(vote.user_id)
            user.votes_db.vote_dag.nodes[node]["label"] = user_vote.identifier

            if user_vote.type != UserType.HONEST:
                user.votes_db.vote_dag.nodes[node]["color"] = "red"

        nx.nx_pydot.write_dot(user.votes_db.vote_dag, os.path.join("data", "vote_dag.dot"))

    async def run(self):
        if self.settings.scenario_dir:
            self.setup_scenario()
        else:
            self.create_content()
            self.create_users()

        self.connect_users()

        # Start the routine for exchanging votes
        loop = get_event_loop()
        for user in self.users:
            loop.call_later(random.randint(0, self.settings.exchange_interval),
                            lambda u=user: ensure_future(u.start_vote_exchange(self.settings.exchange_interval,
                                                                               self.settings.gossip_batch_size)))

        await sleep(self.settings.duration)

        self.recompute_all_reputations()
        self.write_data()

        loop = get_event_loop()
        loop.stop()

    def recompute_all_reputations(self):
        self.rules_reputation_per_round[self.round] = {}
        self.user_reputation_per_round[self.round] = {}
        self.tags_reputation_per_round[self.round] = {}
        for user in self.users:
            print("Recomputing all reputations for %s" % user)
            user.recompute_reputations()
            user.trust_db.compute_graph_influences()
            self.rules_reputation_per_round[self.round][hash(user)] = {}
            self.user_reputation_per_round[self.round][hash(user)] = {}
            self.tags_reputation_per_round[self.round][hash(user)] = {}
            for rule in user.rules_db.get_all_rules():
                print("Reputation rule %s: %f" % (hash(rule), rule.reputation_score))
                self.rules_reputation_per_round[self.round][hash(user)][rule.rule_id] = rule.reputation_score
            for other_user_id, user_rep in user.trust_db.user_reputations.items():
                print("Reputation of user %s: %f" % (other_user_id, user_rep))
                self.user_reputation_per_round[self.round][hash(user)][other_user_id] = user_rep
            for tag in user.tags_db.get_all_tags():
                #print("Reputation tag %s: %f" % (hash(tag), tag.reputation_score))
                self.tags_reputation_per_round[self.round][hash(user)][hash(tag)] = tag.reputation_score

    def write_data(self):
        data_dir_path = os.path.join("data", self.scenario.scenario_name)
        shutil.rmtree(data_dir_path, ignore_errors=True)
        os.mkdir(data_dir_path)

        self.write_similarity_graph()
        self.write_similarities()
        self.write_similarity_flows()
        self.write_reputations()
        self.write_tags()
        self.write_votes()
        self.write_vote_dag()
