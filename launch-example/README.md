The purpose of this document is to help people get started with launch by walking through an example that should technically work across any available queue.  The example utilizes Image based jobs (i.e., jobs created by W&B when WANDB_DOCKER env is set) instead of code base jobs (which don’t work at all).  

# Create an Image Based W&B Launch Job

## Prerequisites
* Have Docker installed locally
* Get an account on [Dockerhub](https://hub.docker.com/).  Once you have an account on Dockerhub, Go to account settings then security and create a new API token.  You will be instructed to login to Dockerhub locally. 
* Create a repository on Dockerhub. You will push docker images you build locally to Dockerhub and make it available for Launch. 
Write your python script

Starting locally, create a python script.  The requirements of this script are dead simple.  It should log stuff to wandb.  Nothing fancy is required at this point, in fact, i think the simpler the better.  It is a matter of understanding how this works, and not having some complicated python scripts.  Start with 

```:python
import wandb
import numpy as np
wandb.init(config = dict(a = 0.5, N = 10))
a = wandb.config.a
for i in range(wandb.config.N):
  S_N = (1 - a**i) / (1 - a)
  wandb.log(dict( S_N = S_N) )
  if np.abs(a) < 1:
    err = 1 / (1 - a) - S_N
  else:
    err = np.infty
  wandb.log({"error": err})
wandb.finish()
```

This is just logging the sequence of partial sums for a geometric series with seed `a`.  Name this `geo.py`.  

## Create your Dockerfile
Next up, let’s create a dockerfile.  What is below is what I found to work well.  Start with some simple base image (python:3.8), pip install all of our python requirements, copy our main.py file over to the image via the COPY statement.  Lastly, make sure we the file accessible regardless of who is running the image.

```
FROM python:3.8
RUN pip install wandb numpy
COPY ./geo.py /tmp/geo.py
RUN chmod 777 /tmp/geo.py
ENTRYPOINT [ "python","/tmp/geo.py"]
```

Once the file has been saved, run

```
docker build -t my-dockerhub-username/my-dockerhub-repo
```

The argument `-t` stands for tag and is used to set the image name and optionally a tag.  In the command above the name will be `my-dockerhub-username/my-dockerhub-repo`.  No tag was specified.  You should replace `my-dockerhub-username/my-dockerhub-repo accordingly`.

## Test your Docker Image
Next, run the image to test it out.  
```
docker run -e WANDB_PROJECT=test-project -e WANDB_DOCKER=my-dockerhub-username/my-dockerhub-repo
 -e WANDB_ENTITY=your-entity -e WANDB_API_KEY=your-token my-dockerhub-username/my-dockerhub-repo
:latest
```
The `-e` argument is creating an environment variable at runtime which is passed to the image.  Use this instead of hardcoding the environment variables in the Dockerfile. 

Once you test, this will create an Image Based Job inside of `test-project`.  

## Create a "local" Queue 
## Start an agent

## Push the Docker Image to Dockerhub (optional)
Once you’ve confirmed that this runs as expected, push the image to dockerhub via 
docker push my-dockerhub-username/my-dockerhub-repo
This step is necessary when you will pass your job to a queue which is being polled from anywhere other than your machine that pushed the image.  I haven’t gotten this to work yet, because all of the non local queues are borked. 
