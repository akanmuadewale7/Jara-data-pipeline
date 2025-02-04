import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from io import BytesIO
import boto3
from botocore.exceptions import ClientError
from scripts.pipeline import read_new_data, transform_data, generate_visualization

@pytest.fixture
def mock_s3():
    with patch('boto3.client') as mock:
        yield mock

def test_read_new_data(mock_s3):
    # Mock the S3 client and responses
    mock_client = MagicMock()
    mock_s3.return_value = mock_client
    
    mock_client.get_paginator.return_value.paginate.return_value = [
        {'Contents': [{'Key': 'file1.csv'}, {'Key': 'file2.csv'}]}
    ]
    
    mock_client.get_object.return_value = {
        'Body': BytesIO(b"opportunity_id,sales_agent,product,account,deal_stage,engage_date,close_date,close_value\n1C1I7A6R,Moses Frase,GTX Plus Basic,Cancity,Won,10/20/2016,3/1/2017,1054.0")
    }
    
    result = read_new_data()
    assert not result.empty
    assert result.shape[0] == 1

def test_transform_data():
    # Test transformation logic
    raw_data = pd.DataFrame({
        'sales_agent': ['Moses Frase', 'Darcel Schlecht'],
        'close_date': ['10/20/2016', '10/25/2016'],
        'deal_stage': ['Won', 'Won'],
        'product': ['GTX Plus', 'GTXPro']
    })
    
    transformed_data = transform_data(raw_data)
    assert transformed_data.shape[0] == 1  # Only Moses Frase should remain

def test_generate_visualization():
    # Test if visualization function handles the data correctly
    processed_data = pd.DataFrame({
        'product': ['GTX Plus', 'GTXPro'],
        'deal_stage': ['Won', 'Won'],
    })
    
    img_buffer = generate_visualization(processed_data)
    assert img_buffer is not None
    assert img_buffer.getvalue() is not None


