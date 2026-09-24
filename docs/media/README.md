# Browser demo recording

`receipt-atlas-demo.mp4` is a short screen recording of the actual local web
application. `receipt-atlas-demo.jpg` is a still taken from that recording.

Duration: **45.84 seconds**. Size: **3.13 MB** (3,134,310 bytes). Resolution:
**1280 × 1040**, including the caption footer, at **25 fps**. Playback is at
the original speed. Click the preview in the root README, then use GitHub's
video player or download the MP4 if your viewer does not offer inline playback.

The recording follows the difficult real receipt `op-65346` through a new local
trace-it OCR computation and two live `jev-1.13.0` requests. The OCR model session
was warmed before recording; the recorded image computation and Jev responses
were fresh. Responses and measured timings were not replaced with mock data.

English captions were added below the browser image; there is no audio. The video
shows a curated demonstration, not an independent accuracy test. Candidate
probabilities and OCR scores are not measured accuracy. The final scene presents
the separate reviewed-evidence evaluation and its limitations.

## Files

- [MP4 video](receipt-atlas-demo.mp4): H.264, suitable for browser playback.
- [Preview image](receipt-atlas-demo.jpg): linked from the repository README.
- [Recording metadata](recording.json): duration, capture cues and the actual run's metrics.
- [English captions](receipt-atlas-demo.srt): a separate accessible caption transcript.

The browser footage was recorded with Playwright video capture in a separate
browser context and encoded with FFmpeg. Only the final small MP4, preview,
captions and recording metadata are committed; raw footage is under ignored `.cache`.
No API credential is visible in the recording or its metadata.

## Image attribution and licence

The receipt photograph is an unmodified Open Prices / Open Food Facts contribution:

- Source proof: <https://prices.openfoodfacts.org/proofs/65346>
- Original image: <https://prices.openfoodfacts.org/img/0172/kJjhqpqf46.webp>
- Image licence: [Creative Commons Attribution-ShareAlike 4.0](https://creativecommons.org/licenses/by-sa/4.0/).

The recording shows the photo within the application, with OCR boxes and explanatory
captions added. The video and preview are distributed under the same CC BY-SA 4.0
licence. This media licence does not change the licensing of the surrounding source
code or upstream models. The live demonstration results are separate from the
published evaluation records.

## Recorded run

The recorded run on 2026-09-24 extracted 36 OCR regions and took **5.67 seconds**:
**4.95 seconds** for OCR and **0.71 seconds** for the two parallel Jev calls.
Both prompts returned **US** with **99% candidate probability**, which is not a
validated accuracy or an automatic acceptance decision. The requests used
**2,217 input tokens** and **180 output tokens** combined. The displayed API cost
estimate is **USD 0.000093114**, using the experiment's configured input-token
rate; it excludes local OCR compute and is not an invoice. Timings will vary
on other machines and subsequent requests.

The full metrics and run identifier are in [recording.json](recording.json).

For running the browser yourself, see [DEPLOYMENT.md](../DEPLOYMENT.md).
