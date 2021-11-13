FROM python:3.9
RUN pip install osm_conflate
WORKDIR /src/
ADD . .
RUN chmod +x loop.sh
RUN pip install jsondiff
RUN pip install feedgen
CMD ["./loop.sh"]
