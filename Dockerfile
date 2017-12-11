FROM python:2.7

COPY . /
WORKDIR /

# Setup ENV variables
ENV SAMTOOLS_BIN="samtools-1.6.tar.bz2" \
	SAMTOOLS_VERSION="1.6"

# Install libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	ca-certificates \
	curl \
	libbz2-dev \
	liblzma-dev \
	libncurses5-dev \
	libncursesw5-dev \
	zlib1g-dev \
	&& rm -rf /var/lib/apt/lists/*

# Download and install samtools:
RUN curl -fsSL https://github.com/samtools/samtools/releases/download/$SAMTOOLS_VERSION/$SAMTOOLS_BIN -o /opt/$SAMTOOLS_BIN \
	&& tar xvjf /opt/$SAMTOOLS_BIN -C /opt/ \
	&& cd /opt/samtools-$SAMTOOLS_VERSION \
	&& make \
	&& make install \
	&& rm /opt/$SAMTOOLS_BIN \
	&& cd \
	&& ls -l
	
RUN pip install --upgrade pip \
  && pip install -r requirements.txt
  
ENTRYPOINT ["python"]
CMD ["app.py"]
	
	