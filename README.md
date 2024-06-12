# Data Layer

This is a repo containing the data-layer code, Dockerfile and docker-compose file. This docker-compose will be used to enable local development of the data layer by creating a database
 contianer alongside the flask container, once this is in production Kubernetes will be used instead to create and manage containers and communtication. All needed login info for the db
 connection will be stored in a .env file in the root directory.

## Local Setup

Follow these steps to get started with local development:

- Ensure that docker engine and docker-compose is installed.
- Run docker-compose up --build
