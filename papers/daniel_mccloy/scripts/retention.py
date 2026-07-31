import datetime as dt
import os
import re

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import yaml

from github import Auth, Github

sns.set_theme(style="white", context="talk")
plt.style.use("dark_background")
mpl.rc("axes.spines", left=False, right=False, top=False, bottom=False)
mpl.rc("xtick", color="0.8")
mpl.rc("ytick", color="0.8")
mpl.rc("axes", labelcolor="0.8", titlecolor="0.8")

handles = (
    "adam2392",
    "adelinefecker",
    "alexrockhill",
    "anaradanovic",
    "apoorva6262",
    "ashdrew",
    "CarinaFo",
    "catalinamagalvan",
    "cmista",
    "dominikwelke",
    "eioe",
    "eort",
    "Falach",
    "FinLouarn",
    "HamidMandi",
    "HanBnrd",
    "kimcoco",
    "marsipu",
    "MatteoAnelli",
    "mdclarke",
    "neurogima",
    "NeuroLaunch",
    "nordme",
    "ramkpari",
    "scott-huberty",
    "sfc-neuro",
    "timonmerk",
    "vagechirkov",
    "vpeterson",
)

repos = (
    "mne-bids",
    "mne-connectivity",
    "mne-gui-addons",
    "mne-hfo",
    "mne-icalabel",
    "mne-python",
    "mne-qt-browser",
)

onboarding_events = (
    dict(date="2021-03-16", y=0.3, text="1st New Developer\nSprint"),
    dict(date="2022-07-22", y=0.15, text="2nd New Developer\nSprint"),
    dict(date="2023-11-14", y=0.4, text="Intermediate\nSprint"),
)

# mapping from GH handles to names
userfile = Path("users.yaml").resolve()
if userfile.exists():
    print("")
    with open(userfile, "r") as fid:
        users = yaml.safe_load(fid)
else:
    auth = Auth.Token(os.environ["GITHUB_TOKEN"])
    g = Github(auth=auth, per_page=100)
    coauthor_regex = re.compile(
        r"Co-authored-by: (?P<name>[^<>]+) <(?P<email>[^()>]+)>"
    )
    users = {handle: g.get_user(handle).name for handle in handles}
    with open(userfile, "w") as fid:
        yaml.dump(users, fid)

# check if data already fetched
datafile = Path("all-commits.csv").resolve()
if datafile.exists():
    df = pd.read_csv(datafile, index_col=False, parse_dates=["date"])
else:
    rows = list()
    for _repo in repos:
        repo = g.get_repo(f"mne-tools/{_repo}")
        all_commits = repo.get_commits(since=dt.datetime(2021, 1, 1))
        # while loop over paginated results
        ix = 0
        done = False
        while not done:
            page = all_commits.get_page(ix)
            for commit in page:
                # keep commit if its author was someone on this list
                if commit.author and commit.author.login in handles:
                    row = dict(
                        date=commit.commit.author.date,
                        repo=_repo,
                        user=commit.author.login,
                        role="author",
                        hash=commit.sha,
                    )
                    rows.append(row)
                # keep commit if its committer was someone on this list
                if commit.committer and commit.committer.login in handles:
                    row = dict(
                        date=commit.commit.committer.date,
                        repo=_repo,
                        user=commit.committer.login,
                        role="committer",
                        hash=commit.sha,
                    )
                    rows.append(row)
                # keep commit if a coauthor was someone on this list
                coauths = coauthor_regex.findall(commit.commit.message)
                for coauth in coauths:
                    for handle in handles:
                        if coauth[0] == users[handle]:
                            row = dict(
                                date=commit.commit.author.date,
                                repo=_repo,
                                user=handle,
                                role="co-author",
                                hash=commit.sha,
                            )
                            rows.append(row)
            ix += 1
            done = not len(page)

    df = pd.DataFrame(rows)
    df.sort_values("date", inplace=True)
    df.to_csv(datafile, index=False)

# make figure
ax = sns.stripplot(
    df,
    x="date",
    y="user",
    # hue="role",
    size=6,
    orient="h",
    jitter=False,
    linewidth=0,
    edgecolor="#00000066",
)
ax.yaxis.set_ticklabels(np.arange(len(ax.yaxis.get_ticklabels())))
ax.yaxis.set_tick_params(labelsize=6)
ylim = ax.get_ylim()

vline_locs = [pd.to_datetime(e["date"]) for e in onboarding_events]
vlines = ax.vlines(
    x=vline_locs,
    ymin=ylim[0] + 0.01 * np.diff(ylim)[0],
    ymax=ylim[0] + 0.99 * np.diff(ylim)[0],
    colors="w",
    linestyle="--",
    alpha=1,
    zorder=5,
)

# TODO add fills at dates of first and second sprints and maintainer onboarding period

fig = ax.figure
w, h = np.array((23.67, 9.49)) / 2.54
fig.set_size_inches(w, h)
fig.subplots_adjust(left=0.1, right=0.95)
# fig.show()
fig.savefig("retention-raw-data.png")

1 / 0

ax = (
    df.set_index("date")
    .rolling(dt.timedelta(days=90))["user"]
    .count()
    .plot(kind="line")
)
ax.figure.show()
