import pandas as pd
import boto3
from io import BytesIO
import matplotlib.pyplot as plt
import logging
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the S3 bucket
bucket_name = 'jara-data-pipeline'

# Initialize the S3 client
s3 = boto3.client('s3')

def read_new_data():
    new_files = []
    
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get('Contents', []):
            if obj['Key'].endswith('.csv'):
                new_files.append(obj['Key'])
    
    dfs = []
    for file_key in new_files:
        obj = s3.get_object(Bucket=bucket_name, Key=file_key)
        df = pd.read_csv(BytesIO(obj['Body'].read()))
        dfs.append(df)
    
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

raw_data = read_new_data()
print("Raw Data Loaded:")
print(raw_data.head())  # Check the first few rows of the dataframe


def transform_data(raw_df):
    if raw_df.empty:
        return raw_df
    
    raw_df['agent_first_name'] = raw_df['sales_agent'].str.split().str[0]
    filtered = raw_df[~raw_df['agent_first_name'].isin(['Darcel', 'Kami', 'Jonathan'])]
    
    # Specify the date format and handle errors (coerce invalid dates)
    filtered.loc[:, 'close_date'] = pd.to_datetime(filtered['close_date'], format='%m/%d/%Y', errors='coerce')
    
    # Check if 'close_date' was successfully converted to datetime
    if not pd.api.types.is_datetime64_any_dtype(filtered['close_date']):
        logger.warning("The 'close_date' column is not in datetime format.")
        return pd.DataFrame()  # Return an empty DataFrame or handle as needed
    
    closed_2016 = filtered[
        (filtered['close_date'].dt.year == 2016) & 
        (filtered['deal_stage'] == 'Won')
    ]
    
    top_agents = closed_2016['sales_agent'].value_counts().nlargest(5).index
    return closed_2016[closed_2016['sales_agent'].isin(top_agents)]


processed_data = transform_data(raw_data)
print("Processed Data:")
print(processed_data.head())  # Check the first few rows after transformations


def generate_visualization(processed_df):
    if processed_df.empty:
        logger.warning("No data available for visualization.")
        return None  
    
    # Print sample data for verification
    print(processed_df.head())  # Debugging step

    plt.figure(figsize=(12, 6))
    
    # Group data for visualization
    grouped = processed_df.groupby(['product', 'deal_stage']).size().unstack()
    
    # Plotting
    grouped.plot(kind='bar', stacked=False)
    plt.title('2016 Closed Deals by Product and Deal Stage (Top 5 Agents)')
    plt.xlabel('Product')
    plt.ylabel('Number of Deals')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Show the plot
    plt.show()
    
    # Save to buffer
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png')
    img_buffer.seek(0)
    plt.close()
    
    return img_buffer

def main():
    try:
        # Data ingestion
        raw_data = read_new_data()
        if raw_data.empty:
            logger.info("No new data to process")
            return
        
        # Data transformation
        processed_data = transform_data(raw_data)
        if processed_data.empty:
            logger.warning("No valid data after transformations")
            return
        
        # Generate visualization
        img_buffer = generate_visualization(processed_data)
        
        # Upload to S3
        s3.put_object(
            Bucket=bucket_name,
            Key='results/latest_chart.png',
            Body=img_buffer,
            ContentType='image/png'
        )
        logger.info("Successfully updated visualization")
    
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
