#!/bin/bash
sudo docker build -t num_next . &&
sudo docker run -d -p 3003:3003 num_next
