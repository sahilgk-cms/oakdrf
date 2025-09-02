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

#### Chatbot

```http
  POST /oak/chat/
```

| Body Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| text | str | name of the document context  |
| query | str | query  |
| session_id | uuid | Optional. id of the session. if not given will create a new session id  |
<img width="1356" height="897" alt="image" src="https://github.com/user-attachments/assets/f27a62ef-5269-4a53-bb5f-acc50954ba47" />

##### oak_chatmessage
<img width="1140" height="197" alt="image" src="https://github.com/user-attachments/assets/8fad5ecf-7e61-441b-abb9-764c4bc07cee" />

##### oak_chatsession
<img width="687" height="95" alt="image" src="https://github.com/user-attachments/assets/ce20a47a-f846-4bc5-9c75-1ca4d313dc95" />

#### Case story
```http
  POST /oak/casestory/
```
| Body Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| main_document | str | name of the document- Outcome Journals or Progress Report partners |
| journal | str | Phase 1 or Phase 2 Journals  |
| partner | str | Name of the relevant partner  |
| social_actor_name | str |  Name of the relevant social actor in the partner   |
| pdf_name | str | name of pdf. Only for Progress Report Partners |

<img width="1379" height="882" alt="image" src="https://github.com/user-attachments/assets/9b69c6c9-4c15-403c-92ef-040876079aca" />

##### oak_casestory
<img width="1434" height="188" alt="image" src="https://github.com/user-attachments/assets/9b391e87-8cdc-455f-a9e2-8e87ec6fb70e" />

