import pandas as pd
import csv
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt


pd.set_option("display.max_columns", None)
orig_df = pd.read_csv("./backup/steam_apps_reviews.csv", index_col = 0)
df = orig_df.copy()
# df = df[df["playtime_at_review"] ]
print(df.sample(15))
df.rename(columns={'playtime_at_review': "play"}, inplace=True)
playtimes = df["play"].to_numpy()

# print(len(df))
# print(len(playtimes))

reviews = df["review"]
reviews = [[review] for review in reviews]

review_lists = [str(rev_string[0])
                .replace("\n", " ")
                .replace(",", "")
                .replace(".", " ")
                .replace(")", "")
                .replace(":", "")
                .replace(";", "")
                .replace("-", "")
                .replace("(", "")
                .split(" ") for rev_string in reviews]

review_counts = np.array([len(rev_list) for rev_list in review_lists])
print(review_counts)
# print(len(review_counts))
# print(len(playtimes))

sns.scatterplot(x=review_counts[::50], y=playtimes[::50] / 60)
plt.xlabel("Number of Words in Review")
plt.ylabel("Gameplay Time at Review (Hours)")
plt.title("Number of Words vs. Gameplay Time")
plt.show()

# sns.histplot(x=review_counts)
# plt.xlabel("Number of Words in Review")
# plt.ylabel("Counts")
# plt.title("Histogram of Review Lengths")
# plt.show()

shortened_review_lists = review_lists[:50]

# for my_list in shortened_review_lists:
#     print(len(my_list))

# print(len(shortened_review_lists))

with open("./review_lists.csv", "w") as f:
    write = csv.writer(f)
    write.writerows(shortened_review_lists)
