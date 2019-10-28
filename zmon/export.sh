#!/bin/bash

echo -e "\e[1m\e[39mPlease provide the Team Name once more to collect ZMON Alerts with Time Period \e[21m"
read -p "Team Name:" directory
mkdir /tmp/$directory
echo -e "\e[1m\e[39mCollecting ZMON Alerts.... \e[21m"
for i in $(zmon alert-definitions list | grep -i $directory | cut -d" " -f1,2 | sed -e 's/^[ \t]*//' | cut -d" " -f 1); 
   do zmon alert-definitions get $i > /tmp/$directory/$i.yaml && echo "Downloading ZMON Alert definition $i";
done
