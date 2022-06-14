library(ggplot2)

dat <- read.csv("../../../scripts/create_tribler_dataset/data/torrent_healths.csv")
dat_filtered <- dat[dat$seeders <= 5000,]

p <- ggplot(dat_filtered, aes(x=seeders)) +
     geom_histogram(bins=100) +
     ylab("Frequency") +
     xlab("Seeders") +
     scale_y_log10() +
     theme_bw()

ggsave("../plots/torrent_healths_seeders.pdf", p, width=7, height=3)