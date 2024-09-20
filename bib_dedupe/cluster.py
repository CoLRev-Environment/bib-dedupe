#! /usr/bin/env python
"""Cluster for dedupe"""
from collections import defaultdict
from itertools import combinations
from typing import List
from typing import Set

import pandas as pd

from bib_dedupe.constants.fields import DUPLICATE_LABEL


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
    node: str,
    adjacency_list: dict,
    visited: dict,
    component: list,
    entity_set_map: dict,
    component_sets: set,
) -> None:
    """
    Perform a depth-first search on an adjacency list starting from a given node.

    Args:
        node (str): The node to start the search from.
        adjacency_list (dict): The adjacency list to perform the search on.
        visited (dict): A dictionary where each key is a node and
        each value is a boolean indicating if the node has been visited.
        component (list): A list to store the nodes visited in the search.
        entity_set_map (dict): A mapping of entity IDs to their sets.
        component_sets (set): A set to store the sets that have been added to the component.
    """

    node_set = entity_set_map[node]

    if node_set in component_sets:
        return

    visited[node] = True
    component.append(node)
    if node_set:
        component_sets.add(node_set)

    for neighbor in adjacency_list[node]:
        if not visited[neighbor]:
            depth_first_search(
                neighbor,
                adjacency_list,
                visited,
                component,
                entity_set_map,
                component_sets,
            )


def get_connected_components(
    duplicates_df: pd.DataFrame,
    label: str = "duplicate",
) -> list:
    """
    Find the connected components in an adjacency list represented by a DataFrame of duplicate pairs,
    while ensuring no component contains more than one entity from the same set.

    Args:
        duplicates_df (pd.DataFrame): A DataFrame where each row represents a pair of duplicate IDs.
        label (str, optional): The label to filter the DataFrame by. Defaults to "duplicate".

    Returns:
        list: A list of connected components. Each component is a list of IDs
             that are all duplicates of each other, with no two entities from the same set.
    """

    if duplicates_df.empty:
        return []

    duplicates_df = duplicates_df[duplicates_df[DUPLICATE_LABEL] == label]

    adjacency_list = get_adjacency_list(duplicates_df)

    entity_set_map = {}

    for _, row in duplicates_df.iterrows():
        entity_set_map[row["ID_1"]] = row["search_set_1"]
        entity_set_map[row["ID_2"]] = row["search_set_2"]

    visited = {node: False for node in adjacency_list}
    components = []

    for node in adjacency_list:
        if not visited[node]:
            component: List[str] = []
            component_sets: Set[str] = set()
            depth_first_search(
                node, adjacency_list, visited, component, entity_set_map, component_sets
            )
            components.append(sorted(component))

    return components
