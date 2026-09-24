# Browser verification

Date: 2026-09-24. Target: `http://127.0.0.1:8765/`, live Python server,
trace-it local OCR and real Jev API. Tested through a separate automated Chromium
browser; the user's existing browser tab was not available for direct inspection.

## Layout corrections

### Native-window follow-up

The earlier checks below resized an emulated viewport. A subsequent user report
exposed a mismatch: the page reported a 1,280 px viewport while the physical browser
window was only about 1,138 px wide. Browser zoom made the discrepancy harder to
identify. Passing viewport-overflow checks did not establish that the entire page
was visible inside the actual window.

The browser's device-size override was cleared and zoom reset to 100%. Verification
then resized the actual browser window, instead of calling `setViewportSize`:

| Actual outer width | Layout viewport | Session table right edge | Review table right edge |
|---:|---:|---:|---:|
| 1,101 px | 1,091 px | 1,035 px | 1,031 px |
| 901 px | 891 px | 835 px | 831 px |
| 701 px | 691 px | 635 px | 631 px |
| 521 px | 511 px | 455 px | 451 px |

Both tables had data, including a freshly processed UK receipt. All right edges
were inside the visible window; no visible text containers overflowed horizontally.
The browser was left maximized at 100% zoom with its device-size override cleared.

Tables now use container queries at 60 rem, so their layout follows the actual space
they have rather than a potentially misleading viewport media query. Workspace
columns also fit their container. A host-window safeguard constrains the page when
an automated/embedded browser reports an oversized viewport, including after reload.
It watches host width only while that mismatch exists. This safeguard can also make
the layout more compact when deliberately zooming out; it does not change browser zoom.

### Earlier viewport checks

- Removed forced line breaks and the narrow fixed-width introduction layout.
- Removed superseded responsive CSS rules; allowed grid children and long text to wrap.
- Kept desktop tables within the page width, with wrapping cells. In the earlier version, below 1,000 px,
  each row becomes labelled values; no columns depend on horizontal scrolling.
- Enlarged supporting text and kept OCR text and expanded line lists at their full height.
- Kept horizontal scrolling only where it is intentional: inspecting a zoomed image.
- Prevented controls from becoming available between items in a running batch.
- Stopped attributing an edited transcription to the earlier OCR timing measurement.
- Made partial Jev failures explicit in the individual and batch completion status.

The previous introduction did not reproduce as clipped in the test browser at
1,280 px, but the old table design did require sideways scrolling on small screens.
The updated introduction and tables were both inspected visually. DOM checks covered
320, 390, 800, 1,024, 1,280 and 1,440 px: page width stayed within the viewport and
visible text containers had no horizontal overflow. Introductory text ranges also
stayed inside the viewport. This does not assert that every browser/zoom combination
has been tested.

## Functional checks

| Flow | Observed outcome |
|---|---|
| Run all eight real examples | Fresh OCR and two fresh Jev calls per image; both prompts match all eight metadata references |
| Run one real example | Fresh comparison, populated text, boxes, result cards and history row |
| Saved demos | All three selectable; recorded comparison explicitly identified |
| Ambiguous pasted text | `MILK $4.50 / BREAD $2.00 / TOTAL $6.50`: both live prompts return UNKNOWN |
| Image upload | Bundled crumpled US photograph extracted 36 OCR regions; both prompts return US |
| Edit extracted text | Replacing it with an explicit Barcelona/Spain receipt yields ES; no stale OCR metrics are attributed to the edited input |
| Native PDF | Four text lines extracted from a locally generated test PDF; no misleading image overlay |
| Invalid image | Clear extraction error; comparison stays disabled for empty text |
| OCR interaction | Text-line selection and image-box selection link to the same region; show/hide, zoom and fit controls work |
| Results | Country, probability, evidence judgment, API confidence, margin, tokens, latency and estimated cost are visible |
| Full probability distribution | Expands to show all nine configured labels |
| Export | Downloaded `receipt-comparison.json` contains the displayed comparison and text |
| Reviewed evaluation | Browser table equals the generated 70-case results, including failures and unsupported guesses |

The batch uses deliberately selected difficult receipts; 8/8 is demonstration
evidence, not independent accuracy. Recorded measurements from final browser runs
are in [web-validation.json](../research/web-validation.json). They are separate
from both evaluation cohorts. No paid output was mocked for these browser checks.
Provider-error behavior is tested separately in unit tests with simulated failures.
The invalid-file browser test intentionally produces an HTTP error response.

## Repeat the checks

Start the live server using [WEB.md](WEB.md), then:

1. Open the page and click **Run all 8**. Wait for completion and check all history rows.
2. Resize the browser to desktop and mobile widths. Verify the entire introductory
   sentence, country names, costs and final table columns remain readable.
3. Select an image region, toggle **Show OCR text regions**, inspect its line, and
   try zoom, fit and **Open full image**.
4. Expand both probability distributions and download the comparison JSON.
5. Visit all three saved demos and compare them. These do not call the API.
6. Use **Your receipt** to paste ambiguous text, upload an image, extract text,
   edit it, and compare. Timing labels must distinguish unedited OCR from typed text.
7. Check the reviewed-evidence table against `evaluation/observable/summary.json`.

Automated checks, without paid requests:

```powershell
python -m unittest discover -s tests -v
python research/evaluate_observable.py
node --check jev_tickets/static/app.js
```

28 tests pass. Node is optional and used only for JavaScript syntax validation;
it is not needed to run the web application. Docker deployment remains unverified
because no Docker engine was running in the development environment.
