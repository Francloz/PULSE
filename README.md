# PULSE
PULSE, **P**erforming **U**nification of OMOP and FHIR through **L**LM-based **S**QL **E**xtraction, is an API that received queries from credentialed users in natural language to an OMOP DB and returns the result as a FHIR Bundle.



## How to run
### Test the toy version 
Set the toy script in the dockerfile. 
```dockerfile
ENV FLASK_APP=app.src.toy
```
Then build and run the docker image.
```bash
$ docker build -f App.dockerfile -t my-flask-app .   
$ docker run --name ToyApp -p 5000:5000 my-flask-app
```
The first line might require to be changed to:
```bash
$ docker buildx build -f App.dockerfile -t my-flask-app --load .
```
depending on Docker's configuration.

### Test Keycloak
```bash
$ docker build -f Keycloak.dockerfile -t my-keycloak .
$ docker run --name keycloak -p 8080:8080 my-keycloak
```

Go to http://localhost:8080 and log in using the credentials for the admin found in the dockerfile. 

Import the realm settings in the /keycloak/realm-export.json and  create a dummy user for the realm.

### Check the LLM is running 
Make sure that [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation) is installed
```bash
$ docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
$ docker exec -it ollama ollama pull gemma3:1b
```



## Releases
There are currently no releases available.