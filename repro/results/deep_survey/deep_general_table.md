## General Deep Segmentation Models (14)

| Rank | Model | Category | mIoU | Dice | Pixel Acc | Params (M) | Train min |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | U-Net (EfficientNet-B0) | encoder-decoder | 0.5983 | 0.7055 | 0.8059 | 5.84 | 0.1 |
| 2 | DeepLabV3+ (EfficientNet-B0) | context-atrous | 0.5903 | 0.7063 | 0.8215 | 4.50 | 0.1 |
| 3 | SegFormer (MiT-B0) | transformer | 0.5890 | 0.7088 | 0.8068 | 3.72 | 0.1 |
| 4 | U-Net++ (ResNet34) | encoder-decoder | 0.5888 | 0.7097 | 0.8061 | 26.08 | 0.2 |
| 5 | U-Net (ResNet34) | encoder-decoder | 0.5606 | 0.6791 | 0.7680 | 24.44 | 0.1 |
| 6 | MAnet (ResNet34) | attention | 0.5518 | 0.6732 | 0.7625 | 31.79 | 0.1 |
| 7 | DeepLabV3+ (ResNet34) | context-atrous | 0.5506 | 0.6734 | 0.7762 | 22.44 | 0.1 |
| 8 | SegFormer (MiT-B2) | transformer | 0.4918 | 0.6094 | 0.7267 | 24.73 | 0.1 |
| 9 | LinkNet (ResNet34) | lightweight | 0.4772 | 0.5905 | 0.7258 | 21.77 | 0.1 |
| 10 | FPN (ResNet34) | pyramid | 0.4643 | 0.5774 | 0.7070 | 23.16 | 0.1 |
| 11 | PSPNet (ResNet34) | pyramid | 0.4345 | 0.5235 | 0.7053 | 21.49 | 0.0 |
| 12 | UPerNet (MiT-B2) | transformer | 0.3918 | 0.4988 | 0.6223 | 32.53 | 0.2 |
| 13 | UPerNet (MiT-B0) | transformer | 0.3560 | 0.4493 | 0.5611 | 10.74 | 0.1 |
| 14 | DeepLabV3 (ResNet34) | context-atrous | 0.3166 | 0.3720 | 0.6509 | 26.01 | 0.1 |