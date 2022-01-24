library(ggplot2)

dat <- read.csv("../../../scripts/create_movielens_experiment/data/tag_votes.csv")
dat$score = dat$upvotes - dat$downvotes
dat_filtered <- dat[dat$score > -25,]
dat_filtered <- dat_filtered[dat_filtered$score < 25,]
dat_filtered <- dat_filtered[dat_filtered$score != 1,]

p <- ggplot(dat_filtered, aes(x=score)) +
     geom_histogram(bins=50) +
     xlab("Tag Score (upvotes - downvotes)") +
     ylab("Count") +
     theme_bw()

ggsave("../plots/movielens_tag_scores_histogram.pdf", p, width=4, height=3)
