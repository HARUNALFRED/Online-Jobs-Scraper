import os.path
import os
import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from datetime import datetime


def jobs_save(dict, keep="last"):
    """Checks job links against previously fetched jobs, and saves new entries
    to file. Takes a dictionary which must have the key "Link" and returns a
    dataframe of all jobs"""

    new_jobs_df = pd.DataFrame(dict)

    # Check if file exists
    if os.path.isfile("joblist.pkl"):
        old_jobs_df = pd.read_pickle("joblist.pkl")
        df = pd.concat([new_jobs_df, old_jobs_df])

        # Remove any entry with the same link
        df["Select"].replace("", np.nan, inplace=True)
        df.sort_values(by=["Link", "Select"], na_position="last", inplace=True)
        df.drop_duplicates(subset="Link", keep="first", inplace=True)
        df["Select"].replace(np.nan, "", inplace=True)

    else:
        df = new_jobs_df

    df.to_pickle("joblist.pkl")

    return df


def jobs_load():
    df = pd.read_pickle("joblist.pkl")
    return df


def jobs_sort(df, date):
    """Iterates through jobs in a dataframe from a specified date. User input
    flags selects, returns a dataframe of selected jobs. Date should be in the
    format "YYYY-MM-DD"."""

    df["Date Posted"] = pd.to_datetime(df["Date Posted"])
    df = df[(df["Date Posted"] >= date)]
    df = df.fillna("")
    df = df[(df["Select"] == "")]

    # Filter out some words
    if os.path.isfile("filters.txt"):
        with open("./filters.txt") as f:
            filters = f.readlines()

        filters = [line.strip() for line in filters]

        filter = "|".join(filters)
        df = df[~df["Title"].str.contains(filter, case=False)]

    # Ensure the query is within the title, using fuzzy matching
    df = df[
        df.apply(
            lambda row: fuzz.token_set_ratio(row["Query"].lower(), row["Title"].lower())
            > 75
            if pd.notnull(row["Title"]) and pd.notnull(row["Query"])
            else False,
            axis=1,
        )
    ]

    if len(df) == 0:
        print("No jobs matching description.")
        return

    for i in range(0, len(df)):
        print_frame = df.iloc[i]
        print_snippet = print_frame["Snippet"]

        # Clear the terminal screen based on the operating system
        if os.name == "posix":  # For UNIX/Linux/Mac
            os.system("clear")
        elif os.name == "nt":  # For Windows
            os.system("cls")

        print(f'\n\nResult {i+1} of {len(df)}: {print_frame["Query"]}')

        print_frame = print_frame.drop(
            ["Link", "Datetime Retrieved", "Query", "Select", "Snippet"]
        )

        print(print_frame)
        print(print_snippet)
        usr_input = input(
            "Type an integer rating if interested. Enter or 0 to reject. (Q) to quit: "
        )
        if not usr_input.isdigit():
            if usr_input.lower() == "q":
                break
            rating = 0
        else:
            rating = int(usr_input)

        df.iloc[i, df.columns.get_loc("Select")] = rating

    df["Select"] = pd.to_numeric(df["Select"])
    df = df.sort_values(by="Select", ascending=False)
    jobs_save(df, keep="first")

    df_selects = df[
        (df["Select"] > 0) & (~df["Select"].isnull()) & (df["Select"] != "")
    ]

    if os.path.isfile("selects.pkl"):
        old_selects_df = pd.read_pickle("selects.pkl")
        all_selects = pd.concat([df_selects, old_selects_df])
        # Remove any entry with the same link
        all_selects = df.drop_duplicates(subset="Link", keep="last")
    else:
        all_selects = df_selects

    all_selects.to_pickle("selects.pkl")

    return df_selects


if __name__ == "__main__":
    from datetime import datetime

    df = jobs_load()
    selects = jobs_sort(df, datetime.now().strftime("%Y-%m-%d"))
    jobs_save(selects, keep="first")
