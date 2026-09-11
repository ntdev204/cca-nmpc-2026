# Runtime perception model

The hardware runtime uses the declared `yolo26s-pose` pretrained pose model.
It is a perception interface for person observations; CCA--NMPC remains the
motion controller. The pose contract contains 17 COCO keypoints.

The binary checkpoint/engine is deliberately ignored by Git. On the Jetson,
from the repository root, run:

```bash
python3 -B scripts/python/tools/download_yolo26_pose.py --output models/yolo26s-pose.pt
```

If the Jetson has a working TensorRT/Ultralytics installation, the same command
can export the deployment engine:

```bash
python3 -B scripts/python/tools/download_yolo26_pose.py \
  --output models/yolo26s-pose.pt --export-engine --device 0
```

The ROS launch defaults to the `.pt` path so it can run with PyTorch. Set
`perception_model_path:=/home/rai/cca-nmpc-ros2/models/yolo26s-pose.engine`
after a successful TensorRT export when lower latency is required.
