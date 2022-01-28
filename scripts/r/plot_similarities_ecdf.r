library(ggplot2)

dat <- read.csv("../../data/similarities.csv")
dat$idu <- as.numeric(row.names(dat))

p <- ggplot(dat, aes(x=similarity)) +
     stat_ecdf(geom="step") +
     ylab("ECDF") +
     xlab("Similarity") +
     theme_bw()

ggsave("plots/similarities_ecdf.pdf", p, width=5, height=5)
