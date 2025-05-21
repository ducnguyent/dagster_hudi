ARG SPARK_IMAGE
FROM ${SPARK_IMAGE}

USER root
COPY ./jupyter_dev/requirements.txt /tmp/
RUN apt-get update && apt-get install -y python3 python3-pip && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /jupyter_dev
EXPOSE 8888

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", "--NotebookApp.token=''"]
