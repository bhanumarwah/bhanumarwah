# NREGA Data Scraper

A comprehensive Python toolkit for scraping district, block, and panchayat level data from NREGA (National Rural Employment Guarantee Act) reports. This project provides multiple scraping approaches to handle different website configurations and anti-bot measures.

## Features

- **Multi-level data extraction**: Districts → Blocks → Panchayats
- **Multiple scraping engines**: Requests-based and Selenium-based scrapers
- **Robust error handling**: Automatic retries, connection management, and graceful failure handling
- **Multiple output formats**: CSV, Excel, and JSON
- **Configurable limits**: Control scraping scope for testing or partial extraction
- **Rate limiting**: Built-in delays to avoid overwhelming servers
- **Detailed logging**: Track progress and troubleshoot issues

## Installation

1. **Clone or download the project files**
2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **For Selenium scraper (optional)**: Install ChromeDriver
   - Download from: https://chromedriver.chromium.org/
   - Add to PATH or place in project directory

## Project Structure

```
nrega_scraper/
├── nrega_scraper.py              # Basic requests-based scraper
├── nrega_enhanced_scraper.py     # Enhanced requests scraper with better error handling
├── nrega_selenium_scraper.py     # Selenium-based scraper for dynamic content
├── requirements.txt              # Python dependencies
└── README.md                     # This documentation
```

## Usage

### Basic Usage

**Enhanced Requests Scraper (Recommended for most cases):**
```bash
python3 nrega_enhanced_scraper.py --test-mode
```

**Selenium Scraper (For problematic websites):**
```bash
python3 nrega_selenium_scraper.py --test-mode
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--url` | NREGA report URL | Madhya Pradesh 2024-25 age registration report |
| `--max-districts` | Maximum districts to scrape | All available |
| `--max-blocks` | Maximum blocks per district | All available |
| `--output-dir` | Directory for CSV files | `nrega_data` |
| `--excel-file` | Excel output filename | `nrega_data.xlsx` |
| `--json-file` | JSON output filename | `nrega_data.json` |
| `--delay` | Delay between requests (seconds) | 2.0 (3.0 for Selenium) |
| `--test-mode` | Limit to 2 districts, 2 blocks each | False |

### Examples

**Full scraping (all districts and blocks):**
```bash
python3 nrega_enhanced_scraper.py
```

**Limited scraping (first 5 districts, 3 blocks each):**
```bash
python3 nrega_enhanced_scraper.py --max-districts 5 --max-blocks 3
```

**Custom URL and output:**
```bash
python3 nrega_enhanced_scraper.py \
  --url "YOUR_NREGA_REPORT_URL" \
  --output-dir "custom_output" \
  --excel-file "my_data.xlsx"
```

**Selenium scraper with visible browser:**
```bash
python3 nrega_selenium_scraper.py --test-mode --headless false
```

## Output Files

The scraper generates three types of output files:

### 1. CSV Files (in `nrega_data/` directory)
- `districts.csv` - District-level data
- `blocks.csv` - Block-level data  
- `panchayats.csv` - Panchayat-level data

### 2. Excel File (`nrega_data.xlsx`)
- Multiple sheets: Districts, Blocks, Panchayats
- Formatted for easy analysis

### 3. JSON File (`nrega_data.json`)
- Raw structured data
- Preserves links and hierarchical relationships

## Data Structure

Each administrative level includes:

**Districts:**
- `state`: State name (Madhya Pradesh)
- `name`: District name
- `link`: URL for district details
- Additional columns from the report (employment data, etc.)

**Blocks:**
- `state`: State name
- `district`: Parent district name
- `name`: Block name
- `link`: URL for block details
- Additional data columns

**Panchayats:**
- `state`: State name
- `district`: Parent district name
- `block`: Parent block name
- `name`: Panchayat name
- `link`: URL for panchayat details (if available)
- Additional data columns

## Troubleshooting

### Connection Issues
If you encounter connection errors:
1. Check your internet connection
2. Try the Selenium scraper: `python3 nrega_selenium_scraper.py --test-mode`
3. Increase delay between requests: `--delay 5`
4. Use test mode first to verify functionality

### ChromeDriver Issues (Selenium)
If Selenium fails to start:
1. Install ChromeDriver: https://chromedriver.chromium.org/
2. Add ChromeDriver to your PATH
3. Or use the requests-based scraper instead

### Rate Limiting
If the website blocks requests:
1. Increase delay: `--delay 5` or higher
2. Use test mode to reduce load: `--test-mode`
3. Try scraping during off-peak hours

### Empty Results
If no data is extracted:
1. Verify the URL is accessible in your browser
2. Check if the website structure has changed
3. Use `--test-mode` to debug step by step
4. Check logs for specific error messages

## Customization

### Adding New States
To scrape other states:
1. Find the appropriate NREGA report URL for your state
2. Update the default URL or use `--url` parameter
3. Modify the state name in the scraper code if needed

### Custom Data Fields
To extract additional data fields:
1. Examine the HTML structure of the target pages
2. Modify the `extract_table_data()` method
3. Add field mapping in the data processing functions

### Different Report Types
To scrape different NREGA reports:
1. Analyze the new report's structure
2. Adapt the table parsing logic
3. Update the navigation and link extraction methods

## Legal and Ethical Considerations

- **Respect robots.txt**: Check the website's robots.txt file
- **Rate limiting**: Built-in delays prevent server overload
- **Terms of service**: Ensure compliance with website terms
- **Data usage**: Use scraped data responsibly and ethically
- **Attribution**: Consider crediting the data source

## Technical Details

### Retry Strategy
- Automatic retries on connection failures
- Exponential backoff for rate limiting
- Graceful handling of temporary errors

### Session Management
- Persistent sessions for cookie handling
- Custom headers to mimic browser requests
- User-agent rotation for better compatibility

### Data Validation
- Checks for meaningful data in extracted rows
- Validates links and navigation paths
- Handles missing or malformed data gracefully

## Contributing

To contribute to this project:
1. Test the scrapers with different NREGA reports
2. Report bugs or website changes
3. Suggest improvements for data extraction
4. Add support for additional states or report types

## License

This project is provided as-is for educational and research purposes. Users are responsible for ensuring compliance with applicable laws and website terms of service.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the log files for error details
3. Test with `--test-mode` to isolate problems
4. Verify website accessibility and structure changes
