#!/usr/bin/env python3

import argparse
import logging
import sys
import time
from collections import defaultdict
from urllib.parse import urlparse

import requests
import yaml


# Define some constants
CHECK_INTERVAL = 15  # seconds
HTTP_TIMEOUT = 0.5  # 500ms

# Set up logger
logger = logging.getLogger(__name__)


class Endpoint:
    """Class representing an HTTP endpoint to be monitored."""
    
    def __init__(self, name, url, method="GET", headers=None, body=None):
        self.name = name
        self.url = url
        self.method = method
        self.headers = headers or {}  # Use empty dict if headers is None
        self.body = body
        
        # Extract domain from URL, ignoring port if present
        url_parts = urlparse(url)
        self.domain = url_parts.netloc.split(':')[0]
        
        # Counters for availability calculation
        self._success_count = 0
        self._check_count = 0
    
    def check_availability(self):
        """
        Check if endpoint is available based on:
        - Status code 200-299
        - Response time <= 500ms
        """
        self._check_count += 1
        
        try:
            # Record start time for response time calculation
            start = time.time()
            
            # Make the request with timeout
            response = requests.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                data=self.body,
                timeout=HTTP_TIMEOUT
            )
            
            # Calculate response time
            elapsed = time.time() - start
            
            # Check status code and response time
            if 200 <= response.status_code < 300 and elapsed <= HTTP_TIMEOUT:
                self._success_count += 1
                return True
            return False
            
        except requests.RequestException:
            # Any request exception means the endpoint is unavailable
            return False
    
    def get_availability(self):
        """Calculate the availability percentage as an integer."""
        if self._check_count == 0:
            return 0
        
        # Calculate and truncate decimal portion
        return int((self._success_count / self._check_count) * 100)


def load_config(file_path):
    """Load and parse the YAML configuration file."""
    try:
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        
        if not isinstance(config, list):
            logger.error("Invalid configuration format. Expected a list of endpoints.")
            return []
            
        endpoints = []
        for i, cfg in enumerate(config):
            # Validate required fields
            if 'name' not in cfg or 'url' not in cfg:
                logger.warning(f"Skipping endpoint #{i+1}: missing required fields")
                continue
                
            # Create endpoint instance
            endpoint = Endpoint(
                name=cfg['name'],
                url=cfg['url'],
                method=cfg.get('method', 'GET'),
                headers=cfg.get('headers'),
                body=cfg.get('body')
            )
            endpoints.append(endpoint)
            
        return endpoints
        
    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Failed to load configuration: {e}")
        return []


def check_all_endpoints(endpoints):
    """Check all endpoints and calculate domain availability."""
    # Use defaultdict to collect domain statistics
    domain_stats = defaultdict(lambda: {'success': 0, 'total': 0})
    
    # Check each endpoint
    for ep in endpoints:
        is_available = ep.check_availability()
        
        # Update domain statistics
        domain_stats[ep.domain]['total'] += 1
        if is_available:
            domain_stats[ep.domain]['success'] += 1
    
    # Calculate availability percentage for each domain
    domain_availability = {}
    for domain, stats in domain_stats.items():
        if stats['total'] == 0:
            availability = 0
        else:
            # Integer division to drop decimal portion
            availability = int((stats['success'] / stats['total']) * 100)
        domain_availability[domain] = availability
    
    return domain_availability


def monitor_loop(endpoints):
    """Main monitoring loop that runs indefinitely."""
    if not endpoints:
        logger.error("No valid endpoints to monitor!")
        return
        
    logger.info(f"Starting monitoring of {len(endpoints)} endpoints...")
    
    try:
        while True:
            # Check all endpoints
            domain_availability = check_all_endpoints(endpoints)
            
            # Log domain availability
            logger.info("=== Domain Availability ===")
            for domain, avail in domain_availability.items():
                logger.info(f"{domain}: {avail}%")
            
            # Log individual endpoint availability
            logger.info("=== Endpoint Availability ===")
            for ep in endpoints:
                logger.info(f"{ep.name}: {ep.get_availability()}%")
                
            # Wait for next check cycle
            time.sleep(CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user.")


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Monitor HTTP endpoint availability"
    )
    parser.add_argument(
        "config_file", 
        help="Path to YAML configuration file"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Load configuration
    endpoints = load_config(args.config_file)
    
    if not endpoints:
        sys.exit(1)
        
    # Start monitoring
    monitor_loop(endpoints)


if __name__ == "__main__":
    main()
