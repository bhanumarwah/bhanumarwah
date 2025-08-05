#!/usr/bin/env python3
"""
Demo script for NREGA Data Scraper
Shows different usage patterns and examples
"""

import os
import sys
import time
import json
import pandas as pd
from pathlib import Path

# Add the local packages to path
sys.path.append('/home/ubuntu/.local/lib/python3.13/site-packages')

def demo_basic_usage():
    """Demonstrate basic scraper usage"""
    print("=" * 60)
    print("DEMO 1: Basic Usage with Enhanced Scraper")
    print("=" * 60)
    
    # Import the enhanced scraper
    from nrega_enhanced_scraper import EnhancedNREGAScraper
    
    # Create scraper instance
    scraper = EnhancedNREGAScraper()
    
    # Define the NREGA URL for Madhya Pradesh
    url = "https://nreganarep.nic.in/netnrega/age_reg_emp.aspx?page=s&lflag=eng&state_name=MADHYA+PRADESH&state_code=17&fin_year=2024-2025&source=national&Digest=b5I+IPQDDYk+CpNbEmEo6w"
    
    try:
        print("Testing basic data extraction...")
        
        # Try to get districts (limited for demo)
        districts = scraper.get_districts(url)
        
        if districts:
            print(f"✓ Successfully extracted {len(districts)} districts")
            print("Sample district data:")
            for i, district in enumerate(districts[:3]):
                print(f"  {i+1}. {district.get('name', 'Unknown')} - {len([k for k, v in district.items() if v])} fields")
        else:
            print("⚠ No districts extracted - website may be blocking requests")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        
    print("\nDemo 1 completed.\n")

def demo_limited_scraping():
    """Demonstrate limited scraping for testing"""
    print("=" * 60)
    print("DEMO 2: Limited Scraping (Test Mode)")
    print("=" * 60)
    
    from nrega_enhanced_scraper import EnhancedNREGAScraper
    
    scraper = EnhancedNREGAScraper()
    url = "https://nreganarep.nic.in/netnrega/age_reg_emp.aspx?page=s&lflag=eng&state_name=MADHYA+PRADESH&state_code=17&fin_year=2024-2025&source=national&Digest=b5I+IPQDDYk+CpNbEmEo6w"
    
    try:
        print("Testing limited scraping (1 district, 2 blocks max)...")
        
        # Scrape with limits
        scraper.scrape_all_levels(
            url, 
            max_districts=1, 
            max_blocks_per_district=2,
            delay_between_requests=1.0
        )
        
        # Display results
        print(f"Results:")
        print(f"  Districts: {len(scraper.data['districts'])}")
        print(f"  Blocks: {len(scraper.data['blocks'])}")
        print(f"  Panchayats: {len(scraper.data['panchayats'])}")
        
        if scraper.data['districts']:
            # Save sample data
            output_dir = "demo_output"
            scraper.save_to_csv(output_dir)
            scraper.save_to_json("demo_data.json")
            print(f"✓ Sample data saved to {output_dir}/ and demo_data.json")
            
        else:
            print("⚠ No data extracted - connection issues with NREGA website")
            
    except Exception as e:
        print(f"✗ Error during scraping: {e}")
        
    print("\nDemo 2 completed.\n")

def demo_data_analysis():
    """Demonstrate data analysis capabilities"""
    print("=" * 60)
    print("DEMO 3: Data Analysis Example")
    print("=" * 60)
    
    # Create sample data for demonstration
    sample_data = {
        'districts': [
            {'state': 'MADHYA PRADESH', 'name': 'Bhopal', 'total_registered': '15000', 'active_workers': '12000'},
            {'state': 'MADHYA PRADESH', 'name': 'Indore', 'total_registered': '18000', 'active_workers': '14500'},
            {'state': 'MADHYA PRADESH', 'name': 'Gwalior', 'total_registered': '12000', 'active_workers': '9800'}
        ],
        'blocks': [
            {'state': 'MADHYA PRADESH', 'district': 'Bhopal', 'name': 'Bhopal Block 1', 'registered': '5000'},
            {'state': 'MADHYA PRADESH', 'district': 'Bhopal', 'name': 'Bhopal Block 2', 'registered': '4500'},
            {'state': 'MADHYA PRADESH', 'district': 'Indore', 'name': 'Indore Block 1', 'registered': '6000'}
        ]
    }
    
    try:
        # Convert to DataFrames
        df_districts = pd.DataFrame(sample_data['districts'])
        df_blocks = pd.DataFrame(sample_data['blocks'])
        
        print("Sample data analysis:")
        print(f"📊 Number of districts: {len(df_districts)}")
        print(f"📊 Number of blocks: {len(df_blocks)}")
        
        # Basic analysis
        if 'total_registered' in df_districts.columns:
            df_districts['total_registered'] = pd.to_numeric(df_districts['total_registered'], errors='coerce')
            total_registered = df_districts['total_registered'].sum()
            print(f"📊 Total registered workers: {total_registered:,}")
            print(f"📊 Average per district: {total_registered/len(df_districts):,.0f}")
        
        # District summary
        print("\nDistrict summary:")
        for _, row in df_districts.iterrows():
            print(f"  • {row['name']}: {row.get('total_registered', 'N/A')} registered")
        
        # Block distribution
        block_counts = df_blocks.groupby('district').size()
        print(f"\nBlocks per district:")
        for district, count in block_counts.items():
            print(f"  • {district}: {count} blocks")
            
        print("✓ Analysis completed successfully")
        
    except Exception as e:
        print(f"✗ Error during analysis: {e}")
        
    print("\nDemo 3 completed.\n")

