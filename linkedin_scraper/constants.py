class LinkedInConstants:
    BASE_URL = "https://www.linkedin.com"

    LOGIN_URL = f"{BASE_URL}/login"
    JOBS_SEARCH_URL = f"{BASE_URL}/jobs/search"

    JOB_ID_ATTRIBUTE = "data-job-id"
    NEXT_PAGE_BUTTON_CSS = "li.active + li"
    DESCRIPTION_CLASS = "jobs-description__content"
    JOBS_SEARCH_FOOTER_ID = "jobs-search-results-footer"
    JOB_LIST_CSS = '[data-job-id]:not([data-job-id="search"])'
    JOB_TITLE_CLASS = "job-details-jobs-unified-top-card__job-title"
    COMPANY_NAME_CLASS = "job-details-jobs-unified-top-card__company-name"
    LOCATION_CLASS = "job-details-jobs-unified-top-card__primary-description-container"

    WAIT_SHORT = 5
    WAIT_MEDIUM = 10
    WAIT_LONG = 15
