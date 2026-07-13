import datetime as dt
import os
import re

from pathlib import Path

import pandas as pd
import seaborn as sns
import yaml

from github import Auth, Github

sns.set_theme(style="white", context="talk")

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


auth = Auth.Token(os.environ["GITHUB_TOKEN"])
g = Github(auth=auth, per_page=100)
coauthor_regex = re.compile(r"Co-authored-by: (?P<name>[^<>]+) <(?P<email>[^()>]+)>")

# mapping from GH handles to names
userfile = Path("users.yaml").resolve()
if userfile.exists():
    print("")
    with open(userfile, "r") as fid:
        users = yaml.safe_load(fid)
else:
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
    hue="role",
    size=8,
    orient="h",
    jitter=False,
    linewidth=1,
    edgecolor="#FFFFFF66",
)
# TODO add fills at dates of first and second sprints and maintainer onboarding period

fig = ax.figure
fig.set_size_inches(12, 8)
fig.subplots_adjust(left=0.2)
fig.show()
fig.savefig("retention-raw-data.png")

1 / 0

ax = (
    df.set_index("date")
    .rolling(dt.timedelta(days=90))["user"]
    .count()
    .plot(kind="line")
)
ax.figure.show()