def demo_file_operations():
    """Demonstrate file operations and data formats"""
    print("=" * 60)
    print("DEMO 4: File Operations and Formats")
    print("=" * 60)
    
    # Sample data
    sample_data = {
        'districts': [
            {'state': 'MADHYA PRADESH', 'name': 'Sample District', 'code': 'D001', 'registered': 1000}
        ],
        'blocks': [
            {'state': 'MADHYA PRADESH', 'district': 'Sample District', 'name': 'Sample Block', 'code': 'B001'}
        ]
    }
    
    try:
        # Create demo output directory
        demo_dir = Path("demo_files")
        demo_dir.mkdir(exist_ok=True)
        
        # 1. JSON format
        json_file = demo_dir / "sample_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=2, ensure_ascii=False)
        print(f"✓ Created JSON file: {json_file}")
        
        # 2. CSV format
        if sample_data['districts']:
            df = pd.DataFrame(sample_data['districts'])
            csv_file = demo_dir / "districts.csv"
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"✓ Created CSV file: {csv_file}")
        
        # 3. Excel format
        excel_file = demo_dir / "sample_data.xlsx"
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            if sample_data['districts']:
                pd.DataFrame(sample_data['districts']).to_excel(writer, sheet_name='Districts', index=False)
            if sample_data['blocks']:
                pd.DataFrame(sample_data['blocks']).to_excel(writer, sheet_name='Blocks', index=False)
        print(f"✓ Created Excel file: {excel_file}")
        
        # Show file sizes
        for file_path in demo_dir.glob("*"):
            size = file_path.stat().st_size
            print(f"  📄 {file_path.name}: {size} bytes")
            
        print("✓ All file operations completed successfully")
        
    except Exception as e:
        print(f"✗ Error during file operations: {e}")
        
    print("\nDemo 4 completed.\n")

def show_usage_examples():
    """Show command-line usage examples"""
    print("=" * 60)
    print("COMMAND-LINE USAGE EXAMPLES")
    print("=" * 60)
    
    examples = [
        {
            "description": "Basic test run (recommended first step)",
            "command": "python3 nrega_enhanced_scraper.py --test-mode"
        },
        {
            "description": "Scrape first 3 districts, 2 blocks each",
            "command": "python3 nrega_enhanced_scraper.py --max-districts 3 --max-blocks 2"
        },
        {
            "description": "Custom output directory and files",
            "command": "python3 nrega_enhanced_scraper.py --output-dir my_data --excel-file my_report.xlsx"
        },
        {
            "description": "Slow scraping with 5-second delays",
            "command": "python3 nrega_enhanced_scraper.py --delay 5 --test-mode"
        },
        {
            "description": "Selenium scraper for problematic sites",
            "command": "python3 nrega_selenium_scraper.py --test-mode"
        },
        {
            "description": "Full scraping (all districts and blocks)",
            "command": "python3 nrega_enhanced_scraper.py"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['description']}:")
        print(f"   {example['command']}")
        print()

def main():
    """Run all demos"""
    print("🚀 NREGA Data Scraper - Demonstration Suite")
    print("=" * 60)
    print("This demo shows various features and usage patterns.")
    print("Note: Actual scraping may fail due to website connectivity issues.")
    print("=" * 60)
    print()
    
    # Show command-line examples first
    show_usage_examples()
    
    # Run demos
    try:
        demo_basic_usage()
        time.sleep(1)
        
        demo_limited_scraping()
        time.sleep(1)
        
        demo_data_analysis()
        time.sleep(1)
        
        demo_file_operations()
        
    except KeyboardInterrupt:
        print("\n⏸ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
    
    print("=" * 60)
    print("✅ Demo suite completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Try: python3 nrega_enhanced_scraper.py --test-mode")
    print("2. Check output files in nrega_data/ directory")
    print("3. Adjust parameters based on your needs")
    print("4. For issues, check README.md troubleshooting section")

if __name__ == "__main__":
    main()