/**
 * The English landing page's text (index.mdx), in the shape home.ts gives
 * both locales. The Spanish text is home-es.ts: each landing page is dated by
 * its own language's module alone (site/date-sources.json).
 */
import { designations, domains, passingChecks, sources } from './conformance-stats.mjs';
import { DOI, FICHE_CODE, type HomeContent, SPECTRUM_CODE } from './home.ts';
import { apiPages, catalogueRows, fiches, guides, installCommand, pythonFloor, version } from './repo-stats.mjs';

export const en: HomeContent = {
	statsLabel: 'The library in four numbers',
	stats: [
		{ value: String(passingChecks), label: 'conformance checks passing', href: '/reference/conformance/' },
		{ value: String(designations), label: `normative designations and ${sources} further published sources, across ${domains} test domains`, href: '/reference/conformance/' },
		{ value: String(catalogueRows), label: 'published catalogue rows, each naming the source it came from', href: '/reference/catalogues/' },
		{ value: String(fiches), label: 'PDF fiches in the reporting format their standard defines', href: '/reference/reports/' },
	],
	what: {
		title: 'What this is',
		body: [
			'phonometry (published as PyOctaveBand until 3.0.0) is a Python library for acoustic measurement, analysis and prediction. You give it a signal, a measured spectrum or a set of geometrical and material inputs; it gives you the quantity the standard defines, with the intermediate terms still visible.',
			'Every result is a typed, frozen dataclass. It carries the inputs it was computed from, it draws its own figure with a one-line <code>.plot()</code> in English or Spanish, and where a standard defines a reporting format it renders a one-page PDF fiche with <code>.report()</code>.',
			`It is written and maintained by one person, published under the MIT licence on <a href="https://pypi.org/project/phonometry/">PyPI</a>, archived with a <a href="https://doi.org/${DOI}">DOI on Zenodo</a>, and currently at version ${version}. It needs Python ${pythonFloor} or newer with NumPy and SciPy. Optional extras add the rest: <code>[plot]</code> for the figures, <code>[perf]</code> for the faster impulse ballistics, <code>[report]</code> for the PDF fiches, <code>[audio]</code> for the audio formats beyond uncompressed WAV, <code>[full]</code> for all four, and <code>[torch]</code>, outside <code>[full]</code>, for running the FDTD simulations on PyTorch.`,
		],
	},
	who: {
		title: 'Who it is for',
		items: [
			'Consultants and test laboratories who need the number a standard defines and the terms behind it, in a form that can go into a report.',
			'Researchers who need a readable, citable reference implementation rather than a black box, and who need to see which clause each formula came from.',
			'Audio, firmware and product engineers who need class 1 weighting and filters, distortion, loudness and speech metrics inside their own test rigs.',
			'Students and teachers, since every guide states the standard, the formula and the assumptions before the code.',
		],
	},
	honest: {
		title: 'What it is not',
		items: [
			'Not a certified instrument. The conformance report is the library checking its own output against values published in the standards, not an accredited third-party calibration. Legal measurements still need type-approved hardware.',
			'Not a data-acquisition system. It processes arrays and files you supply; it does not talk to sound cards, microphones or analysers.',
			'Not a complete implementation of every standard it cites. Each guide states which clauses, methods and annexes are covered, and which are not.',
		],
	},
	proof: {
		title: 'What it looks like in use',
		lead: 'Three things the library does that are hard to claim and easy to show: it computes wave fields and renders them, the result of an analysis draws itself, and where a standard prescribes a reporting layout, the same result renders that layout as a PDF.',
		banner: {
			title: 'A wavefront through a hall of columns (2D FDTD)',
			description:
				'An 800 Hz plane wavefront sweeps a 4 m rigid-walled hall filled with a staggered colonnade of rigid columns 10 to 17 cm across, simulated at 2.5 mm; every column diffracts the front and sheds a scattered wavelet, and the wavelets interfere until the whole hall is filled with structured energy that then drains through the absorbing ends.',
			caption:
				'An 800 Hz front through a hall of rigid columns, 2D FDTD at 2.5 mm: every column diffracts the front until the scattered wavelets fill the hall.',
		},
		spectrum: {
			title: 'An analysis, and the figure it draws',
			note: 'One-third-octave band levels per the IEC 61260-1 band edges, and the power spectral density of the same record, which is a result object, so one call draws it. The figure below is committed to the documentation, not a mock-up; it is drawn from a six-tone signal rather than the two-tone one in the snippet, so that the band structure is worth looking at.',
			code: SPECTRUM_CODE,
			alt: 'One-third-octave spectrum of a six-tone signal, with the raw power spectral density in the background',
			caption: 'From the Getting Started guide: 33 bands from 12.6 Hz to 20 kHz, with tones at 20, 100, 500, 2000, 4000 and 15 000 Hz standing out of the spectrum behind them.',
		},
		fiche: {
			title: 'A rating, and the fiche it renders',
			note: 'The weighted airborne rating of ISO 717-1 over the 16 one-third-octave bands the rating uses, rendered in a laboratory report layout: metadata header, band table, the curve against the shifted reference, the boxed single-number result and the verdict against the requirement. The code is the call that renders the fiche beside it, with the metadata block cut to the fields discussed here. Reading the result: Rw is the value of the standard reference curve, at 500 Hz, after it has been shifted as far towards the measured curve as the unfavourable-deviation rule allows (their sum may reach 32.0 dB and here stops at 23.7 dB), so one number stands in for sixteen. The terms in brackets are the spectrum adaptation terms C and Ctr, which are added to Rw rather than replacing it and say how the same element performs against a pink-noise-like source and against urban road traffic: 30 and 28 dB for this pane. The verdict is a pass because the requirement was written against Rw alone; written against Rw + Ctr, as national codes for facades often are, the same pane would fail it.',
			code: FICHE_CODE,
			caption: 'Airborne rating fiche (SoundReductionResult.report), Rw (C; Ctr).',
			linkTitle: 'Airborne ISO 717-1 example report (PDF)',
			description:
				'One-page airborne sound insulation fiche for a 6 mm float glass pane: a metadata header, the one-third-octave R table beside the plot of that curve against the shifted reference, the boxed result Rw (C; Ctr) = 31 (-1; -3) dB and a PASS verdict against the 30 dB requirement.',
		},
	},
	coverage: {
		title: 'What it covers',
		lead: `Thirteen documentation areas over twenty-one import namespaces; in all, ${guides} guides and ${apiPages} API reference pages. Each row links to the area overview; the designations are the standards actually implemented there, not a reading list.`,
		headers: ['Area', 'Standards implemented'],
		noStandard: 'no governing standard',
		areas: [
			{
				name: 'Signal analysis',
				href: '/signals/',
				summary: 'Filter banks, weighting, levels, spectra, calibration and uncertainty.',
				standards: ['IEC 61260-1', 'ANSI S1.11', 'IEC 61672-1', 'ISO 7196', 'IEC 61252', 'ISO 1996-1', 'IEC 60942', 'GUM'],
			},
			{
				name: 'Fluids',
				href: '/fluids/',
				summary: 'The fluid a sound travels through, computed from the measured conditions: humid air, sea water and ideal gases, each with the model behind it.',
				standards: ['IEC 61094-2 Annex F'],
			},
			{
				name: 'Elastic solids',
				href: '/solids/',
				summary: 'The elastic constants of a solid and the three longitudinal wave speeds that follow from them, with the conversions between the forms a table prints.',
				standards: [],
			},
			{
				name: 'Files',
				href: '/io/',
				summary: 'Measurement audio in and out: calibrated reading, provenance, streaming, BWF writing, lossless conversion; catalogues of materials of your own.',
				standards: ['EBU Tech 3285', 'ITU-R BS.2088'],
				keyword: 'measurement audio',
			},
			{
				name: 'Hearing and perception',
				href: '/perception/',
				summary: 'Loudness, sound quality, speech intelligibility, hearing and exposure.',
				standards: ['ISO 532-1/-2/-3', 'ECMA-418-1/-2', 'ISO 226', 'DIN 45692', 'IEC 60268-16', 'ANSI S3.5', 'DIN 45681', 'ISO/PAS 20065', 'ISO 7029', 'ISO 389-7', 'ISO 8253-1/-2', 'ISO 1999', 'ISO 9612', 'ISO 4869-1/-2/-3/-6'],
			},
			{
				name: 'Rooms and buildings',
				href: '/buildings/',
				summary: 'Room parameters, background noise, field and laboratory insulation, prediction.',
				standards: ['ISO 3382-1/-2/-3', 'ISO 16283-1/-2/-3', 'ISO 10140', 'ISO 10848', 'ISO 15186-1/-2', 'ISO 16251-1', 'ISO 717-1/-2', 'EN 12354-1…-6', 'ISO 18233', 'ISO 12999-1', 'ISO 10052', 'ISO 16032', 'ANSI/ASA S12.2', 'ASTM E413'],
			},
			{
				name: 'Materials and surfaces',
				href: '/materials/',
				summary: 'Absorption, airflow resistance, impedance tube, porous and metamaterial models, diffusers, scattering.',
				standards: ['ISO 354', 'ISO 11654', 'ISO 10534-1/-2', 'ISO 9053-1/-2', 'ISO 17497-1/-2', 'ISO 13472-1/-2', 'EN 29052-1', 'ISO 12999-2'],
			},
			{
				name: 'Vibration and structure-borne sound',
				href: '/vibration/',
				summary: 'Mobility and FRFs, isolators, radiated power, junctions, human vibration.',
				standards: ['ISO 7626-1/-2/-5', 'ISO 10846-1/-2/-3/-4/-5', 'ISO 9611', 'ISO/TS 7849-1/-2', 'EN 15657', 'EN 12354-5', 'ISO 2631-1/-2/-4/-5', 'ISO 5349-1/-2', 'ISO 8041-1/-2'],
			},
			{
				name: 'Environment and transport',
				href: '/environment/',
				summary: 'Outdoor propagation, barriers, refraction, environmental indicators, traffic and wind-turbine sources. Of CNOSSOS-EU, the source side of Annex II: the propagation method of its section 2.5 is not implemented, and outdoor attenuation here goes through ISO 9613-2 instead.',
				standards: ['ISO 9613-1/-2', 'ISO 1996-1/-2', 'ISO/PAS 1996-3', 'NT ACOU 112', 'CNOSSOS-EU (2002/49/EC Annex II, 2.2 and 2.3)', 'IEC 61400-11'],
			},
			{
				name: 'Aircraft noise',
				href: '/aircraft/',
				summary: 'Certification levels, airport contours and the rotorcraft hemisphere method.',
				standards: ['ICAO Annex 16', 'IEC 61265', 'SAE ARP 866A/5534', 'ECAC Doc 29', 'ECAC Doc 32'],
			},
			{
				name: 'Underwater acoustics',
				href: '/underwater/',
				summary: 'Levels re 1 µPa, ship radiated noise, pile driving, ambient noise, propagation loss.',
				standards: ['ISO 18405', 'ISO 17208-1/-2', 'ISO 18406', 'JOMOPANS-ECHO'],
			},
			{
				name: 'Sources and devices',
				href: '/devices/',
				summary: 'Sound power, intensity, emission declarations, electroacoustics, programme loudness.',
				standards: ['ISO 3741', 'ISO 3744/3746', 'ISO 3745', 'ISO 9614-1/-2/-3', 'IEC 61043', 'ISO 4871', 'IEC 60268-3/-4/-5', 'ITU-R BS.1770-5', 'EBU R 128'],
			},
			{
				name: 'Wave simulation',
				href: '/simulation/',
				summary: 'Deterministic 2D FDTD solvers, acoustic and elastic P-SV, validated against analytic oracles rather than a standard.',
				standards: [],
			},
		],
	},
	start: {
		title: 'Starting from zero',
		lead: 'Three steps, in order. The first two take a few minutes; the third is the part you keep coming back to.',
		steps: [
			{
				title: 'Install it',
				body: `Python ${pythonFloor} or newer. The base install pulls in NumPy and SciPy; the [full] extra adds four more, [plot] for the figures, [perf] for the faster impulse ballistics, [report] for the PDF fiches and [audio] for the audio formats beyond uncompressed WAV. [torch], which [full] leaves out, runs the FDTD simulations on PyTorch. On 32-bit Windows and 32-bit Linux, which [full] does not support, [plot,report,audio] installs the other three. If phonometry 3.x is already installed, upgrade it with pip install -U phonometry and the extras you use: 3.x has a different import layout, and from phonometry import filters fails on it.`,
				code: installCommand,
				href: '/start/getting-started/',
				linkText: 'Installation options',
			},
			{
				title: 'Run one analysis end to end',
				body: 'Getting Started splits a signal into one-third-octave bands, then anchors those bands to a calibrator tone so the levels are decibels re 20 µPa rather than decibels re nothing, and reduces them to one A-weighted level. Build a sound level meter carries the same chain to the end: the Fast ballistics, LAeq, SEL, LCpeak, the percentile levels and the class check of every stage.',
				href: '/start/getting-started/',
				linkText: 'Getting Started',
				also: { href: '/signals/sound-level-meter/', linkText: 'Build a sound level meter' },
			},
			{
				title: 'Go to the page for your job',
				body: `What do you need to measure? is the same library indexed by the task instead of the subject: a job on the left, the guide that answers it and the standard it implements on the right. All guides is the full inventory, ${guides} of them grouped by topic. Each one opens with the standard it implements, the quantities that standard defines and the assumptions the implementation makes, then the runnable code and the figure it draws, and closes with a Covered / Not covered statement, so you know before you start what the page will and will not answer. When you need an exact signature rather than a method, the API reference has one page per module.`,
				href: '/start/tasks/',
				linkText: 'What do you need to measure?',
				also: { href: '/start/guides/', linkText: 'All guides' },
			},
		],
	},
};
