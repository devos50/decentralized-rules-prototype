library(ggplot2)

dat <- read.csv("../../data/tags.csv")
print(dat)

p <- ggplot(dat, aes(x=as.factor(user_id), y=weight)) +
     geom_point(aes(shape=as.factor(is_accurate), color=as.factor(is_accurate))) +
     ylim(c(-1, 1)) +
     ylab("Tag weight") +
     xlab("Honest user ID") +
     theme_bw() +
     theme(legend.position="bottom") +
     scale_shape_discrete(name="Tag type", breaks=c(1, 0), labels=c("Accurate", "Inaccurate")) +
     scale_color_manual(name="Tag type", breaks=c(1, 0), labels=c("Accurate", "Inaccurate"), values=c("green4", "red"))

ggsave("plots/tag_weights_scatterplot.pdf", p, width=5, height=3)
