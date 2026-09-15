# NISHAN physical capture inbox

Print `artifacts/nishan/dual-carrier-user-0000-live-text.pdf` on A4 at **Actual
Size / 100%**. Do not use “fit to page”. The page is synthetic and contains no
private information.

Create these five captures without renaming or editing the source PDF:

1. `scan_150dpi.png` — flatbed/MFP scan, 150 DPI, colour or greyscale.
2. `scan_300dpi.png` — flatbed/MFP scan, 300 DPI, colour or greyscale.
3. `photo_front.jpg` — ordinary phone camera, page fills most of the frame.
4. `photo_angle20.jpg` — phone tilted about 20 degrees, all four page corners visible.
5. `photo_document_app.jpg` — one capture through a document-scanner app with its
   normal auto-crop and enhancement enabled.

For phone captures, place the sheet on a dark, plain surface, keep all four
corners visible, avoid flash glare, and use the phone's normal 1x lens. Keep the
original files; do not send them through WhatsApp or another recompressing app.

Put the files in this directory, then run from the repository root:

```bash
PYTHONPATH=prototypes/nishan_pq .venv/bin/python \
  prototypes/nishan_pq/tools/score_physical_capture.py \
  physical_captures/scan_150dpi.png \
  physical_captures/scan_300dpi.png \
  physical_captures/photo_front.jpg \
  physical_captures/photo_angle20.jpg \
  physical_captures/photo_document_app.jpg
```

The tool writes per-capture scores, all accused rows, marking-condition errors,
registration diagnostics, file hashes, and aligned previews under
`artifacts/nishan/`.
