#!/bin/sh

celery -A remo worker -l INFO
