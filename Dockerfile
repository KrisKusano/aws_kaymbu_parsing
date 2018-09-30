# Dockerfile to build distribution package using AWS linux.
# This is required for things that compile against machine specific libraries,
# e.g., lxml
#
# source:
# https://blog.mapbox.com/aws-lambda-python-magic-e0f6a407ffc6
FROM amazonlinux:latest
RUN yum install -y gcc gcc-c++ freetype-devel yum-utils findutils \
openssl-devel groupinstall development tar.x86_64 xz make zip
# Install python3.6
RUN curl https://www.python.org/ftp/python/3.6.1/Python-3.6.1.tar.xz | tar -xJ \
&& cd Python-3.6.1 \
&& ./configure --prefix=/usr/local --enable-shared \
&& make && make install \
&& cd .. && rm -rf Python-3.6.1
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
# Install Python modules to a /tmp/vendored directory that we will zip
# up for deployment to Lambda.
ADD requirements.txt /tmp/vendored/
RUN pip3 install -t /tmp/vendored -r /tmp/vendored/requirements.txt
RUN rm -rf /tmp/vendored/requirements.txt
# Echo the estimated size of the package
RUN du -sh /tmp/vendored
# We can remove all tests/ script and other unused files
RUN find /tmp/vendored -name "*-info" -type d -exec rm -rdf {} +
RUN find /tmp/vendored -name "tests" -type d -exec rm -rdf {} +
# Here we remove package that will be present in AWS Lambda env
RUN rm -rdf /tmp/vendored/boto3/
RUN rm -rdf /tmp/vendored/botocore/
RUN rm -rdf /tmp/vendored/docutils/
RUN rm -rdf /tmp/vendored/dateutil/
RUN rm -rdf /tmp/vendored/jmespath/
RUN rm -rdf /tmp/vendored/s3transfer/
RUN rm -rdf /tmp/vendored/numpy/doc/
RUN du -sh /tmp/vendored
# Keep byte-code compiled files for faster Lambda startup
RUN find /tmp/vendored -type f -name '*.pyc' \
| while read f; do n=$(echo $f | sed 's/__pycache__\///' \
| sed 's/.cpython-36//'); cp $f $n; done;
RUN find /tmp/vendored -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find /tmp/vendored -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN du -sh /tmp/vendored
# Create the zip file
ADD lambda_function.py note_parse.py sdb_modify_domain.py /tmp/vendored/
RUN cd /tmp/vendored && zip -r9q /tmp/deploy.zip *
RUN du -sh /tmp/deploy.zip