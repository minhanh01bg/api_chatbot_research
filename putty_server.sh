git pull
docker stop api_eduprompt
docker rm api_eduprompt
docker build -t api_eduprompt .
docker run -d -p 7000:7000 --name api_eduprompt --restart always api_eduprompt
