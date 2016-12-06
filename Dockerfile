FROM ubuntu

RUN apt-get update && apt-get install -y gcc make bzip2 zlib1g-dev ncurses-dev
RUN apt-get update && apt-get install -y python3
RUN apt-get update && apt-get install -y python3-pip
RUN apt-get update && apt-get install -y wget

RUN python3 -m pip install boto3
RUN python3 -m pip install requests
RUN python3 -m pip install hvac
ADD samtools-1.3.1.tar.bz2 samtools.tar.bz2
RUN cd samtools.tar.bz2 && cd samtools-1.3.1 && make
ENV PATH /samtools.tar.bz2/samtools-1.3.1/:$PATH
ENV AWS_CONFIG_FILE /.aws/config

RUN mkdir /.aws/
COPY config /.aws/config

RUN mkdir /output/
COPY generate_md5.py /output/generate_md5.py

COPY s3_fileservice /output/s3_fileservice
COPY sample_fileservice /output/sample_fileservice
COPY rehead_bam.sh /output/rehead_bam.sh
RUN chmod 700 /output/rehead_bam.sh

CMD ["python3","/output/generate_md5.py"]