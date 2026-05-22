import pandas as pd
import requests
import json
import io
from datetime import datetime

CSV_URL = "https://www.fuel-finder.service.gov.uk/internal/v1.0.2/csv/get-latest-fuel-prices-csv"

# Spoof a real browser so the server doesn't block us with a 403
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
}

# The exact column names in the Gov CSV
FUEL_COLS = {
    "E10": "fourcourts.fuel_price.E10",
    "E5": "fourcourts.fuel_price.E5",
    "B7S": "fourcourts.fuel_price.B7S",
    "B7P": "fourcourts.fuel_price.B7P"
}

def main():
    try:
        # Fetch the CSV using requests with the browser headers
        response = requests.get(CSV_URL, headers=HEADERS)
        response.raise_for_status() # This will throw an error if it's a 403/404 etc.
        
        # Read the CSV into pandas from the text data
        df = pd.read_csv(io.StringIO(response.text))
        
        prices = {}
        prices["last_updated"] = datetime.now().strftime("%d %b %Y")
        
        for fuel, col_name in FUEL_COLS.items():
            if col_name in df.columns:
                # Convert column to numeric, turning text/blanks into NaN (Not a Number)
                series = pd.to_numeric(df[col_name], errors='coerce')
                
                # Drop the NaN values
                clean_data = series.dropna()
                
                # CLEAN THE DATA: UK fuel is in pence per litre (ppl). 
                # Valid current prices are between 100p and 250p. 
                # This removes missing decimals (e.g. 1499), extra decimals (e.g. 1.49), and swapped columns.
                clean_data = clean_data[(clean_data >= 100) & (clean_data <= 250)]
                
                if not clean_data.empty:
                    # Calculate the mean, convert pence to pounds (£), round to 3 decimals
                    avg_ppl = clean_data.mean()
                    prices[fuel] = round(avg_ppl / 100, 3)
                else:
                    prices[fuel] = None
            else:
                prices[fuel] = None
                
        # Write to JSON
        with open('prices.json', 'w') as f:
            json.dump(prices, f, indent=2)
            
        print(f"Successfully updated prices.json: {prices}")
        
    except Exception as e:
        print(f"Error fetching/parsing CSV: {e}")
        exit(1)

if __name__ == "__main__":
    main()
