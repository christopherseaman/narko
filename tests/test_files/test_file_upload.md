# File Upload Extension Test

This document tests the new file upload extension functionality.

## External URLs

External image from URL:
![image](https://via.placeholder.com/400x300.png)

External video:
![video](https://sample-videos.com/zip/10/mp4/SampleVideo_1280x720_1mb.mp4)

External PDF:
![pdf](https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf)

## Local Files (with auto-detection)

Local image (auto-detected):
![file](./profile.png)

## Explicit File Types with Captions

Image with caption:
![image:Company Logo](./profile.png)

Video file:
![video:Demo Video](./sample.mp4)

PDF document:
![pdf:User Manual](./documentation.pdf)

Audio file:
![audio:Background Music](./music.mp3)

Generic file:
![file:Configuration](./config.json)

Embedded content:
![embed:GitHub Repository](https://github.com/example/repo)

## Edge Cases

File that doesn't exist:
![image](./nonexistent.png)

Empty caption:
![file:](./profile.png)

## Combined with Other Extensions

> [!TIP]
> You can combine file uploads with callouts!
> ![image:Example](./profile.png)

- [x] Upload images ✓
- [x] Upload videos ✓ 
- [ ] Upload audio files

$$
\text{File uploads work with math: } f(x) = \int_{-\infty}^{\infty} e^{-x^2} dx
$$