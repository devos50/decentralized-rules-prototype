library(ggplot2)

dat <- read.csv("../../../scripts/create_tribler_dataset/data/torrent_healths.csv")

p <- ggplot(dat, aes(x=seeders, y=leechers)) +
     geom_bin2d(bins=100) +
     ylab("Seeders") +
     xlab("Leechers") +
     scale_fill_continuous(type = "viridis") +
     scale_x_log10() +
     scale_y_log10() +
     theme_bw()

ggsave("../plots/torrent_healths_scatter.pdf", p, width=7, height=7)