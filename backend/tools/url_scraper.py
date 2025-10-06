import asyncio
import csv
import os
import re
from typing import List, Dict, Optional, Tuple, Set
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, field_validator
from langchain.tools import tool

# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

class ScraperConfig:
    """Centralized configuration for the scraper."""
    
    # HTTP Configuration
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    # Async Configuration
    MAX_CONCURRENT_REQUESTS = 10
    SEMAPHORE_LIMIT = 5
    
    # Retry Configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    BACKOFF_FACTOR = 2
    
    # Timeout Configuration
    CONNECTION_TIMEOUT = 10
    READ_TIMEOUT = 20
    TOTAL_TIMEOUT = 30
    
    # Content Configuration
    MAX_PAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_CONTACT_PAGE_SIZE = 5 * 1024 * 1024  # 5MB
    
    # Domain Configuration
    EXCLUDED_DOMAINS = {
        'example.com', 'example.org', 'localhost',
        'test.com', 'dummy.com', 'placeholder.com'
    }
    
    # Contact Keywords
    CONTACT_KEYWORDS = [
        'contact', 'about', 'reach-us', 'get-in-touch',
        'connect', 'support', 'help', 'contactus'
    ]

# ============================================================================
# PHONE NUMBER PATTERNS (COMPREHENSIVE)
# ============================================================================

class PhonePatterns:
    """Comprehensive international phone number patterns."""
    
    PATTERNS = [
        # International format with country code
        r'\+\d{1,4}[\s.-]?\(?\d{1,5}\)?[\s.-]?\d{1,5}[\s.-]?\d{1,5}[\s.-]?\d{0,5}',
        
        # US/Canada format: (555) 123-4567 or 555-123-4567
        r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
        
        # UK format: 020 1234 5678 or +44 20 1234 5678
        r'\+?44[\s.-]?\d{2,4}[\s.-]?\d{3,4}[\s.-]?\d{3,4}',
        
        # India format: +91 98765 43210 or 022-12345678
        r'\+?91[\s.-]?\d{10}',
        r'\d{2,4}[\s.-]?\d{6,8}',
        
        # European format: +33 1 23 45 67 89
        r'\+?\d{2,4}[\s.-]?\d{1,3}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
        
        # Generic international
        r'\+\d{1,4}[\s.-]?\d{4,14}',
        
        # Parentheses format: (123) 456-7890
        r'\(\d{2,5}\)[\s.-]?\d{3,5}[\s.-]?\d{3,5}',
        
        # Simple 10-15 digit numbers
        r'\b\d{10,15}\b',
        
        # Dotted format: 123.456.7890
        r'\d{3,5}\.\d{3,5}\.\d{3,5}',
        
        # Toll-free numbers: 1-800-123-4567
        r'1[\s.-]?[8(00)][\s.-]?\d{3}[\s.-]?\d{4}',

        # 5 + 5 digit format (e.g., 96242 43941)
        r'\d{5}[\s.-]?\d{5}',

        # International format with country code and hyphens
        r'\+\d{1,4}[-\s]?\d{2,5}[-\s]?\d{5,10}',
        
        # International format with country code
        r'\+\d{1,4}[\s.-]?\(?\d{1,5}\)?[\s.-]?\d{1,5}[\s.-]?\d{1,5}[\s.-]?\d{0,5}',
    ]
    
    # Compile patterns for better performance
    COMPILED_PATTERNS = [re.compile(pattern) for pattern in PATTERNS]
    
    # Invalid patterns to filter out
    INVALID_PATTERNS = [
        r'^0+$',  # All zeros
        r'^1+$',  # All ones
        r'^(\d)\1+$',  # All same digit (corrected)
        r'^(123|111|000|999)+$',  # Sequential/repeated
    ]
    
    COMPILED_INVALID = [re.compile(pattern) for pattern in INVALID_PATTERNS]
    

# ============================================================================
# DATA MODELS
# ============================================================================

