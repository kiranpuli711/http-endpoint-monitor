# HTTP Endpoint Monitor

A Python tool for monitoring HTTP endpoint availability and reporting domain-level statistics.

## Installation

### Requirements

* Python 3.6+
* pip package manager

### Setup

1. Clone the repository
git clone https://github.com/yourusername/http-endpoint-monitor.git
cd http-endpoint-monitor


2. Install dependencies
pip install -r requirements.txt


## Usage

Run the monitoring tool with your YAML configuration file:


python monitor.py config.yaml


For verbose logging:

python monitor.py config.yaml --verbose


### Configuration File Format

The configuration file should be in YAML format and contain a list of endpoints to monitor:

yaml
# Example configuration
- name: fetch rewards API
  url: https://api.example.com/endpoint
  method: GET
  
- name: login endpoint
  url: https://auth.example.com/login
  method: POST
  headers:
    content-type: application/json
  body: '{"username": "test", "password": "test"}'


Each endpoint definition supports these fields:
* `name` (required): A friendly name for the endpoint
* `url` (required): The URL to monitor
* `method` (optional): HTTP method (defaults to GET)
* `headers` (optional): HTTP headers for the request
* `body` (optional): JSON request body

## Problem Statement & Solution

### Issues Found and Fixed

#### 1. Cumulative Availability Calculation
**Problem:** The original code was only considering the latest check result, not tracking availability over time.

**Solution:** Implemented counters to track successful and total checks for proper cumulative availability calculation.

python
# Added counters to Endpoint class
self._success_count = 0
self._check_count = 0

# Increment counters on each check
self._check_count += 1
if successful:
    self._success_count += 1


#### 2. Domain Availability Reporting
**Problem:** The code wasn't calculating availability by domain as required.

**Solution:** Implemented domain extraction from the URL (ignoring port numbers) and domain-level availability aggregation.

python
# Extract domain, ignoring port
url_parts = urlparse(url)
self.domain = url_parts.netloc.split(':')[0]


#### 3. Incomplete Availability Criteria
**Problem:** Availability was only being determined by HTTP status code.

**Solution:** Updated the availability check to consider both status code (200-299) and response time (≤500ms).

python
# Check both status code and response time
if 200 <= response.status_code < 300 and elapsed <= HTTP_TIMEOUT:
    # Endpoint is available


#### 4. Timeout Handling
**Problem:** The original code didn't properly handle timeouts, which could cause monitoring to hang.

**Solution:** Added proper timeout handling and exception catching:

python
try:
    response = requests.request(
        method=self.method,
        url=self.url,
        headers=self.headers,
        data=self.body,
        timeout=HTTP_TIMEOUT  # 500ms timeout
    )
    # Process response
except requests.RequestException:
    # Handle request failure


#### 5. Decimal Truncation
**Problem:** The original code didn't truncate decimal portions of availability percentages.

**Solution:** Used integer conversion to drop decimal portions:

python
# Calculate and truncate decimal portion
return int((self._success_count / self._check_count) * 100)


#### 6. Log Interval
**Problem:** Results were being logged at inconsistent intervals.

**Solution:** Restructured the monitoring loop to check all endpoints and then log results at fixed 15-second intervals.

python
# Check all endpoints
domain_availability = check_all_endpoints(endpoints)

# Log results
logger.info("=== Domain Availability ===")
for domain, avail in domain_availability.items():
    logger.info(f"{domain}: {avail}%")

# Wait for next check cycle
time.sleep(CHECK_INTERVAL)  # 15 seconds


#### 7. Error Handling
**Problem:** The original code lacked robust error handling.

**Solution:** Added comprehensive exception handling and validation:

python
try:
    # Configuration loading
    # Request handling
    # etc.
except (yaml.YAMLError, IOError) as e:
    logger.error(f"Failed to load configuration: {e}")
except requests.RequestException:
    # Handle request failures


## Future Enhancements

* Add support for different reporting formats (JSON, CSV)
* Implement persistent storage for historical availability data
* Add alert thresholds for low availability
* Create a simple web dashboard for visualizing availability metrics
