#!/usr/bin/env python3
"""
Enhanced NREGA District/Block/Panchayat Data Scraper
Scrapes age registration employment data from NREGA reports with robust error handling
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import json
import os
from urllib.parse import urljoin, parse_qs, urlparse, urlencode
import logging
from typing import Dict, List, Optional
import argparse
import sys
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedNREGAScraper:
    def __init__(self):
        self.session = self._create_session()
        self.base_url = "https://nreganarep.nic.in/netnrega/"
        self.data = {
            'districts': [],
            'blocks': [],
            'panchayats': []
        }
        
    def _create_session(self):
        """Create a robust session with retry strategy"""
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
        
    def safe_request(self, url: str, max_retries: int = 3, delay: float = 2.0) -> Optional[requests.Response]:
        """Make a safe HTTP request with retries and error handling"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Requesting: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
                
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                    continue
                    
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    continue
                    
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
        
    def extract_asp_net_form_data(self, html_content: str) -> Dict[str, str]:
        """Extract ASP.NET form data like ViewState, EventValidation, etc."""
        soup = BeautifulSoup(html_content, 'html.parser')
        form_data = {}
        
        # Extract common ASP.NET form fields
        fields = ['__VIEWSTATE', '__VIEWSTATEGENERATOR', '__EVENTVALIDATION', '__EVENTTARGET', '__EVENTARGUMENT']
        
        for field in fields:
            element = soup.find('input', {'name': field})
            if element:
                form_data[field] = element.get('value', '')
                
        return form_data
        
    def extract_table_data(self, html_content: str) -> List[Dict]:
        """Extract data from HTML tables with improved parsing"""
        soup = BeautifulSoup(html_content, 'html.parser')
        all_data = []
        
        # Look for main content tables (exclude navigation/header tables)
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            # Skip very small tables (likely navigation or headers)
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue
                
            # Try to identify header row
            header_row = None
            data_start_idx = 0
            
            # Check first few rows for headers
            for i, row in enumerate(rows[:3]):
                cells = row.find_all(['th', 'td'])
                if cells and any(cell.find('strong') or 'district' in cell.get_text().lower() 
                               or 'block' in cell.get_text().lower() 
                               or 'panchayat' in cell.get_text().lower() for cell in cells):
                    header_row = row
                    data_start_idx = i + 1
                    break
                    
            if not header_row:
                continue
                
            # Extract headers
            headers = []
            for cell in header_row.find_all(['th', 'td']):
                header_text = cell.get_text(strip=True)
                if header_text:
                    headers.append(header_text)
                    
            if not headers:
                continue
                
            logger.info(f"Table {table_idx + 1}: Found headers: {headers[:5]}...")
            
            # Extract data rows
            for row_idx, row in enumerate(rows[data_start_idx:]):
                cells = row.find_all(['td', 'th'])
                if len(cells) != len(headers):
                    continue
                    
                row_data = {}
                has_meaningful_data = False
                
                for i, cell in enumerate(cells):
                    if i >= len(headers):
                        break
                        
                    cell_text = cell.get_text(strip=True)
                    
                    # Check for links (navigation to next level)
                    link = cell.find('a')
                    if link and link.get('href'):
                        row_data[headers[i]] = {
                            'text': cell_text,
                            'link': link.get('href')
                        }
                        has_meaningful_data = True
                    else:
                        row_data[headers[i]] = cell_text
                        
                    # Check if this cell has meaningful data
                    if cell_text and cell_text not in ['', '-', 'N/A', '0']:
                        has_meaningful_data = True
                        
                if has_meaningful_data:
                    all_data.append(row_data)
                    
        logger.info(f"Extracted {len(all_data)} data rows from {len(tables)} tables")
        return all_data
        
    def get_districts(self, state_url: str) -> List[Dict]:
        """Get list of districts from state page"""
        logger.info("Fetching districts...")
        
        response = self.safe_request(state_url)
        if not response:
            return []
            
        districts_data = self.extract_table_data(response.text)
        
        structured_districts = []
        for data_row in districts_data:
            district_info = {'state': 'MADHYA PRADESH'}
            
            # Look for district name and link
            for key, value in data_row.items():
                if isinstance(value, dict) and 'link' in value:
                    district_info['name'] = value['text']
                    district_info['link'] = value['link']
                    break
                    
            # Add other data columns
            for key, value in data_row.items():
                if not isinstance(value, dict):
                    clean_key = key.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
                    district_info[clean_key] = value
                    
            if 'name' in district_info and 'link' in district_info:
                structured_districts.append(district_info)
                
        logger.info(f"Found {len(structured_districts)} districts")
        return structured_districts
        
    def get_blocks(self, district_link: str, district_name: str) -> List[Dict]:
        """Get list of blocks from district page"""
        logger.info(f"Fetching blocks for district: {district_name}")
        
        full_url = urljoin(self.base_url, district_link)
        response = self.safe_request(full_url)
        if not response:
            return []
            
        blocks_data = self.extract_table_data(response.text)
        
        structured_blocks = []
        for data_row in blocks_data:
            block_info = {
                'state': 'MADHYA PRADESH',
                'district': district_name
            }
            
            # Look for block name and link
            for key, value in data_row.items():
                if isinstance(value, dict) and 'link' in value:
                    block_info['name'] = value['text']
                    block_info['link'] = value['link']
                    break
                    
            # Add other data columns
            for key, value in data_row.items():
                if not isinstance(value, dict):
                    clean_key = key.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
                    block_info[clean_key] = value
                    
            if 'name' in block_info and 'link' in block_info:
                structured_blocks.append(block_info)
                
        logger.info(f"Found {len(structured_blocks)} blocks in {district_name}")
        return structured_blocks
        
    def get_panchayats(self, block_link: str, block_name: str, district_name: str) -> List[Dict]:
        """Get list of panchayats from block page"""
        logger.info(f"Fetching panchayats for block: {block_name}, district: {district_name}")
        
        full_url = urljoin(self.base_url, block_link)
        response = self.safe_request(full_url)
        if not response:
            return []
            
        panchayats_data = self.extract_table_data(response.text)
        
        structured_panchayats = []
        for data_row in panchayats_data:
            panchayat_info = {
                'state': 'MADHYA PRADESH',
                'district': district_name,
                'block': block_name
            }
            
            # Look for panchayat name (may not have link)
            name_found = False
            for key, value in data_row.items():
                if isinstance(value, dict) and 'link' in value:
                    panchayat_info['name'] = value['text']
                    panchayat_info['link'] = value['link']
                    name_found = True
                    break
                elif 'panchayat' in key.lower() or 'gram' in key.lower():
                    panchayat_info['name'] = value
                    name_found = True
                    
            # If no specific name found, use first non-empty value
            if not name_found:
                for key, value in data_row.items():
                    if value and value not in ['', '-', 'N/A', '0']:
                        panchayat_info['name'] = value
                        break
                        
            # Add other data columns
            for key, value in data_row.items():
                if not isinstance(value, dict):
                    clean_key = key.lower().replace(' ', '_').replace('.', '').replace('(', '').replace(')', '')
                    panchayat_info[clean_key] = value
                    
            if 'name' in panchayat_info:
                structured_panchayats.append(panchayat_info)
                
        logger.info(f"Found {len(structured_panchayats)} panchayats in {block_name}")
        return structured_panchayats
        
    def scrape_all_levels(self, initial_url: str, max_districts: int = None, 
                         max_blocks_per_district: int = None, delay_between_requests: float = 2.0):
        """Scrape data from all administrative levels with configurable limits"""
        logger.info("Starting comprehensive scraping...")
        
        # Get districts
        districts = self.get_districts(initial_url)
        self.data['districts'] = districts
        
        if max_districts:
            districts = districts[:max_districts]
            logger.info(f"Limited to first {max_districts} districts")
            
        # Process each district
        for i, district in enumerate(districts):
            if 'link' not in district:
                logger.warning(f"No link found for district: {district.get('name', 'Unknown')}")
                continue
                
            logger.info(f"Processing district {i+1}/{len(districts)}: {district['name']}")
            
            blocks = self.get_blocks(district['link'], district['name'])
            self.data['blocks'].extend(blocks)
            
            if max_blocks_per_district:
                blocks = blocks[:max_blocks_per_district]
                logger.info(f"Limited to first {max_blocks_per_district} blocks per district")
                
            # Process each block
            for j, block in enumerate(blocks):
                if 'link' not in block:
                    logger.warning(f"No link found for block: {block.get('name', 'Unknown')}")
                    continue
                    
                logger.info(f"  Processing block {j+1}/{len(blocks)}: {block['name']}")
                
                panchayats = self.get_panchayats(block['link'], block['name'], district['name'])
                self.data['panchayats'].extend(panchayats)
                
                # Delay between requests
                time.sleep(delay_between_requests)
                
            # Longer delay between districts
            time.sleep(delay_between_requests * 2)
            
        logger.info("Scraping completed!")
        logger.info(f"Total collected: {len(self.data['districts'])} districts, "
                   f"{len(self.data['blocks'])} blocks, {len(self.data['panchayats'])} panchayats")
        
    def save_to_csv(self, output_dir: str = "nrega_data"):
        """Save scraped data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save districts
        if self.data['districts']:
            df_districts = pd.DataFrame(self.data['districts'])
            districts_file = os.path.join(output_dir, 'districts.csv')
            df_districts.to_csv(districts_file, index=False, encoding='utf-8')
            logger.info(f"Saved {len(df_districts)} districts to {districts_file}")
            
        # Save blocks
        if self.data['blocks']:
            df_blocks = pd.DataFrame(self.data['blocks'])
            blocks_file = os.path.join(output_dir, 'blocks.csv')
            df_blocks.to_csv(blocks_file, index=False, encoding='utf-8')
            logger.info(f"Saved {len(df_blocks)} blocks to {blocks_file}")
            
        # Save panchayats
        if self.data['panchayats']:
            df_panchayats = pd.DataFrame(self.data['panchayats'])
            panchayats_file = os.path.join(output_dir, 'panchayats.csv')
            df_panchayats.to_csv(panchayats_file, index=False, encoding='utf-8')
            logger.info(f"Saved {len(df_panchayats)} panchayats to {panchayats_file}")
            
    def save_to_excel(self, filename: str = "nrega_data.xlsx"):
        """Save all data to a single Excel file with multiple sheets"""
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                if self.data['districts']:
                    df_districts = pd.DataFrame(self.data['districts'])
                    df_districts.to_excel(writer, sheet_name='Districts', index=False)
                    
                if self.data['blocks']:
                    df_blocks = pd.DataFrame(self.data['blocks'])
                    df_blocks.to_excel(writer, sheet_name='Blocks', index=False)
                    
                if self.data['panchayats']:
                    df_panchayats = pd.DataFrame(self.data['panchayats'])
                    df_panchayats.to_excel(writer, sheet_name='Panchayats', index=False)
                    
            logger.info(f"Saved all data to {filename}")
        except Exception as e:
            logger.error(f"Failed to save Excel file: {e}")
            
    def save_to_json(self, filename: str = "nrega_data.json"):
        """Save scraped data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved all data to {filename}")
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}")


