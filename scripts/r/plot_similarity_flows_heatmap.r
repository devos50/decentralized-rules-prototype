library(ggplot2)

dat <- read.csv("../../data/scenario_24_1_10/similarity_flows.csv")

p <- ggplot(dat, aes(x=user_id, y=other_user_id, fill=transient_similarity)) +
     geom_tile() +
     scale_fill_gradientn(colours=c("red", "white", "darkgreen")) +
     ylab("Target user ID") +
     xlab("Source user ID") +
     scale_x_continuous(expand=c(0,0)) +
     scale_y_continuous(expand=c(0,0)) +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/similarity_flows_heatmap.pdf", p, width=5, height=5)
