# Runnable micro-wake-word baseline inputs

Checked: 10 September 2026. This is an implementation handoff for
[the research protocol](KWS_RESEARCH_PROTOCOL_2026-09-10.md), not a trained
custom-word result or an accuracy/resource claim. Public assistant-word models
are diagnostics only. No training archives or TTS weights were downloaded in
this investigation; archive contents and sizes were inspected using bounded
HTTP range requests and ZIP64 central-directory metadata.

## Pinned upstream sources

| Component | Revision and primary source |
|---|---|
| Training framework | [`4665173cd35f1cff9a61e06fc427f124766c488e`](https://github.com/OHF-Voice/micro-wake-word/tree/4665173cd35f1cff9a61e06fc427f124766c488e) |
| Training notebook | [basic_training_notebook.ipynb at that revision](https://github.com/OHF-Voice/micro-wake-word/blob/4665173cd35f1cff9a61e06fc427f124766c488e/notebooks/basic_training_notebook.ipynb) |
| Negative features | [`kahrendt/microwakeword`, `0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1`](https://huggingface.co/datasets/kahrendt/microwakeword/tree/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1) |
| Current Piper generator | [`2971426a55072f7d22fec416ca7800df8bd23207`](https://github.com/rhasspy/piper-sample-generator/tree/2971426a55072f7d22fec416ca7800df8bd23207), package version 3.2.0 |
| Public diagnostic models | [`05b65922cc433c9df13e98e32a7fe520758c837e`](https://github.com/esphome/micro-wake-word-models/tree/05b65922cc433c9df13e98e32a7fe520758c837e) |
| ESPHome implementation inspected | [`7564f5ff1ace9bbe107ec79107bd6606796f3156`](https://github.com/esphome/esphome/tree/7564f5ff1ace9bbe107ec79107bd6606796f3156), development branch; do not confuse this with a selected firmware release |

The notebook still recommends Python 3.10. Current `setup.py` requires
TensorFlow >=2.18 and NumPy >=2.0, rather than pinning an entire known-good
environment. The separate Python 3.12 `.venv-kws` can support the diagnostic
stack, but a working LiteRT interpreter alone does not verify the complete
training dependency stack. Preserve the resolved package list for any training
run. [Dependency declarations](https://github.com/OHF-Voice/micro-wake-word/blob/4665173cd35f1cff9a61e06fc427f124766c488e/setup.py).

## Minimum custom-phrase pilot

The smallest useful adaptation of the notebook needs one locked custom phrase,
positive training audio, independent positive validation/test audio, negative
training features, and separate ambient validation/test features. Recommended
first source bundle:

1. Generate 1,000 synthetic positive **training** utterances for the chosen
   phrase, inspecting pronunciation before bulk generation. Keep all outputs
   from that generator in training for the first honest pilot.
2. Reserve two teammates for validation and two for final testing, with
   different recording sessions; a practical initial budget is 50 utterances
   per reserved speaker. The other two teammates can supply training audio and
   operate equipment. These counts are a proposed collection budget, not an
   upstream sufficiency guarantee or evidence of broad speaker generalization.
3. Use `dinner_party.zip` for negative training and `dinner_party_eval.zip` for
   their existing ambient validation/test partitions. This is a **reduced-data
   pilot**. The stronger full-notebook baseline adds `speech.zip` and
   `no_speech.zip`; every method in a comparison must use the same selection.
4. Generate features for custom training, validation and testing independently.
   Use separate `Clips(..., random_split_seed=None)` objects rooted in the
   already assigned directories and `audio_generator(split=None)`. Never use
   utterance shuffling to create speaker-independent evaluation.
5. Raw MIT RIR, AudioSet and FMA downloads are not required to execute this
   reduced pilot: `Augmentation` explicitly substitutes identity transforms
   when `impulse_paths=[]` and `background_paths=[]`. Gain/color-noise
   augmentations still work. Record this reduction; add training-only local
   noise recordings when available. Keep held-out environment recordings out
   of augmentation and threshold tuning.

The current generator command is:

```sh
python -m piper_sample_generator 'THE LOCKED CUSTOM PHRASE' \
  --model models/en_US-libritts_r-medium.pt \
  --max-samples 1000 --batch-size 16 \
  --output-dir generated_samples
```

This command assumes the pinned generator is installed/importable and the
matching `.pt.json` is alongside the model. Batch 16 is a conservative starting
choice to measure on the available GPU, not a guaranteed optimum. The
[release weight](https://github.com/rhasspy/piper-sample-generator/releases/download/v2.0.0/en_US-libritts_r-medium.pt)
is **204,089,915 bytes**; the matching
[configuration](https://raw.githubusercontent.com/rhasspy/piper-sample-generator/2971426a55072f7d22fec416ca7800df8bd23207/models/en_US-libritts_r-medium.pt.json)
is **25,782 bytes**, specifies 904 voices, and produces 22,050 Hz audio. Resample
to 16 kHz before the microfrontend; the training `Clips` loader does this.
The approximately 930 MB training checkpoint is unnecessary for sample
generation. [Release metadata](https://api.github.com/repos/rhasspy/piper-sample-generator/releases/tags/v2.0.0).

For an English phrase the notebook's LibriTTS-R generator is directly relevant.
Its English voice does not establish faithful pronunciation for an arbitrary
Indian-language phrase. Actual recorded pronunciation must decide whether a
different TTS voice or recorded training set is necessary.

## Exact negative-data budget and layout

Each archive below is resolved under the pinned Hugging Face revision.
Unpacked sizes include all archive entries, including mmap metadata. These are
disk requirements, not a requirement to load the entire dataset into RAM.

| Archive | Download bytes | Unpacked bytes | Existing content |
|---|---:|---:|---|
| [dinner_party.zip](https://huggingface.co/datasets/kahrendt/microwakeword/resolve/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1/dinner_party.zip) | 444,310,142 | 2,336,478,484 | `training/chime6_train_u01_ch1_mmap`, `training/chime6_train_u02_ch1_mmap` |
| [dinner_party_eval.zip](https://huggingface.co/datasets/kahrendt/microwakeword/resolve/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1/dinner_party_eval.zip) | 82,329,019 | 432,150,988 | `validation_ambient/chime6_dev_eval_mmap`, `testing_ambient/dipco_u01_ch1_mmap` |
| [no_speech.zip](https://huggingface.co/datasets/kahrendt/microwakeword/resolve/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1/no_speech.zip) | 2,000,317,854 | 9,554,808,512 | `training/{fma_medium,fsd50k_speech,fsd50k_no_speech,wham_train}_mmap` |
| [speech.zip](https://huggingface.co/datasets/kahrendt/microwakeword/resolve/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1/speech.zip) | 3,183,001,091 | 14,046,639,090 | `training/voices_lav_{mid,clo,far}_training_mmap` |

Reduced dinner+eval bundle: **526,639,161 download bytes** and
**2,768,629,472 unpacked bytes**. Including the TTS weight/config makes its
known external input download **730,754,858 bytes**; retaining both archives,
their extraction, and the TTS weight/config requires **3,499,384,330 bytes**
before generated audio/features, environments, dependencies, caches and model
checkpoints. Actual team recordings can replace TTS and remove that weight
download.

Full four-archive bundle: **5,709,958,106 download bytes** and
**26,370,077,074 unpacked bytes**. Retaining both versions costs
**32,080,035,180 bytes** before those other inputs. With the TTS weight/config,
known external downloads total **5,914,073,803 bytes**. The notebook also
downloads separate raw augmentation corpora; their sizes are not included in
these totals. There is no single exact total environment footprint until the
package versions, augmentation selection and generated clip lengths are fixed.

The archive indices expose 29,154/29,153 five-second training clips for the
two CHiME6 captures; four ambient validation recordings and ten ambient test
recordings. The current speech archive has 116,845 clips per microphone
distance. Repeated microphone captures are correlated observations of the same
source material, not independent speakers or independent recording hours.
Preserve those source groups if taking a subset.

Hugging Face LFS SHA-256 values, suitable for checking complete downloads:

```text
dinner_party.zip       18a0885d595ced7faa73736a8680206f5ba6e80113ca3e6ce43130e510aac18f
dinner_party_eval.zip  e08e23a5e654dd4415a1c41a4b6cd02d1f983c821512367ad937bac1aeed8299
no_speech.zip          722dbcc967275c64c9581ecb85729549830a9094ce605ee22b2ddab9dbabf3c8
speech.zip             68b6b811b347b8321169f9e75ea2b9be73245943b4470af9532ca288d9f1b3cc
```

[File metadata endpoint](https://huggingface.co/api/datasets/kahrendt/microwakeword/tree/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1?recursive=true).
The values above are remote metadata, not a claim that complete local files
were downloaded and hashed.

## Feature and training settings

Directories contain `RaggedMmap` stores ending in `_mmap`, not WAV, Parquet or
ordinary NPY files. Required partition spellings are `training`, `validation`,
`testing`, `validation_ambient`, and `testing_ambient`. Only `Clips` internally
uses the shorter `train`/`test` names. The inspected DiPCo mmap explicitly
stores `uint16`, with each spectrogram shaped `[time, 40]`.

For the current notebook/model family, use mono signed PCM16 at 16 kHz, 30 ms
windows, 10 ms feature steps, 40 channels, 125–7,500 Hz filterbank, PCAN enabled,
and noise-reduction minimum signal 0.05. ESPHome's remaining constants are
smoothing bits 10, even/odd smoothing 0.025/0.06, PCAN strength 0.95, offset 80,
gain bits 21, and enabled log scale with shift 6.
[Runtime frontend constants](https://github.com/esphome/esphome/blob/7564f5ff1ace9bbe107ec79107bd6606796f3156/esphome/components/micro_wake_word/preprocessor_settings.h).

The current notebook pairs the four archives above with a 10 ms frontend. The
dataset card still documents an older 20 ms frontend and `*_background.zip`
archives. It also attributes LibriSpeech to the older speech collection,
whereas the inspected current `speech.zip` directories are VOiCES only. Do not
substitute old archives or treat the card as proof of the current archives'
complete frontend configuration; the archives do not carry a complete
generation manifest. Verify any reused feature source against the intended
frontend. [Dataset card](https://huggingface.co/datasets/kahrendt/microwakeword/blob/0da95f94302ca2f4aae3b18fc6560fa6d2bba3d1/README.md).

TensorFlow's microfrontend path produces raw `uint16` features; convert those
to float with **0.0390625 = 1/25.6**, once. The default C path in current
`generate_features_for_clip` returns float features and constructs
`MicroFrontend()` without applying its `step_ms` argument. Supplying
`step_ms=20` therefore does not switch that path to 20 ms. The loop also uses
`audio_idx + 320 < num_audio_bytes`, excluding a final exact 10 ms block; a
careful streaming driver must consume the complete stream using
`samples_read`. [Feature generation implementation](https://github.com/OHF-Voice/micro-wake-word/blob/4665173cd35f1cff9a61e06fc427f124766c488e/microwakeword/audio/audio_utils.py).

The notebook's model is MixConv with pointwise filters `64,64,64,64`, block
repeats `1,1,1,1`, kernels `[5],[7,11],[9,15],[23]`, no residual connections,
first-convolution filters 32/kernel 5, and stride 3. It sets
`clip_duration_ms=1500`, batch 128, 10,000 training steps, Adam learning rate
0.001, positive/negative class weights 1/20, validation every 500 steps,
and checkpoint selection by `average_viable_recall`.

Source sampling weights are positive 2, speech 10, dinner 10, no-speech 5,
ambient evaluation 0; all source penalty weights are 1. Positive truncation is
`truncate_start`, training-negative truncation `random`, and ambient-evaluation
truncation `split`. Removing sources changes the data budget and normalized
sampling distribution: record the remaining weights and match them between
methods. Generated positive augmentations last 3.2 s, with 0.195–0.205 s
right-side jitter before feature extraction. The 1.5 s model input duration
means a slow/long phrase can lose its beginning after truncation.

## Splits and notebook traps

- The notebook chooses 80/10/10 **utterance** splits. `Clips` seeds the first
  split but calls the second validation/test split without a seed. Input file
  enumeration is also not explicitly sorted. Store explicit manifests rather
  than relying on its seed alone. [Clips implementation](https://github.com/OHF-Voice/micro-wake-word/blob/4665173cd35f1cff9a61e06fc427f124766c488e/microwakeword/audio/clips.py).
- Piper iterates over pairs of voice embeddings and mixes them. Two synthesized
  clips with different names may share one or both source voices. All
  augmentations of a source clip belong to one split; a speaker-disjoint
  synthetic split must keep **both** voices of every pair within its assigned
  partition. The CLI has `--max-speakers` but no arbitrary train/validation/test
  speaker-range control. Using synthetic training and held-out human evaluation
  avoids needing to claim that its default generation is speaker-independent.
  [Generator implementation](https://github.com/rhasspy/piper-sample-generator/blob/2971426a55072f7d22fec416ca7800df8bd23207/piper_sample_generator/__main__.py).
- The nominal notebook 1,000 samples become 16,000 training, 1,000 validation
  and 100 test spectrograms through augmentation repetition/shift. Those are
  not 17,100 independent speakers or utterances.
- Current generator upstream has no top-level `generate_samples.py`; the
  notebook's invocation is stale. Use the module command and explicit `--model`
  above. Install the pinned generator's actual dependencies; its current code
  imports `piper`, rather than relying solely on the notebook's old
  `piper-phonemize-cross` install line.
- Keep the exact `.pt` basename matched to its `.pt.json`. Current generator
  documentation renames the download in an example, while the repository has
  both older and newer configuration names.
- Notebook existence checks can skip a partially downloaded/generated
  directory on rerun. Validate files and hashes, not just directory presence.
- A resumable run restores a checkpoint but the notebook warns that configured
  training steps restart. Record optimizer/checkpoint and total steps; do not
  assume resumed runs have identical schedules.

## First clean streaming diagnostic

Use the pinned
[okay_nabu model manifest](https://github.com/esphome/micro-wake-word-models/blob/05b65922cc433c9df13e98e32a7fe520758c837e/models/v2/okay_nabu.json)
only to validate the audio/frontend/runtime path. Its declared cutoff is 0.97,
feature step 10 ms, probability window 5, and tensor arena 26,080 bytes. The
main session directly inspected the model: input `int8[1,3,40]`, input scale
0.10196078568696976 and zero point -128; output `uint8[1,1]`, scale 1/256.
The arena declaration does not measure full application RAM.

Feed one persistent frontend chronological PCM16 chunks, respecting returned
`samples_read`. Accumulate three new 40-feature rows per inference: 30 ms
between predictions after frontend startup. Do not make sliding overlapping
three-row inputs with a one-row increment; the network already carries its
streaming history internally.

For MCU feature-input parity, ESPHome computes this from raw frontend uint16
features:

```text
q = clip(((raw * 256 + 333) // 666) - 128, -128, 127)
```

Compute in a wide integer type before converting to int8. For pymicro float
features scaled by 1/25.6, reconstruct raw features by rounding
`features * 25.6`, then apply the integer formula and compare against a device
feature dump. The generic Python wrapper's cast-based quantizer does not apply
the same rounding/saturation. [ESPHome feature conversion](https://github.com/esphome/esphome/blob/7564f5ff1ace9bbe107ec79107bd6606796f3156/esphome/components/micro_wake_word/micro_wake_word.cpp).

Log raw uint8 outputs, tensor-dequantized values (`q/256` for this model), and
the runtime threshold convention (`q/255`). ESPHome tests whether the sum of
the last five raw outputs is **strictly greater** than the quantized cutoff
times five; this is a moving average, not five independent successful clips.
Use the exact cutoff integer produced by the selected firmware configuration.
That window spans five predictions / 150 ms of output updates, not five
10 ms feature rows. [Streaming inference and threshold implementation](https://github.com/esphome/esphome/blob/7564f5ff1ace9bbe107ec79107bd6606796f3156/esphome/components/micro_wake_word/streaming_model.cpp).

Start each independent recorded stream with a fresh interpreter and reset/new
frontend, empty feature accumulator and cleared probability window. Preserve
all those states across quiet/noise/quiet transitions within a stream. Current
`Model.predict_clip` does not itself reset internal resource-variable model
state between calls, while its feature helper constructs a fresh frontend;
naively calling it repeatedly creates inconsistent state handling.
[Python inference wrapper](https://github.com/OHF-Voice/micro-wake-word/blob/4665173cd35f1cff9a61e06fc427f124766c488e/microwakeword/inference.py).

The inspected ESPHome implementation also initializes a 100-feature-slice
suppression counter; it advances toward zero only while the most recent
output is below cutoff. `reset_probabilities()` clears the window and resets
that suppression, without recreating the whole model. Match the selected
firmware's startup and cooldown behavior when comparing trigger counts, and
state whether detection stops listening or continues. A timestamp rule must
include the initial 30 ms frontend window and feature consumption times;
prediction index times 30 ms alone hides startup alignment.

A first acceptance check is deterministic replay: the same PCM stream and
fresh states should produce the same features/raw predictions; different
transport chunk sizes should produce the same completed predictions when the
driver handles partial input correctly. Silence and unrelated speech can
check crashes/constant outputs/false triggers, but sensitivity requires a real
positive phrase recording. Subsequent custom-model tests must use the locked
phrase and speaker/session manifests. None of these desktop diagnostics prove
ESP32 CPU, microphone capture, or total RAM compliance.

## License facts to retain with artifacts

The training framework is Apache-2.0. The negative feature dataset explicitly
labels itself **CC BY-NC 4.0**. Its card is incomplete/stale metadata, not an
unrestricted commercial-use grant. The notebook also explicitly treats the
mixed augmentation corpus as appropriate for noncommercial personal use.

The pinned Piper sample-generator package declares MIT, but its current
dependency includes `piper-tts==1.3.0` and its upstream Piper link is
`OHF-Voice/piper1-gpl`; the generator's MIT label does not replace dependency
licenses. [Generator package metadata](https://github.com/rhasspy/piper-sample-generator/blob/2971426a55072f7d22fec416ca7800df8bd23207/pyproject.toml).
The LibriTTS-R voice's
[model card](https://huggingface.co/rhasspy/piper-voices/blob/main/en/en_US/libritts_r/medium/MODEL_CARD)
states CC BY 4.0 for its source dataset, 904 voices, 22,050 Hz, and fine-tuning
from lessac medium. Preserve source attribution and individual model/data
license records. These labels do not justify describing a custom model trained
on the combined bundle as commercially unrestricted.
