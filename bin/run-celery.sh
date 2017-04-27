#!/bin/sh

celery -A remo worker -B -l INFO
