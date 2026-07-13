import subprocess
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

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
init_events = (dict(date="2010-12-26", y=450, text="1st commit"),)

governance_events = (
    dict(date="2021-05-17", y=420, text="codify de facto\nBDFL governance"),
    dict(date="2022-08-26", y=290, text="BDFL transition"),
    dict(
        date="2024-12-03",
        y=370,
        text="reorg as\nAdvisory Board,\nSteering Council,\n& Maintainer Team",
    ),  # noqa: E501
)

onboarding_events = (
    dict(date="2021-01-22", y=450, text="1st online office hour"),
    dict(date="2021-03-16", y=400, text="1st New Developer\nSprint"),
    dict(date="2022-07-22", y=275, text="2nd New Developer\nSprint"),
    dict(date="2023-11-14", y=200, text="Intermediate\nSprint"),
    dict(date="2025-06-01", y=125, text="Maintainer\nOnboarding\nbegins"),
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

vlines = None
texts = []
for ix, (fname, events) in enumerate(
    dict(gov=governance_events, onboard=onboarding_events, first=init_events).items()
):
    # gray out events from prior slide
    if vlines is not None:
        # vlines.set_color("0.3")
        vlines.remove()
    if texts:
        [t.remove() for t in texts]
        texts = []
        # [t.set_color("0.2") for t in texts]
        # [t.set_bbox(None) for t in texts]
    # add vline_locs for events
    vline_locs = [pd.to_datetime(e["date"]) for e in events]
    vlines = ax.vlines(
        x=vline_locs,
        ymin=ax.get_ylim()[0] + 7,
        ymax=[e["y"] for e in events],  # 450
        colors=f"C{ix}",
        linestyle="--",
        alpha=0.8,
        zorder=5,
    )
    # add text for events
    for event in events:
        d = pd.to_datetime(event["date"]) + pd.Timedelta(days=30)
        texts.append(
            ax.text(
                x=d,
                y=event["y"],
                s=event["text"],
                fontsize="small",
                va="top",
                ha="left",
                zorder=8,
                bbox=dict(facecolor="k", alpha=0.8, pad=2, edgecolor="none"),
            )
        )
    fig.savefig(f"fig-{fname}-history.png", dpi=300, facecolor="none")
