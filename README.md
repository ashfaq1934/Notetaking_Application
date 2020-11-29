

# Instructions for setup #

  ## Clone Repository ##
  
 - To set up this project first clone the repo to your local machine. You can do this by clicking the clone button and copying the link to your clipboard.
 
## Run with Docker ##

- Before you can run docker, you'll need to install it, install it using the instructions at <https://docs.docker.com/get-docker/>

- You’ll also need to go to copy the settings variables from the env_example.txt and create a new .env file in the same directory and copy the settings variables.

- Change the DATABASE_HOST variable in the .env file from 'localhost' to 'db' so that the database container is used when running docker.


- Save the file then run these commands in the terminal to run your project

```
$ docker-compose build  
$ docker-compose up -d  
```

- Once your docker build completes your project should start running. Go to
<http://0.0.0.0:5000/>. 


## Run locally ##

- Copy the settings variables from the env_example.txt and create a new .env file in the same directory and copy the settings variables.

- Install MariaDB server and change credentials, you can also modify the .env variables to match your database configuration settings

- Run this command to start the server.

```
$ python note_app.py
```

- The project should start running at <http://0.0.0.0:5000/>.
