library(ggplot2)

dat <- read.csv("../../data/correlations.csv")
print(dat)

dat_filtered <- dat[dat$user_type == 0,]

p <- ggplot(dat_filtered, aes(x=correlation)) +
     geom_histogram(bin_width=0.1) +
     theme_bw()

ggsave("plots/correlations_histogram.pdf", p, width=4, height=3)
