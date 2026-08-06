## Metallography-Oriented Deep Models (15)

| Rank | Model | Category | mIoU | Dice | Pixel Acc | Params (M) | Train min |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | Metal-MAnet RGB+Sobel (EfficientNet-B0) | edge-aware | 0.6108 | 0.7195 | 0.8258 | 8.67 | 0.1 |
| 2 | Metal-U-Net CLAHE (ResNet34) | micrograph-contrast | 0.6073 | 0.7217 | 0.8359 | 24.44 | 0.1 |
| 3 | Metal-SegFormer CLAHE (MiT-B0) | micrograph-contrast | 0.6002 | 0.7146 | 0.8255 | 3.72 | 0.1 |
| 4 | Metal-U-Net Gabor Stack (ResNet34) | texture-aware | 0.5888 | 0.7094 | 0.7899 | 24.44 | 0.2 |
| 5 | Metal-U-Net Gray (ResNet34) | micrograph-contrast | 0.5742 | 0.6962 | 0.7768 | 24.43 | 0.1 |
| 6 | Metal-U-Net++ CLAHE (EfficientNet-B0) | micrograph-contrast | 0.5711 | 0.6874 | 0.7834 | 6.07 | 0.1 |
| 7 | Metal-SegFormer Gray (MiT-B2) | micrograph-contrast | 0.5656 | 0.6893 | 0.7672 | 24.72 | 0.1 |
| 8 | Metal-DeepLabV3+ CLAHE (ResNet34) | micrograph-contrast | 0.5618 | 0.6874 | 0.7852 | 22.44 | 0.1 |
| 9 | Metal-U-Net RGB+Sobel (ResNet34) | edge-aware | 0.5449 | 0.6589 | 0.7820 | 24.44 | 0.1 |
| 10 | Metal-LinkNet RGB+Sobel (ResNet34) | edge-aware | 0.5414 | 0.6683 | 0.7754 | 21.78 | 0.1 |
| 11 | Metal-U-Net LBP Stack (ResNet34) | texture-aware | 0.5373 | 0.6622 | 0.7430 | 24.44 | 0.1 |
| 12 | Metal-U-Net++ Gray (ResNet34) | micrograph-contrast | 0.5318 | 0.6594 | 0.7290 | 26.07 | 0.2 |
| 13 | Metal-FPN Gabor Stack (ResNet34) | texture-aware | 0.4876 | 0.6092 | 0.7235 | 23.16 | 0.1 |
| 14 | MLography U-Net (2022-style) | metallography-original | 0.4150 | 0.5137 | 0.6754 | 23.75 | 0.2 |
| 15 | Metal-UPerNet CLAHE (MiT-B2) | micrograph-contrast | 0.4140 | 0.5314 | 0.6543 | 32.53 | 0.2 |