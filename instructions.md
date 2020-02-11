# Instructions 
1) Unzip the project file
2) Open terminal
3) Change directory to the project directory (where the un-zipped file is)
4) Make sure you have python3 install or install (https://phoenixnap.com/kb/how-to-install-python-3-windows)
5) Create virtual environment:
% python3 -m venv venv_kadima

6) Install the requirements
 % pip install -r requirements.txt

7) Change directory to kadima_project
8) Create the DB relationships:
% python3 manage.py makemigrations && python3 manage.py migrate

9) Run the server:
% python3 manage.py runserver 127.0.0.1:8001

10) Open your browser and copy/paste link: 127.0.0.1:8001
11) Connect teh TWS

Ready.
