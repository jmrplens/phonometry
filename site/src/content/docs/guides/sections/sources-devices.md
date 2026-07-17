---
title: "Sources and devices"
description: "Characterising what emits the sound: sound power determination by pressure, reverberation-room and intensity methods (ISO 3740 and ISO 9614 series), two-microphone sound intensity (IEC 61043), the IEC 60268 distortion and frequency-response metrics of audio equipment, and the ITU-R BS.1770-5 / EBU R 128 programme loudness and true peak."
---

Every prediction elsewhere in this documentation starts from a source
descriptor, and this section is where those descriptors are measured. Its
common thread is **emission**: numbers that belong to the device rather than
to the room or the distance it is heard at.

The central quantity is the **sound power**: the total acoustic energy per
second a source radiates. Expressed in decibels as the sound power level, it
is the figure that goes on a datasheet, feeds a room or outdoor prediction
and is checked against noise-emission limits.
[Sound Power](/phonometry/guides/sound-power/) covers the five standardised
routes to it, from the enveloping pressure surface of ISO 3744/3746 to the
reverberation room of ISO 3741, the on-site intensity scanning of ISO 9614-2
and the precision grades of ISO 3745 and ISO 9614-3. Behind the intensity-based routes sits **sound intensity** itself:
the signed power flux that can localise sources and separate them from
background noise, measured with a two-microphone probe per IEC 61043 and
qualified by the ISO 9614-1 field indicators, covered in
[Sound Intensity (p-p)](/phonometry/guides/intensity/).

[Electroacoustics](/phonometry/guides/electroacoustics/) turns to devices that
are *supposed* to make sound: amplifiers, loudspeakers and microphones. It
covers the IEC 60268-3 distortion set (THD, THD+N and SINAD, intermodulation
and DIM), the H1/H2 frequency-response estimators with coherence, and the
sensitivity conventions of IEC 60268-4/-5 where datasheet comparisons usually
go wrong.

[Programme loudness](/phonometry/guides/program-loudness/) covers the signal
the devices carry: the ITU-R BS.1770-5 loudness of a broadcast or streaming
programme in LUFS, the EBU R 128 normalisation to -23 LUFS, the EBU Mode
momentary/short-term/integrated meters, the loudness range and the
oversampled true-peak level in dBTP.

If you are here to measure a machine, start with
[Sound Power](/phonometry/guides/sound-power/) and let its decision guidance
pick the route; read [Sound Intensity (p-p)](/phonometry/guides/intensity/)
when that route involves an intensity probe. If you are here to bench-test
audio gear, go straight to
[Electroacoustics](/phonometry/guides/electroacoustics/); if you are here to
level a programme, go to
[Programme loudness](/phonometry/guides/program-loudness/).

## Pages in this section

- [Sound Intensity (p-p)](/phonometry/guides/intensity/): two-microphone
  sound intensity per IEC 61043 with the ISO 9614-1 field indicators.
- [Sound Power](/phonometry/guides/sound-power/): the sound power level by
  enveloping surface, reverberation room, intensity scanning and the
  precision anechoic and intensity methods.
- [Electroacoustics: distortion and frequency response](/phonometry/guides/electroacoustics/):
  the IEC 60268-3 distortion metrics, frequency-response estimation with
  coherence, and microphone and loudspeaker sensitivity conventions.
- [Programme loudness and true peak](/phonometry/guides/program-loudness/):
  the ITU-R BS.1770-5 programme loudness and true-peak level with the
  EBU R 128 normalisation practice, EBU Mode metering and loudness range.
