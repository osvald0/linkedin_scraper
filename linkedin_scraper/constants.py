class LinkedInConstants:
    BASE_URL = "https://www.linkedin.com"
    LOGIN_URL = f"{BASE_URL}/login"
    JOBS_SEARCH_URL = f"{BASE_URL}/jobs/search"
    JOB_VIEW_URL = f"{BASE_URL}/jobs/view"

    JOB_LIST_CLASS = "jobs-search__results-list"
    JOB_TITLE_CLASS = "top-card-layout__title"
    COMPANY_NAME_CLASS = "topcard__org-name-link"
    LOCATION_CLASS = "topcard__flavor--bullet"
    DESCRIPTION_CLASS = "description__text"

    REQUEST_DELAY = 3
