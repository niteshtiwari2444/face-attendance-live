# Face Attendance System 🚀

## Local Run
```
venv\Scripts\activate
python app.py
```
Visit: http://localhost:5000

## Vercel Deployment
<create_file>
<path>
c:/Users/91998/OneDrive/Desktop/FaceAttendanceSystem/api/index.py
</path>
<content>
from flask import Flask, request, Response
import sys
import os
sys.path.append('.')

from app import app

# Vercel serverless handler
def handler(req):
    """Vercel Python handler"""
    with app.test_request_context(path=req.path, method=req.method):
        if req.method == 'GET':
            resp = app.test_client().get(req.path)
        elif req.method == 'POST':
            resp = app.test_client().post(req.path, json=req.json)
        elif req.method == 'DELETE':
            resp = app.test_client().delete(req.path)
        else:
            resp = app.test_client().get('/')
        
        exclude_headers
