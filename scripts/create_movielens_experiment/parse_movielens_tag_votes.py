"""
Parse the votes cast on MovieLens.
"""
import csv

TAG_VOTES_FILE = "data/tag_votes.csv"

total_upvotes = 0
total_downvotes = 0
tags_positive_score = 0
tags_negative_score = 0

with open(TAG_VOTES_FILE) as tag_votes_file:
    csv_reader = csv.reader(tag_votes_file)
    next(csv_reader)  # Ignore the header
    for row in csv_reader:
        print(row)
        total_upvotes += int(row[2])
        total_downvotes += int(row[3])
        score = int(row[2]) - int(row[3])
        if score > 0:
            tags_positive_score += 1
        elif score < 0:
            tags_negative_score += 1

print(total_upvotes)
print(total_downvotes)
print(tags_positive_score)
print(tags_negative_score)
