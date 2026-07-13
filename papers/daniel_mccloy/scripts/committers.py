import os

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# import seaborn as sns

from github import Auth, Github

# styling
plt.style.use("dark_background")
mpl.rc("axes.spines", left=False, right=False, top=False, bottom=False)
mpl.rc("xtick", color="0.8")
mpl.rc("ytick", color="0.8")
mpl.rc("axes", labelcolor="0.8", titlecolor="0.8")

data_path = Path("all-mergers.csv").resolve()

if data_path.exists():
    data = pd.read_csv(data_path, index_col=False, parse_dates=["date"])
else:
    rows = list()
    auth = Auth.Token(os.environ["GITHUB_TOKEN"])
    g = Github(auth=auth, per_page=100)
    repo = g.get_repo("mne-tools/mne-python")
    all_pulls = repo.get_pulls(state="closed")
    # while loop over paginated results
    ix = 0
    done = False
    while not done:
        page = all_pulls.get_page(ix)
        for pr in page:
            if pr.merged:
                row = dict(
                    date=pr.merged_at,
                    number=pr.number,
                    merger=pr.merged_by.login or "",
                )
                rows.append(row)
        ix += 1
        done = not len(page)
    data = pd.DataFrame(rows)
    data.sort_values("date", inplace=True)
    data.to_csv(data_path, index=False)

# remove bots
data = data.loc[~data["merger"].isin(("github-actions[bot]", "mne-bot"))]
#
data["unique mergers"] = [
    data["merger"].iloc[:ix].nunique() for ix in range(data.shape[0])
]

# set up figure
fig, ax = plt.subplots(layout="constrained")
w, h = np.array((23.67, 9.49)) / 2.54
fig.set_size_inches(w, h)
# plot merger data
data.plot(
    x="date",
    y="unique mergers",
    title="Cumulative unique mergers to MNE-Python",
    ylabel="Maintainers",
    xlabel="Date",
    legend=False,
    ax=ax,
    color="C4",
    zorder=10,
)
ax.set(xlim=(pd.to_datetime("2010-11-01"), pd.to_datetime("2027-03-31")), ylim=(-2, 40))
fig.savefig("fig-mergers.png", dpi=300, facecolor="none")

1 / 0
# make figure
ax = sns.stripplot(
    data,
    x="date",
    y="merger",
    size=8,
    orient="h",
    jitter=False,
    linewidth=1,
    edgecolor="#FFFFFF66",
)

fig = ax.figure
fig.set_size_inches(12, 8)
fig.subplots_adjust(left=0.2)
fig.show()
# fig.savefig("fig-committers.png")
