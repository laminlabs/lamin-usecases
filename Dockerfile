FROM ghcr.io/laminlabs/lamin-bionty-jupyter:0.52.1

# Required to ensure that Binder has all necessary information.
ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

RUN pip install --no-cache-dir notebook jupyterlab

# Additional dependencies that some notebooks need
# celltypist.ipynb
RUN pip install celltypist
# enrichr.ipynb; spatial also requires scanpy
RUN pip install gseapy scanpy
# facs.ipynb
RUN pip install readfcs
# multimodal.ipynb
RUN pip install muon

# Binder does not automatically clone notebooks so we clone them manually
RUN git clone https://github.com/laminlabs/lamin-usecases
