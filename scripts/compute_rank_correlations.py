"""
Compute the Spearson Rank Correlation between multiple scenarios.
Requires a clean base scenario without attacks.
"""
import csv
import os

from scipy import stats


no_attack_scenario_dir = "../data/scenario_19_1"
attack_scenario_dirs = [("lower_reputation", "../data/scenario_19_1_1_lower_reputation")]


def read_tags(scenario_base_path):
    tags = {}
    with open(os.path.join(scenario_base_path, "tag_weights.csv")) as in_file:
        csv_reader = csv.reader(in_file)
        next(csv_reader)
        for row in csv_reader:
            user_id = int(row[0])
            content_id = int(row[1])
            tag = row[2]
            tag_weight = float(row[5])
            if user_id not in tags:
                tags[user_id] = {}
            if content_id not in tags[user_id]:
                tags[user_id][content_id] = []
            tags[user_id][content_id].append((tag, tag_weight))

    # Sort the tags by weight
    for user in tags:
        for content_id in tags[user]:
            tags[user][content_id] = sorted(tags[user][content_id], key=lambda x: x[1])

    return tags


with open("../data/spearman_correlations.csv", "w") as out_file:
    out_file.write("scenario,user_id,content_id,correlation\n")
    tags_no_attack = read_tags(no_attack_scenario_dir)
    for attack_name, attack_scenario_dir in attack_scenario_dirs:
        tags_attack = read_tags(attack_scenario_dir)

        for user in tags_no_attack:
            if user not in tags_attack:
                continue

            for content_id in tags_no_attack[user]:
                if content_id not in tags_attack[user]:
                    continue

                t_a = tags_no_attack[user][content_id]
                t_na = tags_attack[user][content_id]

                # Determine intersection
                res1 = [ele1 for ele1 in t_a for ele2 in t_na if ele1[0] == ele2[0]]
                res2 = [ele1 for ele1 in t_na for ele2 in t_a if ele1[0] == ele2[0]]
                if len(res1) < 3:
                    continue

                w1 = [tag[0] for tag in res1]
                w2 = [tag[0] for tag in res2]

                ranks1 = list(range(0, len(w1)))
                ranks2 = [w1.index(ele) for ele in w2]

                correlation = stats.spearmanr(ranks1, ranks2)

                out_file.write("%s,%d,%s,%f\n" % (attack_name, user, content_id, correlation[0]))