class ScrapeStatus(str, Enum):
    """Status codes for scraping operations."""
    SUCCESS = "Success"
    FAILED_CONNECTION = "Failed: Connection Error"
    FAILED_TIMEOUT = "Failed: Timeout"
    FAILED_INVALID_DOMAIN = "Failed: Invalid Domain"
    FAILED_SSL = "Failed: SSL Error"
    FAILED_DNS = "Failed: DNS Resolution"
    FAILED_NO_DATA = "Success: No Contact Data"
    FAILED_SCRAPING = "Failed: Scraping Error"
    SKIPPED_NO_WEBSITE = "Skipped: No Website Available"

@dataclass
class ContactInfo:
    """Contact information extracted from a website."""
    emails: Set[str] = field(default_factory=set)
    phones: Set[str] = field(default_factory=set)
    
    def add_email(self, email: str):
        """Add email with validation."""
        if self._is_valid_email(email):
            self.emails.add(email.lower())
    
    def add_phone(self, phone: str):
        """Add phone with validation."""
        if self._is_valid_phone(phone):
            self.phones.add(phone)
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Validate email address."""
        if not email or len(email) > 254:
            return False
        
        # Exclude common noise domains
        excluded = ['example.com', 'sentry.io', 'schema.org', 'placeholder.com']
        if any(domain in email.lower() for domain in excluded):
            return False
        
        # Basic validation
        return '@' in email and '.' in email.split('@')[1]
    
    @staticmethod
    def _is_valid_phone(phone: str) -> bool:
        """Validate phone number."""
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Length check
        if len(cleaned) < 10 or len(cleaned) > 15:
            return False
        
        # Check for invalid patterns
        for pattern in PhonePatterns.COMPILED_INVALID:
            if pattern.match(cleaned):
                return False
        
        return True
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for CSV output."""
        return {
            'Email': ', '.join(sorted(self.emails)[:5]) or 'N/A',
            'Phone': ', '.join(sorted(self.phones)[:5]) or 'N/A'
        }

