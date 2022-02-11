library(ggplot2)
library(dplyr)

dat_honest <- read.csv("../../data/scenario_24_1_0/tag_weights.csv")

# Average the scores for all users
dat_honest <- dat_honest %>%
group_by(content_id, tag) %>%
summarise(avg_weight = mean(weight))
dat_honest <- as.data.frame(dat_honest)
dat_honest$group = "0"

print(head(dat_honest, n=20))

dat_attack <- read.csv("../../data/scenario_24_1_20/tag_weights.csv")

# Average the scores for all users
dat_attack <- dat_attack %>%
group_by(content_id, tag) %>%
summarise(avg_weight = mean(weight))
dat_attack <- as.data.frame(dat_attack)
dat_attack$group = "1"

print(head(dat_attack, n=20))

# Combine...
dat <- rbind(dat_honest, dat_attack)

# Read and include the experiment tag data
scenario_dat <- read.csv("../create_movielens_experiment/data/scenarios/scenario_24_1_0/tag_votes.csv")
scenario_dat$score <- scenario_dat$upvotes - scenario_dat$downvotes
colnames(scenario_dat)[1] <- "content_id"

merged_dat <- merge(dat, scenario_dat, by=c("content_id", "tag"))
#print(head(merged_dat))

# Plot
p <- ggplot(merged_dat, aes(x=avg_weight, y=score)) +
     geom_point(aes(shape=group, colour=group)) +
     xlab("Avg. tag weight") +
     ylab("Tag score") +
     xlim(c(-1, 1)) +
     labs(color="Scenario", shape="Scenario") +
     scale_shape_manual(breaks=c("0", "1"), values=c(16, 17), labels=c("No attack", "Spam")) +
     scale_colour_manual(breaks=c("0", "1"), values=c("darkgreen", "red"), labels=c("No attack", "Spam")) +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/actual_score_vs_rep_scatterplot.pdf", p, width=4, height=3)
