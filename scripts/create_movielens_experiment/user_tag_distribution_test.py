# Playing around with discrete log-normal distributions
from collections import defaultdict

import numpy as np

SAMPLES = 1093360
MAX_X = 300
NUM_USERS = 14592

mu = 2.386474
sigma = 2.107494

tags_per_user = defaultdict(lambda: 0)

samples_taken = 0
while True:
    s = np.random.lognormal(mu, sigma, 1)
    if s[0] > MAX_X:
        continue

    samples_taken += 1
    if samples_taken == SAMPLES:
        break

    # Determine the lucky user
    bin_size = MAX_X / NUM_USERS
    user_id = int(s[0] / bin_size)
    tags_per_user[user_id] += 1

    if samples_taken % 100000 == 0:
        print("%d samples taken..." % samples_taken)

print(len(tags_per_user))

with open("data/user_tags_created_artificial.csv", "w") as out_file:
    out_file.write("user_id,num_tags\n")
    for user_id, num_tags in sorted(tags_per_user.items(), key=lambda x: x[1], reverse=True):
        out_file.write("%d,%d\n" % (user_id, num_tags))
