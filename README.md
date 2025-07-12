# A Job Scraper for Indeed

## Background
Going through job listings drives me a bit crazy, because most of what I'm trying to do could be sped up considerably if I wasn't dealing with indeed's, frankly, awful search.

I wanted to improve on this process by writing a program that could actually deliver me the kinds of results I want, in the format I want it:

1. A list of recently posted jobs with basic information: title, company, location, salarly, date posted, and a quick blurb
2. Jobs that are better matched to the actual query I've put in: I'm not looking to work as a receptionist, so I'd rather not see _any_ listing with that in the title
3. A way to quickly sort through and rank the jobs that have been posted.

This program attempts to solve the above:
1. It searches through indeed on a base query, given a time range
2. The jobs are first filtered through a list of [user-supplied filters](/filters.txt), then filtered again by fuzzy matching the job title to the original query, catching the vast majority of unrelated results
3. A very basic user interface allows you to look through the important bits of each job then rank each by preference. Following ranking, each job is copied to the system clipboard so that you may look at each selection in greater detail.

## Usage

### Requirements

The program is built in Python 3.9, and relies on the following external packages:

| Package | Usage |
| - | - |
| Urllib | Dynamically builds URLs |
| Selenium | Scrapes the website |
| undetected-chromedriver | Bypasses CloudFlare's anti-bot protection |
| bs4 | BeautifulSoup: parses html files and retrieves text |
| pandas | Manages and filters lists of selected jobs |
| fuzzywuzzy | Applies fuzzy matching to job titles |
| pyperclip | Copies job links to clipboard after sorting |

You'll also need to have: 
- Chrome or a [chromedriver](https://chromedriver.chromium.org/downloads) installed for undetected-chromedriver
- a ```jobs.txt``` file in the same folder as main.py: it's a text file with a list of search queries, separated by line. If your query is more than one word, separate it with spaces or a "+". Case doesn't matter. It should look something like the below:

```
Janitor
Head of Janitorial Services
Zamboni Driver
Bodyguard
secret agent
```

- You may also want to edit the filters in a file called filters.txt, also in the same folder as main.py. These filters will remove jobs from consideration if they contain a word in the list. I have a few set for myself, but you should tailor this to your requirements. It should look something like the below:

```python
assistant
bartender
director
executive
```

The program automatically filters jobs based on fuzzy matching between the job title and query you set up in ```jobs.txt```, which should remove the vast majority of irrevalant results. You can fine-tune this filter in line 64 of [jobanalysis.py](https://github.com/sam-hatley/jobsearch/blob/master/jobanalysis.py#L64), which is currently set to 75(%) using fuzzywuzzy's `token_set_ratio()`.

### Files

This is made up of three files:

| File | Description |
| - | - |
| [main.py](main.py) | The file used to run the program. It calls functions within the other two files to allow a text-based user interface for fetching and sorting jobs. |
| [jobscrape.py](jobscrape.py) | Stores functions related to scraping Indeed |
| [jobanalysis.py](jobanalysis.py) | Stores functions related to handling the output of jobscrape.py |

### Running the Program

I would highly recommend running this behind a VPN: although I've done as much as I can to slow down the scraping process, Indeed isn't fond of scraping software and may block your IP if you use this frequently.

1. After installing any [dependencies](#requirements), run [main.py](main.py).
2. It will ask you if you want to scrape or load. If it's your first time running the program, choose scrape (s).
3. Choose a number of days to scrape jobs: if you select 1, it will search for jobs posted between yesterday and today. Type any number above 0.
4. The program will go through your list of jobs, and search each one until it hits the number of days you've specified. Don't worry if you get an error in the process: I haven't explicitly built in a way of handling "no results" pages, but the program will continue to work even if it hits one.
5. Go ahead and take a look at the results. Plug in a number to "rate" the job. If you're finished before going through the results, type "q".
6. You'll see a list with the job titles and links in the program: you can take a look through them here, or just go to the generated file ```selects_YYYY-MM-DD.csv``` to look through them later. Following a search, each link is also sent to the system clipboard: I'd recommend a browser add-on like ["Open Multiple URLs"](https://addons.mozilla.org/en-US/firefox/addon/open-multiple-urls/) to go through the batch at once. All jobs and ratings are stored in ```joblist.pkl```, which you can export to csv at your leisure using the program.

Roughly, this is what the program looks like:

```
(S)crape new jobs, (L)oad old jobs, or (E)xport jobs?: s
Number of days ago to search jobs? 1
Retrieving results 1-15 for Janitor
Last posting: 2022-10-20

Press enter to continue to job sorting or anything else to quit: 
Number of days ago to display search results? 1

Result 1 of 535: Janitor
Title             Weekend Cleaner/Janitor
Company              Hayward Services Ltd
Location                      London SW15
Salary                     £18,642 a year
Date Posted           2022-10-27 00:00:00
Name: 0, dtype: object

Emptying waste bins or similar receptacles, transporting waste material to designated collection points.
Scheduled spot checks of washroom facilities. Monitoring consumable levels and addressing any cleaning / hygiene issues.

Type an integer rating if interested. Enter or 0 to reject. (Q) to quit: 1


Result 2 of 535: Janitor
Title             Janitor with Driving License
Company              Essential Results Limited
Location                          Brighton BN1
Salary                £20,500 - £22,700 a year
Date Posted                2022-10-26 00:00:00
Name: 3, dtype: object

In your new role as a Janitor with Driving License you will ensure equipment is kept clean, well maintained and in safe working order and meeting all agreed SLAs.

Type an integer rating if interested. Enter or 0 to reject. (Q) to quit: 2


Result 3 of 535: Janitor
Title                        Night Cleaner
Company           Britannia Services Group
Location                         Rochester
Salary                         £11 an hour
Date Posted            2022-10-25 00:00:00
Name: 5, dtype: object

We are seeking a experienced cleaner to work Monday to Friday cleaning my clents premises in Isle of Grain Kent .
Commercial cleaning: 1 year (preferred).

Type an integer rating if interested. Enter or 0 to reject. (Q) to quit: q

Selected jobs saved to selects_2023-06-12.csv.
Selected job links copied to clipboard.
                          Title                    Company Date Posted  ... Time Retrieved                                               Link Select
3  Janitor with Driving License  Essential Results Limited  2022-10-26  ...       10:35:36  https://uk.indeed.com/viewjob?jk=0e591257c2b7f3ac    2.0
0       Weekend Cleaner/Janitor       Hayward Services Ltd  2022-10-27  ...       10:41:32  https://uk.indeed.com/viewjob?jk=d6a6ea7051082f9d    1.0

[2 rows x 7 columns]
```
