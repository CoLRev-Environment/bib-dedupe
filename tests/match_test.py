# @pytest.mark.parametrize(
#     "df, keys, expected_output",
#     [
#         (pd.DataFrame({"volume_1": ["34"], "volume_2": ["34"], "number_1": [""], "number_2": [""]}), ["volume", "number"], False),
#         (pd.DataFrame({"volume_1": ["34"], "volume_2": ["2"], "number_1": [""], "number_2": ["34"], "pages_1": [""], "pages_2": [""]}), ["volume", "number", "pages"], False),
#     ],
# )
# def test_non_contradicting(df, keys, expected_output):
#     query = non_contradicting(*keys)
#     print(query)
#     result = df.query(query)
#     assert result.empty == expected_output
#     # raise Exception
#     # TODO : check how many cases are actually affected by cross-matches AND how many of these are not already covered by non_contradicting
