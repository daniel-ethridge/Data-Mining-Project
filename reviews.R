library("arules")

# TAKES A LONG TIME TO RUN
reviews = arules::read.transactions("./review_lists.csv",
                                    format = "basket",
                                    sep = ",", 
                                    quote = NULL,
                                    cols = NULL)

reviews_rules <- arules::apriori(reviews, parameter = list(support=0.007, 
                                                          confidence=0.28, minlen=3))

inspect(reviews_rules)
