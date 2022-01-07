library(ggplot2)
library(dplyr)

dat <- read.csv("../../data/reputations.csv")
dat$rule_id <- as.factor(dat$rule_id)

# Average the results
dat <- dat %>%
group_by(round,rule_id,rule_type) %>%
summarise(rep_mean = mean(reputation), sd=sd(reputation))

print(dat, n=300)

p <- ggplot(dat, aes(x=round, y=rep_mean, color=rule_id)) +
     geom_point() +
     geom_line() +
     ylim(c(-1, 1)) +
     ylab("Rule Reputation") +
     xlab("Round") +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/reputations_per_round.pdf", p, width=6, height=3)
