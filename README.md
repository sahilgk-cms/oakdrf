# oakdrf

OAK chat functionality using Django Rest Framework & PostgreSQL.


## Installation

Go to the cloned repository & create the virtual enviroment in python
```bash
  cd oakdrf
```

```bash
  python venv myvenv
```

Activate the virtual enviroment.

```bash
  myvenv\Scripts\activate
```

Install the requirements
```bash
  pip install -r "requirements.txt"
```
 Since the data will be stored in PostgreSQL, we will have to run migrations to set up the tables in the database.
 ```bash
  python manage.py makemigrations
  python manage.py migrate
```
<img width="1275" height="737" alt="image" src="https://github.com/user-attachments/assets/31036b6d-27ff-4523-9f27-383fb58ccf39" />


Run the server. 
```bash
  python manage.py runserver
```
The server runs on http://localhost:8000

## API Reference
