#!/usr/bin/env python3
"""
NREGA District/Block/Panchayat Data Scraper
Scrapes age registration employment data from NREGA reports for Madhya Pradesh
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import json
import os
from urllib.parse import urljoin, parse_qs, urlparse
import logging
from typing import Dict, List, Optional
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NREGAScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.base_url = "https://nreganarep.nic.in/netnrega/"
        self.data = {
            'districts': [],
            'blocks': [],
            'panchayats': []
        }
        
    def extract_viewstate_and_eventvalidation(self, html_content: str) -> Dict[str, str]:
        """Extract ViewState and EventValidation for ASP.NET forms"""
        soup = BeautifulSoup(html_content, 'html.parser')
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
        
        result = {}
        if viewstate:
            result['__VIEWSTATE'] = viewstate.get('value', '')
        if eventvalidation:
            result['__EVENTVALIDATION'] = eventvalidation.get('value', '')
            
        return result
        
    def extract_table_data(self, html_content: str, table_selector: str = None) -> List[Dict]:
        """Extract data from HTML tables"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the main data table
        tables = soup.find_all('table')
        data_rows = []
        
        for table in tables:
            # Look for tables with data rows
            rows = table.find_all('tr')
            if len(rows) > 1:  # Has header and data rows
                headers = []
                header_row = rows[0]
                
                # Extract headers
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True))
                
                if not headers:
                    continue
                    
                # Extract data rows
                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) == len(headers):
                        row_data = {}
                        for i, cell in enumerate(cells):
                            # Check for links in cells (district/block/panchayat links)
                            link = cell.find('a')
                            if link and link.get('href'):
                                row_data[headers[i]] = {
                                    'text': cell.get_text(strip=True),
                                    'link': link.get('href')
                                }
                            else:
                                row_data[headers[i]] = cell.get_text(strip=True)
                        data_rows.append(row_data)
                        
        return data_rows
        
    def get_districts(self, state_url: str) -> List[Dict]:
        """Get list of districts from state page"""
        logger.info("Fetching districts...")
        
        try:
            response = self.session.get(state_url)
            response.raise_for_status()
            
            districts = self.extract_table_data(response.text)
            logger.info(f"Found {len(districts)} districts")
            
            # Clean and structure district data
            structured_districts = []
            for district in districts:
                if any('district' in key.lower() for key in district.keys()):
                    district_info = {'state': 'MADHYA PRADESH'}
                    
                    for key, value in district.items():
                        if isinstance(value, dict) and 'link' in value:
                            district_info['name'] = value['text']
                            district_info['link'] = value['link']
                        else:
                            # Map other columns to meaningful names
                            clean_key = key.lower().replace(' ', '_').replace('.', '')
                            district_info[clean_key] = value
                            
                    if 'name' in district_info:
                        structured_districts.append(district_info)
                        
            return structured_districts
            
        except Exception as e:
            logger.error(f"Error fetching districts: {e}")
            return []
            
    def get_blocks(self, district_link: str, district_name: str) -> List[Dict]:
        """Get list of blocks from district page"""
        logger.info(f"Fetching blocks for district: {district_name}")
        
        try:
            full_url = urljoin(self.base_url, district_link)
            response = self.session.get(full_url)
            response.raise_for_status()
            
            blocks = self.extract_table_data(response.text)
            logger.info(f"Found {len(blocks)} blocks in {district_name}")
            
            # Clean and structure block data
            structured_blocks = []
            for block in blocks:
                block_info = {
                    'state': 'MADHYA PRADESH',
                    'district': district_name
                }
                
                for key, value in block.items():
                    if isinstance(value, dict) and 'link' in value:
                        block_info['name'] = value['text']
                        block_info['link'] = value['link']
                    else:
                        clean_key = key.lower().replace(' ', '_').replace('.', '')
                        block_info[clean_key] = value
                        
                if 'name' in block_info:
                    structured_blocks.append(block_info)
                    
            return structured_blocks
            
        except Exception as e:
            logger.error(f"Error fetching blocks for {district_name}: {e}")
            return []
            
    def get_panchayats(self, block_link: str, block_name: str, district_name: str) -> List[Dict]:
        """Get list of panchayats from block page"""
        logger.info(f"Fetching panchayats for block: {block_name}, district: {district_name}")
        
        try:
            full_url = urljoin(self.base_url, block_link)
            response = self.session.get(full_url)
            response.raise_for_status()
            
            panchayats = self.extract_table_data(response.text)
            logger.info(f"Found {len(panchayats)} panchayats in {block_name}")
            
            # Clean and structure panchayat data
            structured_panchayats = []
            for panchayat in panchayats:
                panchayat_info = {
                    'state': 'MADHYA PRADESH',
                    'district': district_name,
                    'block': block_name
                }
                
                for key, value in panchayat.items():
                    if isinstance(value, dict) and 'link' in value:
                        panchayat_info['name'] = value['text']
                        panchayat_info['link'] = value['link']
                    else:
                        clean_key = key.lower().replace(' ', '_').replace('.', '')
                        panchayat_info[clean_key] = value
                        
                if 'name' in panchayat_info:
                    structured_panchayats.append(panchayat_info)
                    
            return structured_panchayats
            
        except Exception as e:
            logger.error(f"Error fetching panchayats for {block_name}: {e}")
            return []
            
    def scrape_all_levels(self, initial_url: str, max_districts: int = None, max_blocks_per_district: int = None):
        """Scrape data from all administrative levels"""
        logger.info("Starting comprehensive scraping...")
        
        # Get districts
        districts = self.get_districts(initial_url)
        self.data['districts'] = districts
        
        if max_districts:
            districts = districts[:max_districts]
            
        # Get blocks for each district
        for i, district in enumerate(districts):
            if 'link' not in district:
                continue
                
            logger.info(f"Processing district {i+1}/{len(districts)}: {district['name']}")
            
            blocks = self.get_blocks(district['link'], district['name'])
            self.data['blocks'].extend(blocks)
            
            if max_blocks_per_district:
                blocks = blocks[:max_blocks_per_district]
                
            # Get panchayats for each block
            for j, block in enumerate(blocks):
                if 'link' not in block:
                    continue
                    
                logger.info(f"  Processing block {j+1}/{len(blocks)}: {block['name']}")
                
                panchayats = self.get_panchayats(block['link'], block['name'], district['name'])
                self.data['panchayats'].extend(panchayats)
                
                # Add delay to avoid overwhelming the server
                time.sleep(1)
                
            time.sleep(2)  # Longer delay between districts
            
    def save_to_csv(self, output_dir: str = "nrega_data"):
        """Save scraped data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save districts
        if self.data['districts']:
            df_districts = pd.DataFrame(self.data['districts'])
            districts_file = os.path.join(output_dir, 'districts.csv')
            df_districts.to_csv(districts_file, index=False)
            logger.info(f"Saved {len(df_districts)} districts to {districts_file}")
            
        # Save blocks
        if self.data['blocks']:
            df_blocks = pd.DataFrame(self.data['blocks'])
            blocks_file = os.path.join(output_dir, 'blocks.csv')
            df_blocks.to_csv(blocks_file, index=False)
            logger.info(f"Saved {len(df_blocks)} blocks to {blocks_file}")
            
        # Save panchayats
        if self.data['panchayats']:
            df_panchayats = pd.DataFrame(self.data['panchayats'])
            panchayats_file = os.path.join(output_dir, 'panchayats.csv')
            df_panchayats.to_csv(panchayats_file, index=False)
            logger.info(f"Saved {len(df_panchayats)} panchayats to {panchayats_file}")
            
    def save_to_excel(self, filename: str = "nrega_data.xlsx"):
        """Save all data to a single Excel file with multiple sheets"""
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
        
    def save_to_json(self, filename: str = "nrega_data.json"):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved all data to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Scrape NREGA district/block/panchayat data')
    parser.add_argument('--url', default='https://nreganarep.nic.in/netnrega/age_reg_emp.aspx?page=s&lflag=eng&state_name=MADHYA+PRADESH&state_code=17&fin_year=2024-2025&source=national&Digest=b5I+IPQDDYk+CpNbEmEo6w', help='NREGA report URL')
    parser.add_argument('--max-districts', type=int, help='Maximum number of districts to scrape')
    parser.add_argument('--max-blocks', type=int, help='Maximum number of blocks per district')
    parser.add_argument('--output-dir', default='nrega_data', help='Output directory for CSV files')
    parser.add_argument('--excel-file', default='nrega_data.xlsx', help='Excel output file')
    parser.add_argument('--json-file', default='nrega_data.json', help='JSON output file')
    
    args = parser.parse_args()
    
    scraper = NREGAScraper()
    
    try:
        # Scrape all levels
        scraper.scrape_all_levels(
            args.url, 
            max_districts=args.max_districts,
            max_blocks_per_district=args.max_blocks
        )
        
        # Save data in multiple formats
        scraper.save_to_csv(args.output_dir)
        scraper.save_to_excel(args.excel_file)
        scraper.save_to_json(args.json_file)
        
        # Print summary
        print(f"\nScraping completed successfully!")
        print(f"Districts: {len(scraper.data['districts'])}")
        print(f"Blocks: {len(scraper.data['blocks'])}")
        print(f"Panchayats: {len(scraper.data['panchayats'])}")
        
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        raise


if __name__ == "__main__":
    main()