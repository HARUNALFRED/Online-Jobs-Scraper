import urllib
import selenium
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import datetime
from time import sleep, strptime
from random import randint


def get_user_agent():
    ua_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.3",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.47",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.3",
    ]
    rand_ua = randint(0, 4)

    return ua_list[rand_ua]


def scrape_joblist(driver, query, page, location=""):
    """Returns a (souped) page from indeed. Takes a job query string and
    starting number."""

    # Create the URL from the query
    url_vars = {"q": query, "l": location, "sort": "date", "start": page}
    url = "https://uk.indeed.com/jobs?" + urllib.parse.urlencode(url_vars)

    # Moving this to the aggregate function

    # Get the page from the URL with undetected_chromedriver to bypass cloudflare security
    # options = uc.ChromeOptions()
    # options.add_argument('--headless')

    # driver = uc.Chrome(version_main=114, options=options)

    driver.get(url)
    page = driver.page_source

    # Convert the page to soup and return soup
    soup = BeautifulSoup(page, "html.parser")
    return soup


def test_page(*args):
    """Returns a saved local page for testing"""

    # Open a previously scraped html file, convert to soup and return
    with open("jobpage.html") as jp:
        soup = BeautifulSoup(jp, "html.parser")
        return soup


def extract_jobs(soup):
    """Takes a soup input and extracts job information. Returns four lists:
    "titles", "companies", "dates", and "links"."""

    date_now = datetime.datetime.now()

    # We'll store the data in lists
    titles = []
    companies = []
    locations = []
    salaries = []
    dates = []
    snippets = []
    links = []

    # Indeed separates job listings in "JobCards". We'll start by pulling these
    # out.
    jobcards = soup.find_all("div", class_="cardOutline")

    # The next step is to iterate through each jobcard and pull the information
    # we need.
    for jobcard in jobcards:
        title_elem = jobcard.find("h2", class_="jobTitle")
        company_elem = jobcard.find("span", {"data-testid": "company-name"})
        location_elem = jobcard.find("div", {"data-testid": "text-location"})
        salary_elem = jobcard.find("div", class_="salary-snippet-container")
        date_elem = jobcard.find("span", {"data-testid": "myJobsStateDate"})
        link_elem = jobcard.find("a").get("data-jk")
        snippet_elem = jobcard.find("tr", class_="underShelfFooter")

        # Cleaning the elements to get what we need
        title = title_elem.get_text()
        company = company_elem.get_text()
        location = location_elem.get_text()
        if salary_elem:
            salary = salary_elem.get_text()
        else:
            salary = "nan"

        # Updated snippet CSS makes this considerably harder: old method below
        # snippet = snippet_elem.get_text()
        snippet_elem_list = snippet_elem.get_text().splitlines()
        if len(snippet_elem_list) > 2:
            snippet_elem_list.pop(0)
            snippet_elem_list.pop(-1)

        snippet = ""
        for line in snippet_elem_list:
            snippet += f"{line} "

        # Converting the posted date into a usable format now
        date_extr = date_elem.get_text().lower()
        if date_extr.startswith("posted"):
            date_extr = date_extr[6:]

        # Anything 'just posted' or 'today' will get timestamped for today
        if date_extr == "just posted" or date_extr == "today":
            date = date_now

        # 'hiring ongoing' means it's been there for a while: we'll use 30 days
        elif date_extr == "hiring ongoing" or date_extr == "active today":
            date = date_now - datetime.timedelta(30)

        # If it's anything else, it's either in the format 'posted {n} days ago'
        # or something we haven't seen before. Converting date to a list,
        # checking to see if it's expected, and saving.
        else:
            date_list = date_extr.split()
            if date_list[0] == "posted":
                # This will generally fail if the posting was "30+" days ago.
                if not date_list[1].isdigit():
                    date = date_now - datetime.timedelta(30)
                else:
                    date = date_now - datetime.timedelta(int(date_list[1]))
            else:
                date = date_now - datetime.timedelta(30)

        date = date.strftime("%Y-%m-%d")

        # Rebuilding the link with an ID fetched earlier
        link = "https://uk.indeed.com/viewjob?jk=" + link_elem

        # Append the values to their lists
        titles.append(title)
        companies.append(company)
        locations.append(location)
        salaries.append(salary)
        dates.append(date)
        links.append(link)
        snippets.append(snippet)

    return titles, companies, locations, salaries, dates, links, snippets


