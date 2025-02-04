FROM apache/airflow:2.5.1-python3.8

USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev && \
    apt-get clean


# Install dependencies for the pipeline
USER airflow
RUN pip install --no-cache-dir \
    boto3 \
    pandas \
    matplotlib \
    moto \
    pytest 

# Set Airflow home directory
ENV AIRFLOW_HOME=/opt/airflow

# Copy your DAGs and test scripts into the container
COPY dags/ /opt/airflow/dags/
COPY test/ /opt/airflow/test/

# Set the working directory
WORKDIR /opt/airflow

# Entry point to run airflow services
ENTRYPOINT ["bash", "-c", "airflow db upgrade && airflow scheduler & airflow webserver"]

USER airflow
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt


