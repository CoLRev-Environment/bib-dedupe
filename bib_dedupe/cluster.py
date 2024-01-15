#! /usr/bin/env python
"""Cluster for dedupe"""
from collections import defaultdict
from itertools import combinations
from typing import List

import pandas as pd


def get_connected_components(
    duplicates_df: pd.DataFrame,
    label: str = "duplicate",
) -> list:
    """
    Find the connected components in a graph represented by a DataFrame of duplicate pairs.

    Args:
        duplicates_df (pd.DataFrame): A DataFrame where each row represents a pair of duplicate IDs.
        label (str, optional): The label to filter the DataFrame by. Defaults to "duplicate".

    Returns:
        list: A list of connected components. Each component is a list of IDs
             that are all duplicates of each other.
    """

    if duplicates_df.empty:
        return []

    duplicates_df = duplicates_df[duplicates_df["duplicate_label"] == label]
    id_sets = duplicates_df[["ID_1", "ID_2"]].values.tolist()

    graph = defaultdict(list)

    def dfs(node: str, graph: dict, visited: dict, component: list) -> None:
        visited[node] = True
        component.append(node)
        for neighbor in graph[node]:
            if not visited[neighbor]:
                dfs(neighbor, graph, visited, component)

    # Create an adjacency list
    for id_set in id_sets:
        for combination in combinations(id_set, 2):
            graph[combination[0]].append(combination[1])
            graph[combination[1]].append(combination[0])

    visited = {node: False for node in graph}
    components = []

    for node in graph:
        if not visited[node]:
            component: List[str] = []
            dfs(node, graph, visited, component)
            components.append(sorted(component))

    return components
