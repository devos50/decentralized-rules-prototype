library(ggplot2)

dat <- read.csv("../../data/reputations.csv")
print(dat)

p <- ggplot(dat, aes(x=as.factor(user_id), y=reputation)) +
     geom_point(aes(shape=as.factor(rule_type), color=as.factor(rule_type))) +
     ylim(c(-1, 1)) +
     ylab("Rule reputation") +
     xlab("Honest user ID") +
     theme_bw() +
     theme(legend.position="bottom") +
     scale_shape_discrete(name="Rule type", labels=c("Accurate", "Spam")) +
     scale_color_manual(name="Rule type", labels=c("Accurate", "Spam"), values=c("green4", "red"))

ggsave("plots/reputations_scatterplot.pdf", p, width=5, height=3)
