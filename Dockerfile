FROM python:3.10.18-slim 
# python 3.10 end of life October 2026, need to refactor code to Django 5

WORKDIR /app

RUN apt-get update

RUN apt-get install -y libpq-dev postgresql-client python3-dev \
    gdal-bin libgdal-dev python3-gdal\
    make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev \
    llvm libncurses5-dev libncursesw5-dev xz-utils \
    tk-dev libffi-dev liblzma-dev \
     --no-install-recommends && \
    apt-get clean -y

# Set GDAL/GEOS library paths
ENV GDAL_LIBRARY_PATH=/lib/x86_64-linux-gnu/libgdal.so.36
ENV GEOS_LIBRARY_PATH=/lib/x86_64-linux-gnu/libgeos_c.so.1
ENV LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH

RUN pip install --upgrade pip

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

ENTRYPOINT ["bash"]