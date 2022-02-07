library(ggplot2)

dat <- read.csv("../../data/user_reputations.csv")

p <- ggplot(dat, aes(x=user_id, y=other_user_id, fill=reputation)) +
     geom_tile() +
     scale_fill_gradientn(colours=c("red", "white", "darkgreen"), limits=c(-1, 1)) +
     ylab("Target user ID") +
     xlab("Source user ID") +
     scale_x_continuous(expand=c(0,0)) +
     scale_y_continuous(expand=c(0,0)) +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/user_reputations_heatmap.pdf", p, width=5, height=5)
