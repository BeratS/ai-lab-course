# RUN Commands

## start the step8 project

```bash

# run the project through these comands
docker build -f step8/Dockerfile.prod -t ai-lab-api .
docker run --rm -p 8001:8000 --env-file .env --network ai-lab_default ai-lab-api

# Check the server is up and running
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"question": "How much is shipping to Kosovo?"}'
# Watch the streaming version arrive step by step
curl -N -X POST http://localhost:8000/ask/stream -H "Content-Type: application/json" -d '{"question": "A mund të paguaj me kartelë?"}'

# Urls & Swagger
http://localhost:8001/health
http://localhost:8001/docs#/

# build image
docker build -f step8/Dockerfile.prod -t ai-lab-api .
```
