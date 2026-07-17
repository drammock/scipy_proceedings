import os
import subprocess

from copy import deepcopy
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from github import Auth, Github

# styling
plt.style.use("dark_background")
mpl.rc("axes.spines", left=False, right=False, top=False, bottom=False)
mpl.rc("xtick", color="0.8")
mpl.rc("ytick", color="0.8")
mpl.rc("axes", labelcolor="0.8", titlecolor="0.8")


data_path = Path("contrib-history.csv").resolve()

if data_path.exists():
    data = pd.read_csv(data_path, parse_dates=["date"])
else:
    months = list(range(1, 13))
    years = list(range(2010, 2027))
    contribs = list()
    for y in years:
        for m in months:
            date = f"{y}-{m:02d}-01"
            result = subprocess.run(
                ["git", "shortlog", "-nse", "--before", date, "--", "/opt/mne/python"],
                capture_output=True,
                text=True,
            )
            n_contrib = len(result.stdout.splitlines())
            contribs.append((date, n_contrib))

    df = pd.DataFrame(contribs, columns=["date", "unique contributors"])
    df["date"] = pd.to_datetime(df["date"])

    data = df.loc[
        (df["date"] >= pd.to_datetime("2010-11-01"))
        & (df["date"] <= pd.to_datetime("2026-07-01"))
    ]

    data.to_csv(data_path, index=False)

# add delta column
data["delta"] = data["unique contributors"].diff()

# event data
init_events = (dict(date="2010-12-26", y=0.9, text="1st commit"),)

governance_events = (
    dict(date="2021-05-17", y=0.4, text="codify de facto\nBDFL governance"),
    dict(date="2022-08-26", y=0.25, text="BDFL transition"),
    dict(
        date="2024-12-03",
        y=0.5,
        text="reorg as\nAdvisory Board,\nSteering Council,\n& Maintainer Team",
    ),  # noqa: E501
)

onboarding_events = (
    dict(date="2021-01-22", y=0.4, text="1st online office hour"),
    dict(date="2021-03-16", y=0.3, text="1st New Developer\nSprint"),
    dict(date="2022-07-22", y=0.15, text="2nd New Developer\nSprint"),
    dict(date="2023-11-14", y=0.4, text="Intermediate\nSprint"),
    dict(date="2025-06-01", y=0.25, text="Maintainer\nOnboarding\nbegins"),
)


# set up figure
fig, ax = plt.subplots(layout="constrained")
w, h = np.array((23.67, 9.49)) / 2.54
fig.set_size_inches(w, h)
# plot contributor data
data.plot(
    x="date",
    y="unique contributors",
    title="Cumulative unique contributors to MNE-Python",
    ylabel="Contributors",
    xlabel="Date",
    legend=False,
    ax=ax,
    color="C3",
    zorder=10,
)
ax.set(xlim=(ax.get_xlim()[0], pd.to_datetime("2027-03-31")), ylim=(-25, 475))
fig.savefig("fig-contrib-history.png", dpi=300, facecolor="none")

# # # # # # # # # # # # # # # # # #
# now, do the committers/mergers  #
# # # # # # # # # # # # # # # # # #
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
# cumulative number of mergers
data["unique mergers"] = [
    data["merger"].iloc[:ix].nunique() for ix in range(data.shape[0])
]

# plot merger data
ax.lines[0].set_data(
    data["date"].to_numpy(),
    data["unique mergers"].to_numpy(),
)
ax.lines[0].set_label("Cumulative")
ax.lines[0].set_color("C4")
ax.set(
    ylim=(-2, 30),
    xlabel="Date",
    ylabel="Maintainers",
    title="Cumulative unique mergers to MNE-Python",
)
fig.savefig("fig-maintainers-cumulative.png", dpi=300, facecolor="none")

# stackplot data
window = 365
stackplot_data = (
    data[["merger", "date", "number"]]
    .set_index(["date", "merger"])
    .unstack()
    .apply(np.isfinite)
    .rolling(window=pd.Timedelta(value=window, unit="days"), min_periods=1)
    .sum()
    .astype(int)
)
# sort column order by total merges
stackplot_data = stackplot_data[
    stackplot_data.sum().sort_values(ascending=False).index.tolist()
]
stackfig, stackax = plt.subplots(layout="constrained")
w, h = np.array((23.67, 9.49)) / 2.54
stackfig.set_size_inches(w, h)
stackax.stackplot(
    stackplot_data.index,
    stackplot_data.T,
    baseline="sym",
)
stackax.set(
    xlabel="Date",
    ylabel="Merges",
    title="Merges by each maintainer (1 year rolling sum)",
)
stackfig.savefig(f"fig-rolling-{window}-merger-history.png", dpi=300, facecolor="none")

vlines = None
texts = []
thisax = stackax  # where to put the event annotations
xlim = thisax.get_xlim()
ylim = thisax.get_ylim()

for ix, (fname, events) in enumerate(
    dict(gov=governance_events, onboard=onboarding_events, first=init_events).items()
):
    # gray out events from prior slide
    if vlines is not None:
        vlines.remove()
    if texts:
        [t.remove() for t in texts]
        texts = []
    # add vline_locs for events
    vline_locs = [pd.to_datetime(e["date"]) for e in events]
    vlines = thisax.vlines(
        x=vline_locs,
        ymin=ylim[0] + 0.01 * np.diff(ylim)[0],
        ymax=ylim[0] + 0.99 * np.diff(ylim)[0],
        colors="w",
        linestyle="--",
        alpha=1,
        zorder=5,
    )
    # add text for events
    for event in events:
        d = pd.to_datetime(event["date"]) + pd.Timedelta(days=30)
        texts.append(
            thisax.text(
                x=d,
                y=thisax.get_ylim()[0] + event["y"] * np.diff(thisax.get_ylim())[0],
                s=event["text"],
                fontsize="small",
                va="top",
                ha="left",
                zorder=8,
                bbox=dict(facecolor="k", alpha=0.8, pad=2, edgecolor="none"),
            )
        )
    thisax.set_xlim(xlim)
    thisax.set_ylim(ylim)
    thisax.figure.savefig(f"fig-{fname}-history.png", dpi=300, facecolor="none")


# clean up event lines
# _ = [l.remove() for l in thisax.collections]

# # add
# newline = mpl.lines.Line2D(
#     xdata=data["date"].to_numpy(),
#     ydata=data["unique mergers"].to_numpy(),
#     color="C4",
#     label="Maintainers (cumulative)",
# )
# ax.add_line(newline)
# ax.legend()
# fig.savefig("fig-merges-per-maintainer-cumulative.png", dpi=300, facecolor="none")
