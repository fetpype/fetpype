#!/bin/bash
#SBATCH -J recon
#SBATCH -p high
#SBATCH --mem 32G
#SBATCH -N 1
#SBATCH -n 4
#SBATCH --gres=gpu:1
#SBATCH -o recon_nesvor.out # STDOUT
#SBATCH -e recon_nesvor.err # STDERR

module --ignore-cache load CUDA/11.7

export PATH="$HOME/project/anaconda3/bin:$PATH"
source activate fetal

## ADD ANTS path
export ANTSPATH=/homedtic/gmarti/LIB/ANTsbin/bin
export ANTSSCRIPTS=/homedtic/gmarti/LIB/ANTs/Scripts
export PATH=${ANTSPATH}:${PATH}

python workflows/pipeline_fet.py -data /homedtic/gmarti/DATA/ERANEU_BIDS_small/ -out /homedtic/gmarti/DATA/ERANEU_BIDS_small/test -params workflows/params_segment_fet_niftimic.json -sub 007 -ses 01