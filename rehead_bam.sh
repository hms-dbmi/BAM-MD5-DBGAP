#!/usr/bin/env bash

samtools view -H /scratch/md5 > /scratch/header.sam
sed -i -e "s/$1/$2/g" /scratch/header.sam
samtools reheader /scratch/header.sam /scratch/md5 > /scratch/md5_reheader