# LinkedIn Job Scraper

## Why?

Created for personal use while job hunting with the goal of finding opportunities
offering relocation and visa sponsorship. LinkedIn lacks a direct filter for
these criteria, but companies often mention them in job descriptions.
This scraper helps identify those opportunities by scanning descriptions for
relevant keywords.

## Current Status

This is the initial version of the tool, focused on scraping job postings and
storing the results in a database. However, there are some known issues:

~~- **Selector Changes:** Some LinkedIn selectors have been updated, causing
the scraper to retrieve elements that do not correspond to job cards.~~
It's working now (Jan 26 2025)

- **Testing Challenges:** Testing is limited due to LinkedIn's rate limits
  and additional security checks required after login.

I’m actively working on fixing these issues to improve the tool’s reliability.

## Future Plans

The roadmap for this project includes the following enhancements:

1. **Improved Scraping Logic:** Resolve current issues with selectors to ensure
   accurate job card retrieval.
2. **Frontend Interface:** Build a user-friendly interface to view and manage
   the scraped results.
3. **Job Application Tracker:** Add features to track job applications, including
   statuses such as "Applied," "Interviewing," or "Rejected."
4. **Advanced Filters:** Introduce more robust filtering options to refine search
   results.

## Current Features

- Search multiple locations keys(uk, netherlands, germany and uruguay).
- Filter by posting date (24h, week, month).
- Content filtering for specific terms.
- Headless mode support.
- Stores results in SQLite or JSON file.

## Setup

1. Install dependencies:

```bash
poetry install
```

2. Configure `.env`:

E.g.:

```env
HEADLESS=true
KEYWORDS="python developer"
LOCATIONS=uk
DATE_FILTER=past_24h
CONTAINS=visa,sponsor,relocation
NON_CONTAINS=c#
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=your_password
```

## Usage

```bash
poetry run python -m linkedin_scraper
```

## Current Supported Location Codes

- uk: 101165590
- netherlands: 102890719
- germany: 101282230
- uruguay: 100867946

## Requirements

- Python 3.9+
- Poetry
- Chrome/Chromium

## Contributing

This tool is currently under active development, but contributions and feedback
are welcome. Feel free to create an issue or submit a pull request with your suggestions.

Stay tuned for updates as the tool evolves!

## License

GPL v3
