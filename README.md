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
$ docker build -t my-flask-app .   
$ docker run -p 5000:5000 my-flask-app
```

## Releases
There are currently no releases available.