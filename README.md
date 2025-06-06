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
These are the steps to create a persistent Keycloak docker instance with backups so that it can be redeployed with the same settings.

#### First-Time Setup with Backups

1. **Build the image**

   ```bash
   docker build -f keycloak/Keycloak.dockerfile -t my-keycloak keycloak
   ```

2. **Prepare backup directory & volume**

   ```bash
   mkdir -p backups
   docker volume inspect keycloak_data >/dev/null 2>&1 || docker volume create keycloak_data
   ```

3. **Restore if backup exists**

   ```bash
   if [ -f backups/keycloak_data.tar.gz ]; then
     docker run --rm \
       -v keycloak_data:/data \
       -v "$(pwd)/backups":/backup \
       busybox \
       sh -c "tar xzf /backup/keycloak_data.tar.gz -C /data"
   fi
   ```

4. **Start Keycloak**

   ```bash
   docker run -d \
     --name keycloak \
     -p 8080:8080 \
     -v keycloak_data:/opt/jboss/keycloak/standalone/data \
     my-keycloak
   ```

#### Ongoing Use

1. **Start (with restore)**
   Repeat steps 2 and 3, then step 4.

2. **Update backup**

   ```bash
   docker stop keycloak
   docker run --rm \
     -v keycloak_data:/data \
     -v "$(pwd)/backups":/backup \
     busybox \
     sh -c "tar czf /backup/keycloak_data.tar.gz -C /data ."
   ```

#### Entering and using the Keycloak API

Go to http://localhost:8080 and log in using the credentials for the admin found in the dockerfile. 

### Check the LLM is running 
Make sure that [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html#installation) is installed
```bash
$ docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
$ docker exec -it ollama ollama pull gemma3:1b
```



## Releases
There are currently no releases available.