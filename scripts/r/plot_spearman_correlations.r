library(ggplot2)

dat <- read.csv("../../data/spearman_correlations.csv")
print(mean(dat$correlation))

p <- ggplot(dat, aes(x=factor(user_id), y=correlation)) +
     geom_boxplot() +
     ylab("Spearman Rank Correlation") +
     xlab("User ID") +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/spearman_correlations.pdf", p, width=7, height=3)
