import boto3
import json
import time
import yfinance as yf

# AWS Kinesis Configuration
kinesis_client = boto3.client('kinesis', region_name='us-east-1')
STREAM_NAME = "stock-market-stream"  # Replace with your actual stream name
STOCK_SYMBOL = "AAPL"
DELAY_TIME = 30  # Time delay in seconds

# Function to fetch stock data
def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="2d")  # Fetch last 2 days to get previous close

        if len(data) < 2:
            raise ValueError("Insufficient data to fetch previous close.")

        stock_data = {
            "symbol": symbol,
            "open": round(data.iloc[-1]["Open"], 2),
            "high": round(data.iloc[-1]["High"], 2),
            "low": round(data.iloc[-1]["Low"], 2),
            "price": round(data.iloc[-1]["Close"], 2),
            "previous_close": round(data.iloc[-2]["Close"], 2),
            "change": round(data.iloc[-1]["Close"] - data.iloc[-2]["Close"], 2),
            "change_percent": round(((data.iloc[-1]["Close"] - data.iloc[-2]["Close"]) / data.iloc[-2]["Close"]) * 100, 2),
            "volume": int(data.iloc[-1]["Volume"]),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        return stock_data
    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return None

# Function to stream data into Kinesis
def send_to_kinesis():
    while True:
        try:
            stock_data = get_stock_data(STOCK_SYMBOL)
            if stock_data is None:
                print("Skipping this iteration due to API error.")
                time.sleep(DELAY_TIME)
                continue

            print(f"Sending: {stock_data}")

            # Send to Kinesis
            response = kinesis_client.put_record(
                StreamName=STREAM_NAME,
                Data=json.dumps(stock_data),
                PartitionKey=STOCK_SYMBOL
            )

            # Debugging Response
            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                print(f"Kinesis Response: {response}")
            else:
                print(f"Error sending to Kinesis: {response}")

            time.sleep(DELAY_TIME)  # Send data every 30 seconds

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(DELAY_TIME)

# Run the streaming function
send_to_kinesis()
