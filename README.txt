JMD store - Minimal catalog (Flask)
==================================

Files included:
- app.py               # Flask app (reads data/catalog.xlsx)
- data/catalog.xlsx    # your uploaded Excel (copied)
- templates/index.html
- static/style.css
- static/logo.svg
- static/images/placeholder.svg
- requirements.txt

How to run locally:
1. python -m venv venv
2. venv\Scripts\activate (Windows) or source venv/bin/activate (mac/linux)
3. pip install -r requirements.txt
4. python app.py
5. Open http://127.0.0.1:5000 in your browser

Render deploy (quick):
1. Create a git repo with these files and push to GitHub.
2. Create a Web Service on Render (Free), connect the GitHub repo.
3. Build command: pip install -r requirements.txt
4. Start command: python app.py
5. Set the root to / (Render will detect Flask app)

Notes:
- Replace placeholder images by uploading files to static/images/
- Excel file is located at data/catalog.xlsx
