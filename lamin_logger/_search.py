from typing import Any, Literal, Union

from lamin_logger import logger


def search(
    df: Any,
    string: str,
    field: str = "name",
    synonyms_field: Union[str, None] = "synonyms",
    case_sensitive: bool = True,
    return_ranked_results: bool = False,
    synonyms_sep: str = "|",
    keep: Literal["first", "last", False] = "first",
    tuple_name: str = "SearchResult",
) -> Any:
    """Search a given string against a field.

    Args:
        string: The input string to match against the field ontology values.
        field: The field against which the input string is matching.
        synonyms_field: Also map against in the synonyms
            If None, no mapping against synonyms.
        case_sensitive: Whether the match is case sensitive.
        return_ranked_results: If True, return all entries ranked by matching ratios.

    Returns:
        Best match record of the input string.
    """
    import pandas as pd

    from ._map_synonyms import explode_aggregated_column_to_map

    def _fuzz_ratio(string: str, iterable: pd.Series, case_sensitive: bool = True):
        from rapidfuzz import fuzz, utils

        processor = None if case_sensitive else utils.default_process
        return iterable.apply(lambda x: fuzz.ratio(string, x, processor=processor))

    # empty DataFrame
    if df.shape[0] == 0:
        if return_ranked_results:
            return df
        else:
            return None

    # search against each of the synonyms
    if (synonyms_field in df.columns) and (synonyms_field != field):
        # creates field_value:synonym
        mapper = explode_aggregated_column_to_map(
            df,
            agg_col=synonyms_field,  # type:ignore
            target_col=field,
            keep=keep,
            sep=synonyms_sep,
        )
        if keep is False:
            mapper = mapper.explode()
        # adds field_value:field_value
        df_field = pd.Series(df[field].values, index=df[field], name=field)
        df_field.index.name = synonyms_field
        df_field = df_field[df_field.index.difference(mapper.index)]
        mapper = pd.concat([mapper, df_field])
        df_exp = mapper.reset_index()
        target_column = synonyms_field
    else:
        if synonyms_field == field:
            logger.warning(
                "Input field is the same as synonyms field, skipping synonyms matching"
            )
        df_exp = df[[field]].copy()
        target_column = field

    # add matching scores as a __ratio__ column
    df_exp["__ratio__"] = _fuzz_ratio(
        string=string, iterable=df_exp[target_column], case_sensitive=case_sensitive
    )
    # only keep the max score between field and synonyms for each entry
    df_exp_grouped = (
        df_exp.groupby(field).max("__ratio__").sort_values("__ratio__", ascending=False)
    )
    # subset to original field values (as synonyms were mixed in before)
    df_exp_grouped = df_exp_grouped[df_exp_grouped.index.isin(df[field])]
    df_scored = df.set_index(field).loc[df_exp_grouped.index]
    df_scored["__ratio__"] = df_exp_grouped["__ratio__"]

    if return_ranked_results:
        return df_scored.sort_values("__ratio__", ascending=False)
    else:
        res = df_scored[df_scored["__ratio__"] == df_scored["__ratio__"].max()]
        res = res.drop(columns=["__ratio__"])
        res_records = list(res.reset_index().itertuples(index=False, name=tuple_name))
        if len(res_records) == 1:
            return res_records[0]
        else:
            return res_records
