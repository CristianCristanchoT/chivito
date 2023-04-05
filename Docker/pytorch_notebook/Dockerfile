FROM pytorch/pytorch:2.0.0-cuda11.7-cudnn8-devel

RUN apt-get update --fix-missing
RUN apt-get install ffmpeg xvfb libsm6 libxext6 git -y

COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

ENV TRANSFORMERS_CACHE=/workdir/models/cache/

RUN jt -t monokai -f fira -fs 10 -nf ptsans -nfs 11 -N -kl -cursw 2 -cursc r -cellw 95% -T

EXPOSE 8888

CMD ["bash", "-c", "source /etc/bash.bashrc && jupyter notebook --notebook-dir=/workdir --ip 0.0.0.0 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"]