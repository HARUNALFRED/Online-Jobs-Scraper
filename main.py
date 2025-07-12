#!/usr/bin/env python3

import datetime
import pandas as pd
import pyperclip
from jobscrape import job_search_time
from jobanalysis import jobs_save, jobs_load, jobs_sort


def get_int_input(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                print("Please enter an integer greater than 0.")
                continue
            return value
        except ValueError:
            print("Invalid input. Please enter a number.")


def export_jobs(df, selection_only):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    filename_prefix = "selects" if selection_only else "all"
    filename = f"custom_export_{filename_prefix}_{timestamp}.csv"
    df.to_csv(filename, encoding="utf-8-sig", index=False)
    print(f"\n✅ Jobs exported to: {filename}")


def main():
    while True:
        choice = input("(S)crape new jobs, (L)oad old jobs, or (E)xport jobs?: ").strip().lower()

        if choice == "s":
            try:
                queries = open("jobs.txt", encoding="utf-8").read().splitlines()
            except FileNotFoundError:
                print("❌ jobs.txt not found.")
                return

            days_ago = get_int_input("Number of days ago to search jobs? ")

            try:
                jobs_dict = job_search_time(queries, days_ago)
                jobs_df = jobs_save(jobs_dict)
            except Exception as e:
                print(f"❌ Job search failed: {e}")
                return

            cont = input("\nPress Enter to continue to job sorting, or anything else to quit: ")
            if cont.strip():
                print("Exiting.")
                return
            break

        elif choice == "l":
            jobs_df = jobs_load()
            break

        elif choice == "e":
            try:
                df = jobs_load()
            except Exception as e:
                print(f"❌ Failed to load jobs: {e}")
                return

            export_choice = input("Export (S)elected or (A)ll jobs? ").strip().lower()
            if export_choice == "s":
                df["Select"] = pd.to_numeric(df["Select"], errors="coerce")
                df = df[df["Select"].notna() & (df["Select"] > 0)]
                export_jobs(df, selection_only=True)
            elif export_choice == "a":
                export_jobs(df, selection_only=False)
            else:
                print("❌ Invalid export option.")
            return

        else:
            print("❌ Invalid input. Please type S, L, or E.")

    # Ask for date filtering
    try:
        usr_in = input("Number of days ago to display search results? ")
        date_limit = datetime.datetime.now() - datetime.timedelta(days=int(usr_in))
    except Exception:
        print("Invalid input. Defaulting to all available jobs.")
        date_limit = datetime.datetime.min

    selects_df = jobs_sort(jobs_df, date_limit)

    if selects_df.empty:
        print("⚠️ No jobs matched the filter.")
        return

    # Copy links to clipboard
    links = "\n".join(map(str, selects_df["Link"]))
    pyperclip.copy(links)

    print("\n📋 Selected job links copied to clipboard:")
    print(selects_df)


if __name__ == "__main__":
    main()
