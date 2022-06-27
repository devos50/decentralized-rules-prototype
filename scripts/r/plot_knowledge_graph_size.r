library(ggplot2)
library(dplyr)

dat <- read.csv("../create_tribler_experiment/data/graph_size.csv")
dat$user <- as.factor(dat$user)

# Edges
p <- ggplot(dat, aes(x=time, y=edges, group=user, color=user)) +
     geom_line() +
     ylab("Num. edges") +
     xlab("Time into experiment (s.)") +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/kg_num_edges.pdf", p, width=6, height=3)


# Nodes
p <- ggplot(dat, aes(x=time, y=nodes, group=user, color=user)) +
     geom_line() +
     ylab("Num. nodes") +
     xlab("Time into experiment (s.)") +
     theme_bw() +
     theme(legend.position="bottom")

ggsave("plots/kg_num_nodes.pdf", p, width=6, height=3)
