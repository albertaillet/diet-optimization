"""Utils for manipulation of lists of dicts."""


def all_same_keys(table: list[dict[str, str]]) -> bool:
    """Returns true if all the dicts of the list have the same keys."""
    keys = table[0].keys()
    return all(row.keys() == keys for row in table)


def inner_merge(left: list[dict[str, str]], right: list[dict[str, str]], left_key: str, right_key: str) -> list[dict[str, str]]:
    """Does a merge of two list of dictionaries, where the dicts in each of the lists have the same keys."""
    # Similar to pandas pd.merge, documentation: https://pandas.pydata.org/docs/reference/api/pandas.merge.html
    # Check that all the dicts they have the same keys and that they contain the keys.
    assert left_key in left[0], f"{left_key=} not in {left[0].keys()}"
    assert right_key in right[0], f"{right_key=} not in {right[0].keys()}"
    assert all_same_keys(left), "Right does not have all the same keys"
    assert all_same_keys(right), "Left does not have all the same keys"

    # Create a dictionary from the right table for fast lookup.
    right_dict = {}
    for row in right:
        if row[right_key] not in right_dict:
            right_dict[row[right_key]] = [row]
        else:
            right_dict[row[right_key]].append(row)

    # Merge with the left table
    merged = []
    common_columns = left[0].keys() & right[0].keys()
    for left_row in left:
        left_key_value = left_row[left_key]
        if left_key_value not in right_dict:
            continue
        for right_row in right_dict[left_key_value]:
            # Check if common columns have the same values
            if any(left_row[col] != right_row[col] for col in common_columns):
                print(f"Warning: Mismatch in common columns for {left_key=}={left_key_value}")
                continue
            # Append the merge of the two dicts
            merged.append(left_row | right_row)

    # Check that the output has all the same keys
    assert all_same_keys(merged), "Merged tables does not have all the same keys"

    # Return merged tables
    return merged
