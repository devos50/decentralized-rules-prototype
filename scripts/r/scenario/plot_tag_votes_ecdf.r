library(ggplot2)
library(dplyr)

dat <- read.csv("../../../scripts/create_movielens_experiment/data/scenarios/scenario_24/tag_votes.csv")
dat$score = dat$upvotes - dat$downvotes
dat$upvotes <- dat$upvotes - 1  # Remove the upvote of the creator

p <- ggplot(dat, aes(x=score)) +
     stat_ecdf() +
     xlab("Tag Score (upvotes - downvotes)") +
     ylab("ECDF") +
     theme_bw()

ggsave("../plots/scenario_tag_scores_ecdf.pdf", p, width=4, height=3)
