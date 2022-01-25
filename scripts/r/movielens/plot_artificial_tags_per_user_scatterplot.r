library(ggplot2)

dat <- read.csv("../../../scripts/create_movielens_experiment/data/user_tags_created_artificial.csv")
dat$idu <- as.numeric(row.names(dat))

p <- ggplot(dat, aes(x=idu, y=num_tags)) +
     geom_point(size=2, shape="+") +
     xlab("User ID") +
     ylab("Tag votes") +
     scale_x_log10() +
     scale_y_log10(limits=c(1, 10000)) +
     theme_bw()

ggsave("../plots/movielens_tags_per_user_artificial.pdf", p, width=4, height=3)