def job_search_time(job_queries: list, days=1, testing: bool = 0):
    """Takes a list of job queries and a number of days to search back.
    Returns a dictionary of results with the keys "Title", "Company", "Date
    Posted", "Date Retrieved", "Link", and "Select" (empty). Waits a 1-5
    seconds between individual queries and half a second within."""

    now = datetime.datetime.now()

    # Create a dictionary to hold the job info
    jobs_dict = {
        "Title": [],
        "Company": [],
        "Location": [],
        "Salary": [],
        "Date Posted": [],
        "Datetime Retrieved": [],
        "Link": [],
        "Snippet": [],
        "Query": [],
        "Select": [],
    }

    # For each query, grab a number of job results and append to lists
    count = 0

    for query in job_queries:
        index = 0
        total_retries = 0

        while index >= 0:
            # Restart driver every thirty pages
            if count % 30 == 0:
                if count != 0:
                    driver.quit()
                options = uc.ChromeOptions()
                options.add_argument("--headless")
                options.add_argument(f"--user-agent={get_user_agent()}")

                driver = uc.Chrome(version_main=114, options=options)

            # Add'l error handling
            if total_retries == 3:
                print(
                    f"Too many errors. Additional results for {query} have been skipped."
                )
                print(f"Waiting 10 seconds...")
                sleep(10)
                break

            # Long run handling
            if (index + 1) % 100 == 0:
                cont_in = input(
                    f"Reached page {index + 1} for {query}. (Y) to continue, (N) to break: "
                )
                while cont_in.lower() not in ["y", "n"]:
                    cont_in = input("Input (Y) to continue, (N) to break: ")
                if cont_in.lower() == "n":
                    break

            print(f"Retrieving results page {index + 1} for {query}")
            # use test_page() for testing, scrape_joblist() for production

            retry = 0
            while True:
                job_soup = scrape_joblist(driver, query, index * 10)

                (
                    ext_titles,
                    ext_companies,
                    ext_locations,
                    ext_salaries,
                    ext_dates,
                    ext_links,
                    ext_snippets,
                ) = extract_jobs(job_soup)
                try:
                    last_date_list = strptime(ext_dates[-1], "%Y-%m-%d")
                    break
                except BaseException as e:
                    if retry == 2:
                        print(
                            f"An error has occured. Results page {index + 1} for {query} has been skipped. \n\
                              error message: {e}"
                        )
                        with open("errorlog.html", "w") as f:
                            job_err = str(job_soup)
                            f.write(job_err)
                        print("HTML output saved to errorlog.html")
                        retry += 1
                        total_retries += 1
                        break
                    else:
                        retry += 1
                        print("An error has occured. Attempting to retry...")
                        driver.quit()

                        options = uc.ChromeOptions()
                        options.add_argument("--headless")
                        options.add_argument(f"--user-agent={get_user_agent()}")

                        driver = uc.Chrome(version_main=114, options=options)

                        sleep(5)
                        continue

            # Error handling
            if retry >= 3:
                index += 1
                count += 1
                continue

            last_date_list = datetime.datetime(*last_date_list[:6])
            last_date = now - datetime.timedelta(days)

            datetime_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Append each entry to the dictionary
            n = 0
            print(f"Last posting: {ext_dates[-1]}")
            for i in ext_links:
                jobs_dict["Title"].append(ext_titles[n])
                jobs_dict["Company"].append(ext_companies[n])
                jobs_dict["Location"].append(ext_locations[n])
                jobs_dict["Salary"].append(ext_salaries[n])
                jobs_dict["Date Posted"].append(ext_dates[n])
                jobs_dict["Datetime Retrieved"].append(datetime_now)
                jobs_dict["Link"].append(ext_links[n])
                jobs_dict["Snippet"].append(ext_snippets[n])
                jobs_dict["Query"].append(query)
                jobs_dict["Select"].append("")
                n += 1

            index += 1
            count += 1
            sleep(randint(50, 150) / 100)
            if last_date_list >= last_date and testing == 0:
                continue
            else:
                break

        # Wait between queries, unless it's the last query
        if query != job_queries[-1]:
            rand = randint(1, 5)
            print(f"Waiting {rand} seconds")
            sleep(rand)

    return jobs_dict


if __name__ == "__main__":
    jobs_dict = job_search_time(job_queries=["Data Engineer"], testing=1)

    from jobanalysis import jobs_save

    jobs_save(jobs_dict)
