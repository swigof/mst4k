FROM continuumio/miniconda3

WORKDIR /opt/mst4k

COPY environment.yml .
RUN conda env create -f environment.yml && rm environment.yml

COPY mst4k.py .
COPY .env .

CMD conda run -n mst4k python mst4k.py
