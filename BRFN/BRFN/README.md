SM
**To run the project for the first time, run:**

> docker compose up --build


If not the first time, or the docker image hasn't changed, run:

> docker compose up -d

- You can dev on the app with the application running. Write code, save changes, and refresh the page to see changes.
- This will also allow you to write commands in the terminal while the project is running


Wait for it to complete, then navigate to http://localhost:8000.

To stop, run:

docker compose down


If making changes to the docker compose file, run

>  docker compose up --build

again to make changes.


**

 - [x] **TC-001**
 - [x] **TC-002**
 - [x] **TC-022**
**