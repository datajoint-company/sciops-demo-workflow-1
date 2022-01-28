# docker buildx build -t vathes/sciops-demo-workflow-1:v0.0.1 . --load && docker push vathes/sciops-demo-workflow-1:v0.0.1
FROM datajoint/djlabhub:1.4.2-py3.8-debian

# WORKDIR ./workflow
# RUN ls -la /tmp && exit 1

RUN \
    umask u+rwx,g+rwx,o-rwx && \ 
    pip install git+https://github.com/vathes/sciops-demo-workflow-1
