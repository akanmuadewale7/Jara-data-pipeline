#!/bin/bash
airflow db init
exec "$@"
