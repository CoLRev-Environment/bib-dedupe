#! /usr/bin/env python
"""Cluster for dedupe"""
from collections import defaultdict
from itertools import combinations
from typing import List

import pandas as pd


def get_adjacency_list(duplicates_df: pd.DataFrame) -> dict:
    """
    Generate an adjacency list from a DataFrame of duplicate pairs.

    Args:
        duplicates_df (pd.DataFrame): A DataFrame where each row represents a pair of duplicate IDs.

    Returns:
        dict: An adjacency list. Each key is an ID and each value is a list
        of IDs that are duplicates of the key.
    """
    id_sets = duplicates_df[["ID_1", "ID_2"]].values.tolist()

    adjacency_list = defaultdict(list)

    for id_set in id_sets:
        for combination in combinations(id_set, 2):
            adjacency_list[combination[0]].append(combination[1])
            adjacency_list[combination[1]].append(combination[0])
    return adjacency_list


def depth_first_search(
    node: str, adjacency_list: dict, visited: dict, component: list
) -> None:
    """
    Perform a depth-first search on an adjacency list starting from a given node.

    Args:
        node (str): The node to start the search from.
        adjacency_list (dict): The adjacency list to perform the search on.
        visited (dict): A dictionary where each key is a node and
        each value is a boolean indicating if the node has been visited.
        component (list): A list to store the nodes visited in the search.
    """
    visited[node] = True
    component.append(node)
    for neighbor in adjacency_list[node]:
        if not visited[neighbor]:
            depth_first_search(neighbor, adjacency_list, visited, component)


def get_connected_components(
    duplicates_df: pd.DataFrame,
    label: str = "duplicate",
) -> list:
    """
    Find the connected components in a adjacency_list represented by a DataFrame of duplicate pairs.

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

    adjacency_list = get_adjacency_list(duplicates_df)

    visited = {node: False for node in adjacency_list}
    components = []

    for node in adjacency_list:
        if not visited[node]:
            component: List[str] = []
            depth_first_search(node, adjacency_list, visited, component)
            components.append(sorted(component))

    return components
