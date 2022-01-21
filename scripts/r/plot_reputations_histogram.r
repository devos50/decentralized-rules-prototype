library(ggplot2)

dat <- read.csv("../../data/rules_reputations.csv")
print(dat)

dat_filtered <- dat[dat$user_type == 0,]

p <- ggplot(dat_filtered, aes(x=reputation)) +
     geom_histogram(bin_width=0.1) +
     xlim(c(-1, 1.1)) +
     theme_bw()

ggsave("plots/reputations_histogram.pdf", p, width=4, height=3)
