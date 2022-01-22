library(ggplot2)

dat <- read.csv("../../data/user_reputations.csv")

p <- ggplot(dat, aes(x=as.factor(user_id), y=as.factor(other_user_id), fill=reputation)) +
     geom_tile() +
     scale_fill_gradient(low="red", high="darkgreen") +
     ylab("Target user ID") +
     xlab("Source user ID") +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/user_reputations_heatmap.pdf", p, width=5, height=5)
