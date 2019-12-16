FROM ros:melodic

# install build tools
RUN apt-get update && apt-get install -y \
      python-catkin-tools \
    && apt-get install -y python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

# clone ros package repo
ENV ROS_WS /opt/ros_ws
RUN mkdir -p $ROS_WS/src
WORKDIR $ROS_WS

ADD rospy_tutorials $ROS_WS/src/rospy_tutorials


RUN apt-get update && \
    rosdep update && \
    rosdep install -y \
      --from-paths \
        src/rospy_tutorials \
      --ignore-src && \
    rm -rf /var/lib/apt/lists/*

RUN cd $ROS_WS/src/rospy_tutorials && chmod +x talker.py && python -m pip install -r requirements.txt

RUN catkin config \
      --extend /opt/ros/$ROS_DISTRO && \
    catkin build \
      rospy_tutorials

# source ros package from entrypoint
RUN sed --in-place --expression \
      '$isource "$ROS_WS/devel/setup.bash"' \
      /ros_entrypoint.sh

CMD ["roslaunch", "rospy_tutorials", "talker_listener.launch", "path:=hi"]