def main():
    parser = argparse.ArgumentParser(description='Enhanced NREGA district/block/panchayat data scraper')
    parser.add_argument('--url', 
                       default='https://nreganarep.nic.in/netnrega/age_reg_emp.aspx?page=s&lflag=eng&state_name=MADHYA+PRADESH&state_code=17&fin_year=2024-2025&source=national&Digest=b5I+IPQDDYk+CpNbEmEo6w', 
                       help='NREGA report URL')
    parser.add_argument('--max-districts', type=int, help='Maximum number of districts to scrape (useful for testing)')
    parser.add_argument('--max-blocks', type=int, help='Maximum number of blocks per district')
    parser.add_argument('--output-dir', default='nrega_data', help='Output directory for CSV files')
    parser.add_argument('--excel-file', default='nrega_data.xlsx', help='Excel output file')
    parser.add_argument('--json-file', default='nrega_data.json', help='JSON output file')
    parser.add_argument('--delay', type=float, default=2.0, help='Delay between requests in seconds')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode (limit to 2 districts, 2 blocks each)')
    
    args = parser.parse_args()
    
    # Add user packages to Python path
    sys.path.append('/home/ubuntu/.local/lib/python3.13/site-packages')
    
    scraper = EnhancedNREGAScraper()
    
    try:
        # Configure limits for test mode
        max_districts = args.max_districts
        max_blocks = args.max_blocks
        
        if args.test_mode:
            max_districts = 2
            max_blocks = 2
            logger.info("Running in test mode: 2 districts, 2 blocks each")
        
        # Scrape all levels
        scraper.scrape_all_levels(
            args.url, 
            max_districts=max_districts,
            max_blocks_per_district=max_blocks,
            delay_between_requests=args.delay
        )
        
        # Save data in multiple formats
        scraper.save_to_csv(args.output_dir)
        scraper.save_to_excel(args.excel_file)
        scraper.save_to_json(args.json_file)
        
        # Print summary
        print(f"\n{'='*50}")
        print("SCRAPING COMPLETED SUCCESSFULLY!")
        print(f"{'='*50}")
        print(f"Districts: {len(scraper.data['districts'])}")
        print(f"Blocks: {len(scraper.data['blocks'])}")
        print(f"Panchayats: {len(scraper.data['panchayats'])}")
        print(f"\nOutput files:")
        print(f"- CSV files: {args.output_dir}/")
        print(f"- Excel file: {args.excel_file}")
        print(f"- JSON file: {args.json_file}")
        
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        print(f"\nPartial data collected:")
        print(f"Districts: {len(scraper.data['districts'])}")
        print(f"Blocks: {len(scraper.data['blocks'])}")
        print(f"Panchayats: {len(scraper.data['panchayats'])}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise


if __name__ == "__main__":
    main()