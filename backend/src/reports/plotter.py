import os
import tempfile
from typing import Dict, List, Tuple, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


def _tmp_path(prefix: str, suffix: str = ".png") -> str:
    fd, path = tempfile.mkstemp(prefix=prefix, suffix=suffix)
    os.close(fd)
    return path


def plot_sentiment_evolution(series: List[Tuple[str, float]]) -> Optional[str]:
    if not series:
        return None
    dates = [d for d, _ in series]
    values = [v for _, v in series]
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 3))
    sns.lineplot(x=dates, y=values, marker="o", linewidth=1.8)
    plt.xticks(rotation=45, ha="right")
    plt.ylim(-1.0, 1.0)
    plt.tight_layout()
    out = _tmp_path("sentiment_evolution_")
    plt.savefig(out, dpi=160)
    plt.close()
    return out


def plot_sentiment_by_category(cat_to_avg: Dict[str, float]) -> Optional[str]:
    if not cat_to_avg:
        return None
    items = sorted(cat_to_avg.items(), key=lambda x: x[1])
    cats = [k for k, _ in items]
    vals = [v for _, v in items]
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 3.6))
    sns.barplot(x=vals, y=cats, orient="h", palette="vlag")
    plt.xlim(-1.0, 1.0)
    plt.tight_layout()
    out = _tmp_path("sentiment_by_category_")
    plt.savefig(out, dpi=160)
    plt.close()
    return out


def plot_topics_top_bottom(top5: List[Tuple[str, float]], bottom5: List[Tuple[str, float]]) -> Optional[str]:
    labels = [t for t, _ in bottom5] + [t for t, _ in top5]
    vals = [v for _, v in bottom5] + [v for _, v in top5]
    if not labels:
        return None
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 3.6))
    sns.barplot(x=vals, y=labels, orient="h", palette=["#d9534f" for _ in bottom5] + ["#5cb85c" for _ in top5])
    plt.xlim(-1.0, 1.0)
    plt.tight_layout()
    out = _tmp_path("topics_top_bottom_")
    plt.savefig(out, dpi=160)
    plt.close()
    return out


def plot_sov_pie(sov_list: List[Tuple[str, float]]) -> Optional[str]:
    if not sov_list:
        return None
    labels = [n for n, _ in sov_list]
    sizes = [max(0.01, float(v)) for _, v in sov_list]
    plt.figure(figsize=(4.8, 4.8))
    plt.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=140, textprops={"fontsize": 8})
    plt.tight_layout()
    out = _tmp_path("sov_pie_")
    plt.savefig(out, dpi=160)
    plt.close()
    return out


