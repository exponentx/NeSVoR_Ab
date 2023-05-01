from typing import Tuple, List
import numpy as np
from ...image import Stack
from . import motion_estimation
from . import iqa


def compute_metric(
    stacks: List[Stack], metric: str, device
) -> Tuple[List[float], bool]:
    descending = True
    if metric == "ncc":
        scores = motion_estimation.ncc(stacks)
    elif metric == "matrix-rank":
        scores = motion_estimation.matrix_rank(stacks)
        descending = False
    elif metric == "volume":
        scores = [
            int(
                stack.mask.float().sum().item()
                * stack.resolution_x
                * stack.resolution_y
                * stack.gap
            )
            for stack in stacks
        ]
    elif metric == "iqa2d":
        scores = iqa.iqa2d(stacks, device)
    elif metric == "iqa3d":
        scores = iqa.iqa3d(stacks)
    else:
        raise ValueError("unkown metric for stack assessment")

    return scores, descending


def sort_and_filter(
    stacks: List[Stack],
    scores: List[float],
    descending: bool,
    filter_method: str,
    cutoff: float,
) -> Tuple[List[Stack], List[int], List[bool]]:
    n_total = len(scores)
    n_keep = n_total
    if filter_method == "top":
        n_keep = min(n_keep, int(cutoff))
    elif filter_method == "bottom":
        n_keep = max(0, n_total - int(cutoff))
    elif filter_method == "percentage":
        n_keep = n_total - int(n_total * min(max(0, cutoff), 1))
    elif filter_method == "threshold":
        if descending:
            n_keep = sum(score >= cutoff for score in scores)
        else:
            n_keep = sum(score <= cutoff for score in scores)
    elif filter_method == "none":
        pass
    else:
        raise ValueError("unknown filter method")

    sorter = np.argsort(-np.array(scores) if descending else scores)
    inv = np.empty(sorter.size, dtype=np.intp)
    inv[sorter] = np.arange(sorter.size, dtype=np.intp)
    ranks = [int(rank) for rank in inv]
    excluded = [rank >= n_keep for rank in ranks]

    output_stacks = [stacks[i] for i in sorter[:n_keep]]

    return output_stacks, ranks, excluded
