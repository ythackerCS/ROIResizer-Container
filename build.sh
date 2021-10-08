cp Dockerfile.base Dockerfile && \
./command2label.py ./xnat/command.json >> Dockerfile && \
docker build -t xnat/resizeroi:latest .
docker tag xnat/resizeroi:latest registry.nrg.wustl.edu/docker/nrg-repo/yash/resizeroi:latest
rm Dockerfile
