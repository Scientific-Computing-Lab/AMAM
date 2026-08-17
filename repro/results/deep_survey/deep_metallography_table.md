## Metallography-Oriented Deep Models (15)

| Rank | Model | Category | mIoU | Dice | Pixel Acc | Params (M) | Train min |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Metal-U-Net++ CLAHE (EfficientNet-B0) | micrograph-contrast | 0.5834 | 0.6995 | 0.8157 | 6.07 | 0.1 |
| 2 | Metal-MAnet RGB+Sobel (EfficientNet-B0) | edge-aware | 0.5741 | 0.6881 | 0.8045 | 8.67 | 0.1 |
| 3 | Metal-U-Net Gabor Stack (ResNet34) | texture-aware | 0.5613 | 0.6727 | 0.7865 | 24.44 | 0.2 |
| 4 | Metal-U-Net RGB+Sobel (ResNet34) | edge-aware | 0.5605 | 0.6750 | 0.8020 | 24.44 | 0.1 |
| 5 | Metal-U-Net CLAHE (ResNet34) | micrograph-contrast | 0.5470 | 0.6627 | 0.7925 | 24.44 | 0.1 |
| 6 | Metal-SegFormer CLAHE (MiT-B0) | micrograph-contrast | 0.5348 | 0.6604 | 0.7606 | 3.72 | 0.1 |
| 7 | Metal-LinkNet RGB+Sobel (ResNet34) | edge-aware | 0.5073 | 0.6197 | 0.7541 | 21.78 | 0.1 |
| 8 | Metal-U-Net LBP Stack (ResNet34) | texture-aware | 0.4795 | 0.5933 | 0.7236 | 24.44 | 0.1 |
| 9 | Metal-DeepLabV3+ CLAHE (ResNet34) | micrograph-contrast | 0.4730 | 0.5887 | 0.7050 | 22.44 | 0.1 |
| 10 | Metal-SegFormer Gray (MiT-B2) | micrograph-contrast | 0.4565 | 0.5685 | 0.7110 | 24.72 | 0.1 |
| 11 | Metal-U-Net Gray (ResNet34) | micrograph-contrast | 0.4538 | 0.5768 | 0.6221 | 24.43 | 0.1 |
| 12 | Metal-U-Net++ Gray (ResNet34) | micrograph-contrast | 0.4350 | 0.5405 | 0.6873 | 26.07 | 0.2 |
| 13 | MLography U-Net (2022-style) | metallography-original | 0.4317 | 0.5480 | 0.6785 | 23.75 | 0.2 |
| 14 | Metal-FPN Gabor Stack (ResNet34) | texture-aware | 0.4197 | 0.5444 | 0.6630 | 23.16 | 0.1 |
| 15 | Metal-UPerNet CLAHE (MiT-B2) | micrograph-contrast | 0.3558 | 0.4631 | 0.5955 | 32.53 | 0.2 |