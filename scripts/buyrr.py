def read_new_data(self):
    processed = self._get_processed_files()
    new_files = []
    
    paginator = self.s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=self.bucket_name):
        for obj in page.get('Contents', []):
            print(f"Found file in S3: {obj['Key']}")  # Debugging step
            if obj['Key'].endswith('.csv') and obj['Key'] not in processed:
                new_files.append(obj['Key'])
                processed.add(obj['Key'])
