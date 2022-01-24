library(ggplot2)
library(dplyr)

dat <- read.csv("../../../scripts/create_movielens_experiment/data/tag_votes.csv")
dat$score = dat$upvotes - dat$downvotes
dat$upvotes <- dat$upvotes - 1  # Remove the upvote of the creator
dat_filtered <- dat[dat$score > -20,]
dat_filtered <- dat_filtered[dat_filtered$score <= 40,]
dat_filtered <- dat_filtered[!(dat_filtered$upvotes == 0 & dat_filtered$downvotes == 0),]

p <- ggplot(dat_filtered, aes(x=score)) +
     geom_histogram(bins=60) +
     xlab("Tag Score (upvotes - downvotes)") +
     ylab("Count") +
     theme_bw()

ggsave("../plots/movielens_tag_scores_histogram.pdf", p, width=4, height=3)
