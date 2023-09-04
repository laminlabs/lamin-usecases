FROM ghcr.io/laminlabs/lamin-bionty-jupyter:0.51.0

RUN pip install --no-cache-dir notebook jupyterlab

ARG NB_USER=jovyan
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /home/${NB_USER}

RUN git clone https://github.com/laminlabs/lamin-usecases
