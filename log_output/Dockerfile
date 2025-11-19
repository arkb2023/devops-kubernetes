FROM alpine:latest
RUN apk add --no-cache bash
WORKDIR /usr/src/app
COPY log_output.sh .
#CMD ["bash", "/usr/src/app/log_output.sh"]
ENTRYPOINT ["bash", "/usr/src/app/log_output.sh"]