@dataclass
class ScrapeResult:
    """Result of scraping a single website."""
    title: str
    original_url: str
    working_url: Optional[str]
    contact_info: ContactInfo
    status: ScrapeStatus
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for CSV output."""
        contact_dict = self.contact_info.to_dict()
        return {
            'Title': self.title,
            'Working_URL': self.working_url or 'N/A',
            'Email': contact_dict['Email'],
            'Phone': contact_dict['Phone']
        }

class ScraperInput(BaseModel):
    """Input schema for the website scraper tool."""
    input_csv_path: str = Field(
        description="Path to the input CSV file containing Title and Website columns"
    )
    title_column: str = Field(
        default="Title",
        description="Name of the column containing business titles"
    )
    website_column: str = Field(
        default="Website",
        description="Name of the column containing website URLs"
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout in seconds for each request"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Maximum number of retry attempts per URL variant"
    )
    max_concurrent: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent requests"
    )
    
    @field_validator('input_csv_path')
    def validate_csv_path(cls, v):
        if not os.path.exists(v):
            raise ValueError(f"Input CSV file not found: {v}")
        if not v.endswith('.csv'):
            raise ValueError("Input file must be a CSV file")
        return v

class ScraperOutput(BaseModel):
    """Output schema for the scraper tool."""
    output_path: str = Field(description="Path to the generated CSV file")
    message: str = Field(description="Summary of the scraping operation")
    total_processed: int = Field(description="Total number of websites processed")
    successful: int = Field(description="Number of successful scrapes with contact data")
    failed: int = Field(description="Number of failed scrapes")
    no_data: int = Field(description="Number of successful connections but no data found")
    skipped: int = Field(description="Number of entries skipped due to no website")
    duration_seconds: float = Field(description="Total execution time in seconds")

# ============================================================================
# URL UTILITIES
# ============================================================================

class URLProcessor:
    """Handles URL cleaning and variant generation."""
    
    @staticmethod
    def clean_domain(domain: str) -> Optional[str]:
        """Clean and normalize domain name."""
        if not domain:
            return None
        
        # Clean up the domain string
        domain = str(domain).strip()
        
        # Check for common "no website" indicators
        no_website_indicators = [
            "not available", "n/a", "na", "none", "no website", 
            "unavailable", "missing", "null", "-"
        ]
        
        if domain.lower() in no_website_indicators:
            return None
        
        # Remove all non-ASCII characters and whitespace
        domain = domain.encode('ascii', 'ignore').decode('ascii')
        domain = ''.join(domain.split()).strip().lower()
        
        if not domain:
            return None
        
        # Remove protocol if present
        if domain.startswith(('http://', 'https://')):
            try:
                parsed = urlparse(domain)
                domain = parsed.netloc if parsed.netloc else parsed.path
            except Exception:
                pass
        
        # Remove trailing slash and path
        domain = domain.split('/')[0]
        
        # Remove port if present
        domain = domain.split(':')[0]
        
        # Validate domain structure
        if not domain or '.' not in domain or len(domain) < 4:
            return None
        
        # Remove any remaining invalid characters
        domain = re.sub(r'[^a-z0-9.-]', '', domain)
        
        # Check against excluded domains
        if domain in ScraperConfig.EXCLUDED_DOMAINS:
            return None
        
        return domain
    
    @staticmethod
    def generate_url_variants(domain: str) -> List[str]:
        """Generate multiple URL variants to try."""
        variants = []
        
        # Remove www if present to create base domain
        base_domain = domain[4:] if domain.startswith('www.') else domain
        
        # HTTPS variants (preferred)
        variants.append(f"https://www.{base_domain}")
        variants.append(f"https://{base_domain}")
        
        # HTTP variants (fallback)
        variants.append(f"http://www.{base_domain}")
        variants.append(f"http://{base_domain}")
        
        return variants

# ============================================================================
# CONTENT EXTRACTORS
# ============================================================================

class ContentExtractor:
    """Extracts contact information from HTML content."""
    
    @staticmethod
    def extract_phone_numbers(text: str) -> Set[str]:
        """Extract phone numbers using comprehensive patterns."""
        if not text:
            return set()
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        phones = set()
        
        for pattern in PhonePatterns.COMPILED_PATTERNS:
            matches = pattern.findall(text)
            for match in matches:
                # Clean the match
                cleaned = re.sub(r'[^\d+]', '', match)
                
                # Validate length
                if 10 <= len(cleaned) <= 15:
                    # Check if it's not an invalid pattern
                    is_valid = True
                    for invalid_pattern in PhonePatterns.COMPILED_INVALID:
                        if invalid_pattern.match(cleaned):
                            is_valid = False
                            break
                    
                    if is_valid:
                        phones.add(cleaned)
        
        return phones
    
    @staticmethod
    def extract_emails(text: str) -> Set[str]:
        """Extract email addresses from text."""
        if not text:
            return set()
        
        # Comprehensive email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = set(re.findall(email_pattern, text, re.IGNORECASE))
        
        # Filter out common noise and invalid emails
        filtered = set()
        for email in emails:
            email_lower = email.lower()
            
            # Exclude noise domains
            if any(x in email_lower for x in ['example.com', 'sentry.io', 'schema.org', 
                                                'placeholder.com', 'yourdomain.com',
                                                'yourcompany.com', 'domain.com']):
                continue
            
            # Basic validation
            if '@' in email and '.' in email.split('@')[1]:
                filtered.add(email_lower)
        
        return filtered
    
    @staticmethod
    def extract_from_soup(soup: BeautifulSoup) -> ContactInfo:
        """Extract contact info from BeautifulSoup object."""
        contact_info = ContactInfo()
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'noscript', 'iframe', 'svg']):
            element.decompose()
        
        # Priority 1: Footer (More Robust Search)
        footer = soup.find('footer')
        if not footer:
            # Look for common footer-like sections or divs by class or id
            footer = soup.find(['section', 'div'], id=re.compile(r'footer', re.I)) \
                    or soup.find(['section', 'div'], class_=re.compile(r'footer', re.I))
        
        # If still no footer, try a broader search for common footer keywords
        if not footer:
            footer = soup.find(['section', 'div'], class_=re.compile(r'my-footer|site-footer|bottom-footer|main-footer|footer-bottom', re.I))

        if footer:
            # Extract from footer text
            footer_text = footer.get_text(" ", strip=True)
            for phone in ContentExtractor.extract_phone_numbers(footer_text):
                contact_info.add_phone(phone)
            for email in ContentExtractor.extract_emails(footer_text):
                contact_info.add_email(email)
            
            # Extract from mailto: links in footer
            for link in footer.find_all('a', href=True):
                href = link['href']
                if href.startswith('mailto:'):
                    email = href.replace('mailto:', '').split('?')[0].strip()
                    contact_info.add_email(email)
        
        # Priority 2: Extract from all mailto: links in the page (important fix)
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('mailto:'):
                email = href.replace('mailto:', '').split('?')[0].strip()
                contact_info.add_email(email)
            elif href.startswith('tel:'):
                phone = href.replace('tel:', '').strip()
                contact_info.add_phone(phone)
        
        # Priority 3: Meta tags and structured data
        for meta in soup.find_all('meta', attrs={'name': re.compile(r'contact|email|phone', re.I)}):
            content = meta.get('content', '')
            for phone in ContentExtractor.extract_phone_numbers(content):
                contact_info.add_phone(phone)
            for email in ContentExtractor.extract_emails(content):
                contact_info.add_email(email)
        
        # Priority 4: Anchor tags with tel: and mailto:
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('tel:'):
                phone = href.replace('tel:', '').strip()
                contact_info.add_phone(phone)
            elif href.startswith('mailto:'):
                email = href.replace('mailto:', '').split('?')[0].strip()
                contact_info.add_email(email)
        
        # If still no data, scan entire page
        if not contact_info.emails and not contact_info.phones:
            full_text = soup.get_text(" ", strip=True)
            for phone in ContentExtractor.extract_phone_numbers(full_text):
                contact_info.add_phone(phone)
            for email in ContentExtractor.extract_emails(full_text):
                contact_info.add_email(email)
        
        return contact_info

# ============================================================================
# ASYNC WEB SCRAPER
# ============================================================================

class AsyncWebScraper:
    """Asynchronous website scraper with connection pooling and debug output."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, max_concurrent: int = 10):
        self.timeout = aiohttp.ClientTimeout(
            total=timeout,
            connect=ScraperConfig.CONNECTION_TIMEOUT,
            sock_read=ScraperConfig.READ_TIMEOUT
        )
        self.max_retries = max_retries
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        connector = aiohttp.TCPConnector(
            limit=ScraperConfig.MAX_CONCURRENT_REQUESTS,
            limit_per_host=5,
            ttl_dns_cache=300,
            ssl=False  # Allow insecure SSL for broader compatibility
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers=ScraperConfig.HEADERS
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def fetch_url(self, url: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fetch URL with retries.
        Returns: (content, final_url, error_message)
        """
        for attempt in range(self.max_retries):
            try:
                async with self.session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        # Check content size
                        content_length = response.headers.get('Content-Length')
                        if content_length and int(content_length) > ScraperConfig.MAX_PAGE_SIZE:
                            return None, None, "Page too large"
                        
                        content = await response.text()
                        return content, str(response.url), None
                    else:
                        error = f"HTTP {response.status}"
                        if attempt == self.max_retries - 1:
                            return None, None, error
                        
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    return None, None, "Timeout"
                await asyncio.sleep(ScraperConfig.RETRY_DELAY * (ScraperConfig.BACKOFF_FACTOR ** attempt))
                
            except aiohttp.ClientError as e:
                if attempt == self.max_retries - 1:
                    return None, None, f"Connection error: {str(e)[:50]}"
                await asyncio.sleep(ScraperConfig.RETRY_DELAY * (ScraperConfig.BACKOFF_FACTOR ** attempt))
                
            except Exception as e:
                return None, None, f"Unexpected error: {str(e)[:50]}"
        
        return None, None, "All retries failed"
    
    async def get_working_url(self, domain: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Find working URL from domain variants.
        Returns: (content, working_url, error_message)
        """
        cleaned_domain = URLProcessor.clean_domain(domain)
        
        if not cleaned_domain:
            return None, None, "Invalid domain"
        
        url_variants = URLProcessor.generate_url_variants(cleaned_domain)
        
        for variant in url_variants:
            content, final_url, error = await self.fetch_url(variant)
            if content:
                return content, final_url, None
        
        return None, None, "No working URL found"
    
    async def scrape_contact_page(self, base_url: str, soup: BeautifulSoup) -> ContactInfo:
        """Scrape contact page if main page has no info."""
        contact_info = ContactInfo()
        
        # Find contact links
        contact_links = soup.find_all('a', href=re.compile(
            r'(' + '|'.join(ScraperConfig.CONTACT_KEYWORDS) + r')', re.I
        ))
        
        for link in contact_links[:2]:  # Limit to first 2 contact pages
            try:
                contact_url = link.get('href')
                if not contact_url:
                    continue
                
                # Make absolute URL
                if not contact_url.startswith('http'):
                    contact_url = urljoin(base_url, contact_url)
                
                content, _, error = await self.fetch_url(contact_url)
                if content:
                    contact_soup = BeautifulSoup(content, 'html.parser')
                    page_info = ContentExtractor.extract_from_soup(contact_soup)
                    
                    contact_info.emails.update(page_info.emails)
                    contact_info.phones.update(page_info.phones)
                    
                    # If we found data, stop searching
                    if contact_info.emails or contact_info.phones:
                        break
                        
            except Exception as e:
                continue
        
        return contact_info
    
    async def scrape_website(self, title: str, domain: str) -> ScrapeResult:
        """Scrape a single website for contact information."""
        async with self.semaphore:
            # Check if domain is valid before attempting to scrape
            cleaned_domain = URLProcessor.clean_domain(domain)
            if not cleaned_domain:
                return ScrapeResult(
                    title=title,
                    original_url=domain,
                    working_url=None,
                    contact_info=ContactInfo(),
                    status=ScrapeStatus.SKIPPED_NO_WEBSITE,
                    error_message="No valid website provided"
                )
            
            # Get working URL and content
            content, working_url, error = await self.get_working_url(domain)
            
            if not content or not working_url:
                status = ScrapeStatus.FAILED_CONNECTION
                if error and 'timeout' in error.lower():
                    status = ScrapeStatus.FAILED_TIMEOUT
                elif error and 'ssl' in error.lower():
                    status = ScrapeStatus.FAILED_SSL
                elif error and 'invalid domain' in error.lower():
                    status = ScrapeStatus.FAILED_INVALID_DOMAIN
                
                return ScrapeResult(
                    title=title,
                    original_url=domain,
                    working_url=None,
                    contact_info=ContactInfo(),
                    status=status,
                    error_message=error
                )
            
            # =================================================================
            # DEBUG: SAVE THE FETCHED HTML TO A FILE
            # =================================================================
            try:
                # Create a safe filename from the title
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
                debug_filename = f"debug_{safe_title}.html"
                with open(debug_filename, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"🔍 DEBUG: Saved fetched HTML for '{title}' to '{debug_filename}'")
            except Exception as e:
                print(f"⚠️ Could not save debug file for '{title}': {e}")
            # =================================================================

            try:
                # Parse HTML
                soup = BeautifulSoup(content, 'html.parser')
                
                # Extract contact info from main page
                contact_info = ContentExtractor.extract_from_soup(soup)
                
                # If no data found, try contact pages
                if not contact_info.emails and not contact_info.phones:
                    contact_page_info = await self.scrape_contact_page(working_url, soup)
                    contact_info.emails.update(contact_page_info.emails)
                    contact_info.phones.update(contact_page_info.phones)
                
                status = ScrapeStatus.SUCCESS if (contact_info.emails or contact_info.phones) else ScrapeStatus.FAILED_NO_DATA
                
                return ScrapeResult(
                    title=title,
                    original_url=domain,
                    working_url=working_url,
                    contact_info=contact_info,
                    status=status
                )
                
            except Exception as e:
                return ScrapeResult(
                    title=title,
                    original_url=domain,
                    working_url=working_url,
                    contact_info=ContactInfo(),
                    status=ScrapeStatus.FAILED_SCRAPING,
                    error_message=str(e)[:100]
                )

# ============================================================================
# MAIN PROCESSOR
# ============================================================================

async def process_websites_async(
    input_csv_path: str,
    title_column: str = "Title",
    website_column: str = "Website",
    timeout: int = 30,
    max_retries: int = 3,
    max_concurrent: int = 10
) -> ScraperOutput:
    """Main async processing function."""
    
    start_time = datetime.now()
    
    # Read input CSV
    rows = []
    try:
        with open(input_csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        raise
    
    total = len(rows)
    
    # Create scraper and process all websites concurrently
    async with AsyncWebScraper(timeout=timeout, max_retries=max_retries, max_concurrent=max_concurrent) as scraper:
        tasks = [
            scraper.scrape_website(
                title=row.get(title_column, "").strip(),
                domain=row.get(website_column, "").strip()
            )
            for row in rows
        ]
        
        results = await asyncio.gather(*tasks)
    
    # Calculate statistics
    successful = sum(1 for r in results if r.status == ScrapeStatus.SUCCESS)
    no_data = sum(1 for r in results if r.status == ScrapeStatus.FAILED_NO_DATA)
    failed = sum(1 for r in results if r.status in [
        ScrapeStatus.FAILED_CONNECTION, ScrapeStatus.FAILED_TIMEOUT,
        ScrapeStatus.FAILED_INVALID_DOMAIN, ScrapeStatus.FAILED_SSL,
        ScrapeStatus.FAILED_DNS, ScrapeStatus.FAILED_SCRAPING
    ])
    skipped = sum(1 for r in results if r.status == ScrapeStatus.SKIPPED_NO_WEBSITE)
    
    # Generate output filename - Changed to email_phone.csv
    output_dir = os.path.dirname(input_csv_path) or '.'
    base_name, ext = os.path.splitext(os.path.basename(input_csv_path))
    output_filename = f"{base_name}_email_phone{ext}"
    output_path = os.path.join(output_dir, output_filename)

    
    # Save results - Changed fieldnames to only include Title, Working_URL, Email, Phone
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Title', 'Working_URL', 'Email', 'Phone']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows([r.to_dict() for r in results])
    
    duration = (datetime.now() - start_time).total_seconds()
    
    message = (f"Processed {total} websites in {duration:.2f}s. "
               f"Success: {successful}, No Data: {no_data}, Failed: {failed}, Skipped: {skipped}")
    
    return ScraperOutput(
        output_path=os.path.abspath(output_path),
        message=message,
        total_processed=total,
        successful=successful,
        failed=failed,
        no_data=no_data,
        skipped=skipped,
        duration_seconds=duration
    )

# ============================================================================
# LANGGRAPH TOOL
# ============================================================================

@tool("WebsiteScraper-Tool", args_schema=ScraperInput, return_direct=False)
async def scrape_website(
    input_csv_path: str,
    title_column: str = "Title",
    website_column: str = "Website",
    timeout: int = 30,
    max_retries: int = 3,
    max_concurrent: int = 10
) -> str:  
    """
    website scraper for extracting email and phone contacts.
    
    Args:
        input_csv_path: Path to CSV with Title and Website columns
        title_column: Column name for business titles (default: "Title")
        website_column: Column name for website URLs (default: "Website")
        timeout: Request timeout in seconds (default: 30)
        max_retries: Retry attempts per URL (default: 3)
        max_concurrent: Maximum concurrent requests (default: 10)
    
    Returns:
        str: Path to the output CSV file with extracted contacts
    
    Example:
        Input: businesses.csv with Title,Website columns
        Output: email_phone.csv with extracted contacts
    """
    result = await process_websites_async(
        input_csv_path=input_csv_path,
        title_column=title_column,
        website_column=website_column,
        timeout=timeout,
        max_retries=max_retries,
        max_concurrent=max_concurrent
    )
    return result.output_path