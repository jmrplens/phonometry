← [Documentation index](../README.md)

# Contributor style guide

This guide states how phonometry is written: how it names things, shapes its public API, documents and comments its code, handles numbers and data, tests itself, documents and draws, and words its prose. It is for everyone who changes the library, people and AI coding agents alike, so that every contribution keeps one style and a review can point to a rule instead of explaining it again.

## How to use it

Read this index, then the page for the area you are changing. [CONTRIBUTING.md](../../CONTRIBUTING.md) holds the process: the development setup, the gates to run, the generated media, the conformance report, filing an errata entry, releasing and opening a pull request.

Every rule has an identifier, a letter for its page and a number: a review cites it as N7 or F35, and a link reaches it as `naming.md#n7`. The tables below list every rule with its statement and the check that enforces it, in the order the pages give them.

The code already in the tree is no authority where it breaks a rule. Where the code around you does, the rule wins: never copy the majority form, fix the sites your change touches, and name the rest in the pull request. A rule that looks wrong is raised with the maintainer, not worked around.

## The shape of a rule

Each rule on a page has the same parts:

- **The heading**: the identifier and one imperative sentence, the same sentence this index gives.
- **Why**: the failure the rule prevents, the real one when there was one.
- **Do**: one correct example, the smallest that shows the rule. A `python` example runs under `scripts/check_doc_snippets.py`, in page order, so it uses only names that exist.
- **Don't**: one incorrect example, fenced `py` so that it never runs. A rule about text, not code, uses a `text` or `markdown` fence for both.
- **Enforced by**: the check that holds the rule: a script, a test (`path::test_name`), a Makefile target (`make target`), a ruff code (`ruff CODE`), a CI job or step (`CI: its name`), `mypy` or `bandit`, or review when no check does.
- **Exceptions**: only when there are some, with how one is declared.

`tests/test_contributing_guide.py` holds the guide to this shape: it fails when a rule lacks its Why, its Do or its Don't, or an example label has no fence after it, when a page and this index disagree, when an enforcer names a check that does not exist or that the configuration switches off, or when a link into the guide misses its anchor.

## Pages

- [Naming](naming.md) (N): modules, classes, errors and warnings, functions, parameters and record fields, constants, and the words, units and spelling names are made of.
- [API shape](api.md) (A): where a public name lives and how it is imported, what a module publishes, the shape of a signature, what a function returns, how a verdict answers, which error or warning a refusal raises, and how a name is renamed or retired.
- [Docstrings and comments](docstrings.md) (D, C): the module docstring and the document it names, function and class docstrings, the mathematics they carry, comments in the code, and how long a module grows. D rules cover docstrings and modules, C rules cover comments.
- [Numbers and data](numerics.md) (X): comparing computed values, validating what a caller passes, the arrays a result keeps, units, references and precision, the data the package publishes, and the fields an FDTD engine steps.
- [Tests](tests.md) (T): where a test lives, where an expected value comes from, how a test waits on an error or a warning, the data the repository keeps, guards and their exemptions, conformance rows, the workflows under `.github/`, and what the pytest configuration may import.
- [Documentation and figures](docs-and-figures.md) (F): the guides, their Spanish twins and the `docs/` mirror, code fences, figures and the `.plot()` code that draws them, records in a notebook, the catalogues pages, the errata register, the frames of a clip and the device its field steps on, the install commands a page prints, the description of each page and its size.
- [Prose, commits and pull requests](prose.md) (P): the language of each surface, the characters a text may hold, citing a page, the CHANGELOG, commit messages and pull request text.

## Rules

### Naming

| Rule | Statement | Enforced by |
|---|---|---|
| [N1](naming.md#n1) | Name a module for its subject in words, never for a standard's designation | `tests/test_api_docs_generator.py::test_no_page_title_carries_a_number`, review |
| [N2](naming.md#n2) | Make a module private when a function of its package takes its name | `scripts/check_api_reference.py`, `tests/test_removed_names.py::test_a_module_hidden_behind_its_function_is_private`, `CI: Curated API quick table covers __all__` |
| [N3](naming.md#n3) | Give every top-level name a module keeps for itself a leading underscore | `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__` |
| [N4](naming.md#n4) | Name a result class `<Concept>Result` for what its function returns | review |
| [N5](naming.md#n5) | Write an acronym in capitals in a class name | `tests/test_public_vocabulary.py::test_an_acronym_is_written_in_capitals` |
| [N6](naming.md#n6) | Name an exception `<Topic>Error` and a warning `<Topic>Warning` | `tests/test_package_architecture.py::test_every_published_exception_is_named_an_error`, `tests/test_package_architecture.py::test_every_published_warning_is_a_phonometry_warning` |
| [N7](naming.md#n7) | Name a function for the quantity it returns; keep a verb for an action | review |
| [N8](naming.md#n8) | Leave `_db` and `_hz` off a function name; keep a unit where two compete | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_public_function_is_named_for_what_it_returns` |
| [N9](naming.md#n9) | Name a judgment `verify_` for an instrument, `assess_` for a situation, `check_` for a setup | `tests/test_verdict_shape.py::test_every_judgement_is_named_with_its_verb`, `tests/test_verdict_shape.py::test_every_judging_method_is_named_with_its_verb`, review |
| [N10](naming.md#n10) | Never start a public function, class or module name with `test` or `Test` | `tests/test_verdict_shape.py::test_no_public_name_is_collected_by_pytest`, `tests/test_verdict_shape.py::test_no_public_module_is_named_like_a_test_file`, `tests/test_removed_names.py::test_the_test_signal_module_is_private` |
| [N11](naming.md#n11) | Name a catalogue lookup `<x>_named` after its `PUBLISHED_<X>`, and take `catalogue=` | `tests/io/test_catalogue_lookups.py::test_a_lookup_is_named_after_the_catalogue_it_searches`, `tests/io/test_catalogue_lookups.py::test_every_lookup_the_packages_publish_takes_a_catalogue`, `tests/io/test_catalogue_lookups.py::test_the_table_here_lists_every_lookup_the_packages_publish` |
| [N12](naming.md#n12) | Name each concept with the one word the library already uses for it | `tests/test_public_vocabulary.py::test_one_concept_is_spelled_one_way`, `tests/test_public_vocabulary.py::test_every_kept_minority_spelling_still_exists` |
| [N13](naming.md#n13) | Name the time signal `x`, first, and a signal of one physical quantity for it, with its unit | `tests/test_public_vocabulary.py::test_the_time_signal_is_x`, `tests/test_public_vocabulary.py::test_a_signal_named_for_its_quantity_carries_its_unit` |
| [N14](naming.md#n14) | Name a parameter `speed_of_sound` or `density`, never by its symbol `c` or `rho` | `tests/test_public_vocabulary.py::test_a_symbol_is_not_a_parameter_name_outside_the_solvers` |
| [N15](naming.md#n15) | Name an array in the plural; a singular vectorized name says it takes either | `tests/test_public_vocabulary.py::test_an_array_of_a_quantity_is_named_in_the_plural` |
| [N16](naming.md#n16) | Put the unit in the name of a scalar quantity, and leave a band axis bare | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py`, `tests/test_public_vocabulary.py::test_one_concept_is_spelled_one_way` |
| [N17](naming.md#n17) | Spell each unit suffix one way: `_deg`, `_s`, `_minutes`, `_hours`, `_kmh`, `_kt` | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_spells_every_unit_one_way`, review |
| [N18](naming.md#n18) | Name an absolute temperature in degrees Celsius, `_c`, and a temperature interval in kelvin, `_k` | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_writes_every_temperature_on_its_scale`, `tests/test_check_parameter_units.py::test_the_temperature_scale_rule_reads_a_name` |
| [N19](naming.md#n19) | Name the pressure of the medium `static_pressure_pa` or `static_pressure_kpa` | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_pressure_of_the_medium_has_one_stem` |
| [N20](naming.md#n20) | End a rate per distance in `_db_per_m`, `_db_per_km` or `_per_m` | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_holds_every_closing_rule` |
| [N21](naming.md#n21) | Never publish one name both bare and with its unit in one subpackage | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_holds_every_closing_rule` |
| [N22](naming.md#n22) | Make every defaulted unit-named parameter and every medium condition keyword-only | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_condition_on_the_tree_is_written_by_name`, `tests/test_check_parameter_units.py::test_a_unit_named_default_is_passed_by_name` |
| [N23](naming.md#n23) | Leave `_db` off a level or a level difference; keep it on other decibel quantities | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_no_level_carries_a_unit_suffix` |
| [N24](naming.md#n24) | Give a name in decibels the noun of its quantity, never qualifiers plus `_db` | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_name_in_decibels_says_its_quantity` |
| [N25](naming.md#n25) | End a published constant's name in its unit unless it is a pure number | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_every_published_constant_says_its_unit` |
| [N26](naming.md#n26) | Name a private constant `_UPPER_SNAKE`, and a transcribed table after its printed table | review |
| [N27](naming.md#n27) | Delete a private constant nothing reads | `scripts/check_dead_constants.py`, `make dead-constants`, `CI: No private constant goes unread` |
| [N28](naming.md#n28) | Spell words out: `microphone`, `laboratory`, `reference`, `standard_deviation`, `frequency`, `confidence` | `tests/test_public_vocabulary.py::test_words_are_spelled_out`, `tests/test_public_vocabulary.py::test_the_row_keys_of_a_verdict_are_spelled_out`, `tests/test_public_vocabulary.py::test_every_kept_spelling_still_exists` |
| [N29](naming.md#n29) | Write `min` and `max` in every public name, `MIN` and `MAX` in a constant | `tests/test_public_vocabulary.py::test_words_are_spelled_out` |
| [N30](naming.md#n30) | Name a count `n_<plural>`, and a limit on one `min_n_` or `max_n_` | `tests/test_public_vocabulary.py::test_a_count_is_n_plural`, `tests/test_public_vocabulary.py::test_every_kept_count_spelling_still_exists` |
| [N31](naming.md#n31) | Name a duration by its quantity, then its unit | `tests/test_public_vocabulary.py::test_a_count_is_n_plural`, `tests/test_public_vocabulary.py::test_a_duration_ends_in_its_unit`, `tests/test_public_vocabulary.py::test_every_kept_duration_spelling_is_still_one` |
| [N32](naming.md#n32) | Spell every identifier and every value a caller types in American English | `scripts/check_identifier_spelling.py`, `make identifier-spelling`, `CI: Every public quantity names its unit` |
| [N33](naming.md#n33) | Write a printed symbol in a public name in lower snake case | review |
| [N34](naming.md#n34) | Name a type alias in PascalCase | review |
| [N35](naming.md#n35) | Put a standard's designation in a name only where it tells two things apart, and write it one way | `tests/test_public_vocabulary.py::test_a_standard_designation_is_written_one_way_and_only_where_it_distinguishes`, `tests/test_public_vocabulary.py::test_the_designation_rule_reads_a_name` |

### API shape

| Rule | Statement | Enforced by |
|---|---|---|
| [A1](api.md#a1) | Give every public name exactly one public address | `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__`, `tests/test_removed_names.py::test_a_leaf_module_publishes_only_what_it_defines`, `tests/test_package_architecture.py::test_every_public_name_is_reachable_from_its_domain`, `tests/test_package_architecture.py::test_no_public_name_is_published_by_two_domains` |
| [A2](api.md#a2) | Declare `__all__` in every public module, listing exactly what it defines and publishes | `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__` |
| [A3](api.md#a3) | Keep the root to the domain packages and four shared names | `scripts/check_api_reference.py`, `tests/test_package_architecture.py::test_every_public_name_is_reachable_from_its_domain` |
| [A4](api.md#a4) | Import a domain package and reach every name through it | review |
| [A5](api.md#a5) | Never publish a type alias, a `TypeVar` or a `Protocol` | `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__`, `tests/test_package_architecture.py::test_a_protocol_declares_its_data_members_as_properties` |
| [A6](api.md#a6) | Publish every type a published record's field can hold | `tests/test_package_architecture.py::test_a_published_field_type_is_published_too` |
| [A7](api.md#a7) | Give every public name a curated API row whose type column is true | `scripts/check_api_reference.py`, `CI: Curated API quick table covers __all__` |
| [A8](api.md#a8) | Import across domain packages only along an edge the architecture test lists | `tests/test_package_architecture.py::test_cross_package_edges_are_whitelisted`, `tests/test_package_architecture.py::test_family_edges_are_whitelisted`, `tests/test_package_architecture.py::test_internal_imports_no_domain_code` |
| [A9](api.md#a9) | Import domain code in `_plot` and `_report` only under `TYPE_CHECKING` | `tests/test_package_architecture.py::test_render_modules_only_type_check_domain_imports` |
| [A10](api.md#a10) | Import matplotlib inside the function that draws, never at module scope | `tests/test_matplotlib_backend.py::test_no_module_scope_matplotlib_import_anywhere`, `tests/test_matplotlib_backend.py::test_import_succeeds_without_matplotlib`, `tests/test_result_plots.py::test_plot_raises_helpful_error_without_matplotlib` |
| [A11](api.md#a11) | Import the package's own modules relatively inside `src` | review |
| [A12](api.md#a12) | Give every source directory an `__init__.py` | `ruff INP001` |
| [A13](api.md#a13) | Remove a renamed or retired name outright, with no alias, shim or warning, before 4.0.0 | `tests/test_removed_names.py`, `scripts/check_api_reference.py`, `tests/test_package_architecture.py::test_a_module_getattr_is_hidden_from_the_type_checker`, `tests/static_typing/test_root_names.py` |
| [A14](api.md#a14) | Record every shipped name you rename or remove in the migration guide's three copies | review |
| [A15](api.md#a15) | Move every caller of a renamed name in the same commit | `scripts/check_doc_snippets.py`, review |
| [A16](api.md#a16) | After 4.0.0, keep a renamed shipped name working for one release with a `DeprecationWarning` | review |
| [A17](api.md#a17) | Take a frequency or wavelength axis by keyword beside the values it labels | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_writes_every_function_axis_by_name` |
| [A18](api.md#a18) | Make every record a caller builds keyword-only | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_writes_every_input_record_axis_by_name`, `tests/test_check_parameter_units.py::test_the_tree_writes_every_input_record_by_name`, `tests/test_check_parameter_units.py::test_every_field_of_an_input_record_is_written_by_name`, `tests/test_check_parameter_units.py::test_a_record_behind_a_union_alias_is_written_by_name`, `tests/test_curated_examples.py::test_no_inline_example_builds_a_record_by_position_or_unpacks_one` |
| [A19](api.md#a19) | Write a boolean by name, in the definition and at the call | `ruff FBT`, `tests/test_package_architecture.py::test_the_grid_flag_is_named_the_way_matplotlib_names_it` |
| [A20](api.md#a20) | Add a `bool` overload beside the `Literal[True]` and `Literal[False]` overloads of a flag | `tests/test_package_architecture.py::test_an_overload_on_a_true_or_false_literal_also_takes_a_bool` |
| [A21](api.md#a21) | Type every fixed choice as a `Literal` of its options, never `str`, and its options tuple alike | `scripts/check_choice_literals.py`, `make choice-literals`, `CI: Check that every fixed public choice is typed Literal`, `tests/test_check_choice_literals.py::test_every_public_choice_of_the_package_is_a_literal`, `tests/test_check_choice_literals.py::test_every_vocabulary_offers_what_its_table_holds`, `tests/test_check_choice_literals.py::test_every_published_table_of_a_vocabulary_is_keyed_by_it`, `tests/test_choice_vocabulary.py::test_no_choice_offers_a_band_set_by_name`, `tests/test_choice_vocabulary.py::test_a_sound_field_is_free_diffuse_or_pressure`, `tests/test_choice_vocabulary.py::test_a_weighting_is_chosen_by_weighting` |
| [A22](api.md#a22) | Choose a band set with `fraction`: 1 for octaves, 3 for one-third octaves | `tests/test_choice_vocabulary.py::test_no_choice_offers_a_band_set_by_name`, `tests/test_choice_vocabulary.py::test_no_table_or_tuple_holds_a_band_set_word`, `tests/test_choice_vocabulary.py::test_a_band_fraction_is_one_or_three`, `tests/test_choice_vocabulary.py::test_anything_else_is_refused_as_a_band_set` |
| [A23](api.md#a23) | Name a sound field `"free"`, `"diffuse"` or `"pressure"` | `tests/test_choice_vocabulary.py::test_a_sound_field_is_free_diffuse_or_pressure`, `tests/test_choice_vocabulary.py::test_a_retired_spelling_is_refused` |
| [A24](api.md#a24) | Choose a frequency weighting with `weighting=`; an unweighted signal is `"Z"` | `tests/test_choice_vocabulary.py::test_a_flat_weighting_is_z`, `tests/test_choice_vocabulary.py::test_a_weighting_is_chosen_by_weighting` |
| [A25](api.md#a25) | Take several values of one kind as one sequence, not as `*args` | review |
| [A26](api.md#a26) | Make `axis` keyword-only | review |
| [A27](api.md#a27) | Put the two ends of a range lower first | `tests/test_public_vocabulary.py::test_the_two_ends_of_a_range_come_lower_first`, `tests/test_public_vocabulary.py::test_the_range_order_rule_reads_a_list`, review |
| [A28](api.md#a28) | Take `ax` first in `.plot()`, data first in `plot_` helpers, the rest by name | `tests/test_result_plots.py::test_every_plot_takes_ax_first_and_the_rest_by_name`, `tests/test_result_plots.py::test_every_plot_helper_takes_its_axes_and_language_by_name`, `tests/test_result_plots.py::test_single_axes_plots_accept_external_ax`, `tests/test_result_plots.py::test_every_plot_forwards_kwargs_to_primary_artist` |
| [A29](api.md#a29) | Take a report's path first, then `metadata` and `language` by name | review |
| [A30](api.md#a30) | Never take a private-named argument in a public constructor | review |
| [A31](api.md#a31) | Annotate every parameter and return; use `Any` only where the set is open | `ruff ANN001`, `ruff ANN401`, `mypy`, `tests/test_package_architecture.py::test_no_published_field_is_typed_any`, `tests/test_package_architecture.py::test_no_published_field_is_typed_dict` |
| [A32](api.md#a32) | Return several different quantities as a frozen record, never a tuple | `scripts/check_parameter_units.py`, `make parameter-units`, `CI: Every public quantity names its unit`, `tests/test_check_parameter_units.py::test_the_tree_answers_several_quantities_as_records`, `tests/test_public_vocabulary.py::test_no_record_unpacks_like_a_tuple` |
| [A33](api.md#a33) | Give a result a `.plot()` that draws its guide figure where a figure says something | review |
| [A34](api.md#a34) | Publish every module-level table immutable, all the way down | `scripts/check_frozen_constants.py`, `make frozen-constants`, `CI: Every published table refuses writes`, `tests/test_package_architecture.py::test_a_record_holding_a_read_only_mapping_travels`, `tests/test_record_conversions.py::test_every_record_survives_pickle_and_deepcopy`, `tests/test_record_conversions.py::test_every_record_holding_a_mapping_is_built_here` |
| [A35](api.md#a35) | Make a field the computation reads required, and refuse `None` for it by name | `tests/test_required_fields.py::test_a_required_field_refuses_none`, `tests/test_required_fields.py::test_an_optional_quantity_may_still_be_absent` |
| [A36](api.md#a36) | Derive a value the stored fields determine as a read-only property | `tests/test_derived_regimes.py`, `tests/test_printed_limits.py::test_no_verdict_takes_a_printed_limit_at_construction`, `tests/test_printed_limits.py::test_no_result_stores_a_verdict_flag` |
| [A37](api.md#a37) | Keep an `io.Signal` a result holds as the object itself, by composition | review |
| [A38](api.md#a38) | Give one formula one function, and one computation one name | review |
| [A39](api.md#a39) | Return a judgment as a record that carries its reasons, never a bare `bool` | `tests/test_verdict_shape.py::test_every_judging_verb_returns_a_record`, `tests/test_verdict_shape.py::test_every_judging_method_returns_a_record`, `tests/test_verdict_shape.py::test_every_exempt_method_still_exists`, `tests/test_verdict_shape.py::test_every_regime_predicate_is_still_published` |
| [A40](api.md#a40) | Spell a pass-or-fail verdict's overall flag `passes` | `tests/test_verdict_shape.py::test_the_overall_flag_is_spelled_passes`, `tests/test_verdict_shape.py::test_every_kept_flag_still_exists`, `tests/test_public_vocabulary.py::test_one_concept_is_spelled_one_way` |
| [A41](api.md#a41) | Make a verdict refuse a truth value, naming the attribute to read | `tests/test_verdict_shape.py::test_every_verdict_refuses_a_truth_value`, `tests/test_verdict_shape.py::test_the_bool_of_every_verdict_raises`, `tests/test_verdict_shape.py::test_a_built_verdict_refuses_a_truth_value`, `tests/test_verdict_shape.py::test_a_real_verdict_refuses_a_truth_value` |
| [A42](api.md#a42) | Raise `TypeError` for a wrong type and `ValueError` for a right type's wrong value | `tests/test_error_kinds.py::test_a_wrong_type_raises_type_error`, `tests/test_error_kinds.py::test_every_exemption_names_a_function_that_exists` |
| [A43](api.md#a43) | Refuse an array or a text where one number belongs with a `TypeError` naming it | `tests/test_scalar_guards.py::test_every_public_scalar_parameter_refuses_an_array_or_a_text_by_name`, `tests/test_scalar_guards.py::test_a_text_where_a_number_belongs_is_one_class_everywhere`, `tests/test_scalar_guards.py::test_a_field_of_text_is_a_type_error` |
| [A44](api.md#a44) | Raise `KeyError` for a missing name or key, `ValueError` for an uncovered value | review |
| [A45](api.md#a45) | Refuse an unknown choice with `ValueError`, and a choice that is not text with `TypeError`, checked as written | `scripts/check_choice_literals.py`, `make choice-literals`, `tests/test_check_choice_literals.py::test_every_literal_choice_is_checked_as_written`, `tests/test_check_choice_literals.py::test_every_literal_choice_is_checked_on_every_path`, `tests/test_choice_vocabulary.py::test_a_retired_spelling_is_refused` |
| [A46](api.md#a46) | Refuse malformed data the library reads with `ValueError` naming the file | review |
| [A47](api.md#a47) | Name in an error message the parameter the caller passed | `tests/test_public_vocabulary.py::test_a_message_names_the_parameter_the_caller_passed`, review |
| [A48](api.md#a48) | Put an error message in a variable before raising it | `ruff EM` |
| [A49](api.md#a49) | Derive every warning from `PhonometryWarning` and publish it from its domain | `tests/test_package_architecture.py::test_every_warning_a_package_can_raise_is_published`, `tests/test_package_architecture.py::test_every_published_warning_is_a_phonometry_warning` |
| [A50](api.md#a50) | Warn with the topic's published class, never `UserWarning` or the bare root | `tests/test_package_architecture.py::test_every_warning_names_a_published_topic` |
| [A51](api.md#a51) | Silence inside the library only the warning topic you mean | `tests/test_package_architecture.py::test_a_warning_filter_in_the_library_names_its_topic` |
| [A52](api.md#a52) | Speak to the caller through warnings, never `print` | `ruff T20` |
| [A53](api.md#a53) | Refuse a value only where the standard bounds it or physics forbids it | review |
| [A54](api.md#a54) | Report progress to a `phonometry.` logger at INFO or DEBUG; never configure logging | `tests/test_package_architecture.py::test_the_library_logs_quietly_to_loggers_of_its_own`, `tests/test_package_architecture.py::test_the_logging_rule_reads_a_loud_logger`, `tests/test_package_architecture.py::test_the_logging_rule_reads_every_spelling_of_a_logger`, `tests/test_package_architecture.py::test_the_logging_rule_reads_every_way_of_configuring`, `tests/test_package_architecture.py::test_the_logging_rule_follows_a_logger_from_module_to_module` |
| [A55](api.md#a55) | Give every parameter of a function that runs on a node, and every field of the records it takes, a form that travels as data | `tests/simulation/test_remote_wire.py::test_every_parameter_of_a_remote_function_travels`, `tests/simulation/test_remote_wire.py::test_every_field_of_a_run_travels`, `tests/simulation/test_remote_wire.py::test_the_guard_names_every_function_a_node_runs`, `tests/simulation/test_remote_simulation.py::test_the_remote_route_sends_every_parameter`, `tests/simulation/test_video_remote.py::test_the_remote_route_sends_every_parameter`, `CI: Remote simulation on a localhost node` |
| [A56](api.md#a56) | Run a program the library does not ship by its full path, check everything before it starts, and fake it in tests | `CI: Videos encode with a real ffmpeg`, `CI: Remote simulation on a localhost node`, `tests/io/test_video_encoders.py`, `tests/simulation/test_remote_command.py`, `tests/test_internal_programs.py`, `bandit` |
| [A57](api.md#a57) | Overload a return whose type one argument decides | `scripts/check_return_overloads.py`, `make return-overloads`, `CI: Every return an argument decides is overloaded on it`, `tests/test_check_return_overloads.py::test_the_package_keeps_the_rule`, `tests/test_result_plots.py::test_a_plot_returns_what_its_signature_promises`, `tests/test_result_plots.py::test_every_decided_plot_has_a_built_result`, `tests/test_scalar_or_array_returns.py::test_every_function_of_a_number_or_an_array_has_a_case` |
| [A58](api.md#a58) | Annotate a parameter with every type its validation accepts | `scripts/check_parameter_annotations.py`, `make parameter-annotations`, `CI: Every public parameter admits what its body converts`, `tests/test_check_parameter_annotations.py::test_the_package_keeps_the_rule`, `tests/test_record_constructors.py::test_every_record_says_what_its_constructor_takes`, `tests/test_record_constructors.py::test_every_record_a_guide_builds_is_read_as_built_by_a_caller`, `scripts/check_array_aliasing.py`, `tests/test_record_conversions.py::test_a_list_given_to_a_converted_field_is_held_converted`, `tests/test_package_architecture.py::test_a_static_case_names_an_array_of_a_given_dtype_before_the_call`, `tests/test_package_architecture.py::test_a_numpy_number_taken_alone_is_taken_in_a_sequence_too`, `mypy` |
| [A59](api.md#a59) | Set a `Literal` choice beside numbers as `NumericArrayLike`, never beside a type that takes any text, and refuse a text where its numbers go | `scripts/check_parameter_annotations.py`, `make parameter-annotations`, `CI: Every public parameter admits what its body converts`, `tests/test_check_parameter_annotations.py::test_a_choice_beside_an_alternative_that_takes_any_text_is_refused`, `tests/test_check_parameter_annotations.py::test_the_array_like_of_numbers_is_read_as_one`, `tests/test_check_parameter_annotations.py::test_the_package_keeps_the_rule`, `tests/test_choices_beside_numbers.py::test_every_choice_beside_numbers_is_walked`, `tests/test_choices_beside_numbers.py::test_a_choice_beside_numbers_refuses_what_is_no_number_by_name`, `tests/test_choices_beside_numbers.py::test_no_body_reads_a_choice_its_annotation_does_not_state`, `mypy` |

### Docstrings and comments

| Rule | Statement | Enforced by |
|---|---|---|
| [D1](docstrings.md#d1) | Name in a module docstring the document it implements, with its edition | review |
| [D2](docstrings.md#d2) | Cite a draft standard by its full dated designation, and say it is a draft | review |
| [D3](docstrings.md#d3) | Say in the docstring which reading is the library's where the standard prints none | review |
| [D4](docstrings.md#d4) | Write docstring fields as a Sphinx field list: `:param`, `:return`, `:raises`, `:warns`, `:ivar` | review |
| [D5](docstrings.md#d5) | Document only the parameters the signature has | `tests/test_package_architecture.py::test_no_docstring_documents_a_parameter_that_is_gone` |
| [D6](docstrings.md#d6) | Keep a docstring's field list unbroken: no prose between two fields | `tests/test_package_architecture.py::test_no_docstring_breaks_its_own_field_list`, `tests/test_package_architecture.py::test_no_docstring_field_is_cut_in_two` |
| [D7](docstrings.md#d7) | State the unit of every numeric parameter, field and return, as the source prints it | review |
| [D8](docstrings.md#d8) | Open a docstring with a noun phrase, on the line of its opening quotes | `ruff D212`, review |
| [D9](docstrings.md#d9) | Never open a judgment's summary with another judgment family's verb | `tests/test_package_architecture.py::test_a_judgement_summary_does_not_open_with_another_family_verb` |
| [D10](docstrings.md#d10) | Give a magic method a docstring | `ruff D105` |
| [D11](docstrings.md#d11) | Document every `TypeError` a function raises, naming each parameter it refuses | `tests/test_error_kinds.py::test_a_public_function_that_raises_type_error_documents_it`, `tests/test_error_kinds.py::test_a_type_error_a_shared_validator_raises_is_documented_too`, `tests/test_error_kinds.py::test_a_type_error_field_names_every_parameter_it_hands_on`, `tests/test_error_kinds.py::test_a_plot_is_followed_into_the_renderer_that_refuses_its_keywords`, `tests/test_error_kinds.py::test_the_keywords_are_followed_however_they_are_handed_on`, `tests/test_error_kinds.py::test_a_choice_handed_on_names_the_type_error_of_where_it_goes`, `tests/test_error_kinds.py::test_a_choice_is_followed_however_it_is_handed_on` |
| [D12](docstrings.md#d12) | List a warning under `:warns`, never under `:raises` | `tests/test_package_architecture.py::test_a_docstring_lists_a_warning_under_warns` |
| [D13](docstrings.md#d13) | Cite a standard by clause, table or formula; a book also by PDF page and folio | review |
| [D14](docstrings.md#d14) | Write docstring mathematics with one backslash per command, in a raw docstring | `scripts/check_docstring_math.py`, `make docstring-math`, `CI: Docstring mathematics reaches the page intact`, `ruff D301` |
| [D15](docstrings.md#d15) | Brace a TeX command used as a subscript or superscript | `scripts/check_docstring_math.py`, `make docstring-math`, `CI: Docstring mathematics reaches the page intact` |
| [D16](docstrings.md#d16) | Set a subscript upright for an abbreviated word, italic for a quantity or an index | `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file`, review |
| [D17](docstrings.md#d17) | Follow the print letter by letter where a standard sets both slopes in one symbol | review |
| [D18](docstrings.md#d18) | Where a source prints every subscript in one slope, let ISO 80000-2 decide each letter | `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file`, review |
| [D19](docstrings.md#d19) | Give each subscript one slope in a file and in the images it embeds | `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file`, `tests/test_check_subscript_slope.py::test_the_tree_it_ships_with_passes` |
| [D20](docstrings.md#d20) | Set KB, the weighted vibration severity, italic in every file and image | `scripts/check_subscript_slope.py`, `make subscripts`, `CI: One meaning per subscript per file` |
| [D21](docstrings.md#d21) | Set Euler's number upright: `\mathrm{e}` | `scripts/check_euler_number.py`, `make euler-number`, `CI: Euler's number is upright` |
| [C1](docstrings.md#c1) | Write a comment for the why or the citation, never to restate the code | review |
| [C2](docstrings.md#c2) | Above a table transcribed from a book or a paper, cite its PDF page and folio | `scripts/check_published_sources.py`, `make published-sources`, `CI: Every published value names its page` |
| [C3](docstrings.md#c3) | Never commit commented-out code | review |
| [C4](docstrings.md#c4) | Give every suppression its reason, on the line above a `noqa` and after a `nosec`'s codes | `tests/test_package_architecture.py::test_no_suppression_comment_hides_its_reason_from_the_parser`, review |
| [C5](docstrings.md#c5) | Fix a SonarCloud finding; never suppress it with NOSONAR | review |
| [D22](docstrings.md#d22) | Judge a module's length by its subject, never by a line count | review |
| [D23](docstrings.md#d23) | Split a module as a pure move: names, docstrings, bodies and outputs unchanged | `make conformance`, review |

### Numbers and data

| Rule | Statement | Enforced by |
|---|---|---|
| [X1](numerics.md#x1) | Never compare a float for equality in src; make the zero stop being a case | `tests/test_package_architecture.py::test_no_source_compares_a_float_for_equality` |
| [X2](numerics.md#x2) | Settle a computed value before comparing it with a printed limit | `scripts/check_boundary_comparisons.py`, `make boundary-comparisons`, `CI: No verdict hangs on the last bits of a computed decimal` |
| [X3](numerics.md#x3) | Compare at a printed limit the way the source prints it, strict or inclusive | `scripts/check_boundary_comparisons.py`, review |
| [X4](numerics.md#x4) | Name a number in a comparison, or give its `noqa` a reason | `ruff PLR2004` |
| [X5](numerics.md#x5) | Make a guard that refuses non-positive values refuse NaN too | review |
| [X6](numerics.md#x6) | Ask a scalar parameter its rank before reading or comparing it as one number | `tests/test_scalar_guards.py::test_no_guard_in_the_tree_leaves_the_rank_to_numpy`, `tests/test_scalar_guards.py::test_every_public_scalar_parameter_refuses_an_array_or_a_text_by_name` |
| [X7](numerics.md#x7) | Read a whole-number parameter through `require_count`, never through `int()` | `tests/test_error_kinds.py::test_a_whole_number_goes_through_require_count` |
| [X8](numerics.md#x8) | Refuse a 2-D signal in a single-channel analysis; never ravel it | `tests/test_multichannel_rejection.py`, review |
| [X9](numerics.md#x9) | Say in every `zip()` whether its inputs must be the same length | `ruff B905` |
| [X10](numerics.md#x10) | Keep your own read-only copy of every array a result or object holds | `scripts/check_array_aliasing.py`, `make array-aliasing`, `CI: Every result keeps its own copy of the arrays it was given`, `tests/test_owns_arrays.py`, `tests/test_bytearray_refusals.py` |
| [X11](numerics.md#x11) | Hand a record its array as it is; never copy it first | `scripts/check_array_aliasing.py`, `make array-aliasing`, `CI: Every result keeps its own copy of the arrays it was given` |
| [X12](numerics.md#x12) | Use `handed_over` only for a new array the factory built and returns at once | `scripts/check_array_aliasing.py`, `make array-aliasing`, `CI: Every result keeps its own copy of the arrays it was given` |
| [X13](numerics.md#x13) | Take the caller's unit and convert inside, keeping the source's printed constants literal | `tests/test_package_architecture.py::test_clause_poles_are_not_migrated_to_the_physical_bound`, review |
| [X14](numerics.md#x14) | Read a reference value from `REFERENCE_VALUES`; never type it again | `scripts/check_reference_values.py`, `make reference-values`, `CI: Every reference value points at ISO 1683 or names its source`, `tests/test_check_reference_values.py::test_the_package_is_clean` |
| [X15](numerics.md#x15) | Size a numerical setting until its error stops being measurable, not until it passes | review |
| [X16](numerics.md#x16) | Write a published record's source as `<Document> <Table>, PDF page N (printed p. M)` | `scripts/check_published_sources.py`, `make published-sources`, `CI: Every published value names its page`, `tests/test_check_published_sources.py` |
| [X17](numerics.md#x17) | Keep a packaged catalogue as strict JSON that cites its source, with unique keys | `tests/test_internal_catalogue.py` |
| [X18](numerics.md#x18) | Write a catalogue number as printed, and say in words why a cell is empty | `tests/test_internal_catalogue.py::test_no_number_carries_more_digits_than_a_page_prints`, `tests/test_internal_catalogue.py::test_an_unquantified_cell_holds_what_the_page_printed`, `tests/test_internal_catalogue.py::test_a_not_derivable_cell_says_why_in_words`, `tests/test_internal_catalogue.py::test_a_misprinted_cell_says_what_the_page_printed_and_why_it_cannot_be` |
| [X19](numerics.md#x19) | Publish both values when two printed sources disagree; never vote by majority | `scripts/check_solid_agreement.py`, `scripts/check_shared_sources.py`, `make solid-agreement`, `make shared-sources`, `CI: The books agree about the solids they share`, `tests/test_check_solid_agreement.py` |
| [X20](numerics.md#x20) | Rename a catalogue field in its data, spec, schema, baseline and translations together | `tests/test_published_catalogue_fingerprint.py::test_every_published_row_is_the_baseline_carried_through_the_changes`, `make catalogue-data`, `make catalogue-schema` |
| [X21](numerics.md#x21) | Touch an engine's field only with Array API standard operations | `CI: FDTD engines on array-api-strict and torch (CPU)`, `CI: FDTD engines hold their golden digests`, `make engine-digests`, `tests/simulation/test_engine_golden_digests.py`, `tests/simulation/test_gpu_parity_lock.py` |

### Tests

| Rule | Statement | Enforced by |
|---|---|---|
| [T1](tests.md#t1) | Give each module one test file, named `test_<module>.py` | review |
| [T2](tests.md#t2) | Give every test file a basename no other test file uses | `tests/test_package_architecture.py::test_collected_test_modules_have_unique_import_names` |
| [T3](tests.md#t3) | Derive an expected value from the printed standard, never from the code under test | review |
| [T4](tests.md#t4) | Without a printed worked example, test closed forms and say so in the module | review |
| [T5](tests.md#t5) | Commit the data a test reads, with a note of its source; never commit documents | review |
| [T6](tests.md#t6) | Never skip an assertion on committed oracle data; skip only full-set tests, saying why | review |
| [T7](tests.md#t7) | Put one call that can raise inside a `pytest.raises`, `pytest.warns` or `pytest.deprecated_call` block | `scripts/check_raises_blocks.py`, `make raises-blocks`, `CI: Every exception test waits on one call`, `ruff PT012`, `tests/test_check_raises_blocks.py` |
| [T8](tests.md#t8) | Match every `pytest.raises` to its quoted identifier and a stable predicate | `ruff PT011`, review |
| [T9](tests.md#t9) | Never pin a test to numpy's or Python's own message; validate in the function | review |
| [T10](tests.md#t10) | Name the topic warning class in `pytest.warns`, never `UserWarning` | review |
| [T11](tests.md#t11) | Pin a retired public name as gone in `tests/test_removed_names.py` | review |
| [T12](tests.md#t12) | Test what a renderer draws, and add it to the plot contract | `tests/test_result_plots.py`, `tests/test_answer_record_plots.py`, review |
| [T13](tests.md#t13) | Show a new value test failing on a deliberately broken copy | review |
| [T14](tests.md#t14) | Close a defect's whole class with a guard, and watch the guard fail on it | review |
| [T15](tests.md#t15) | Key every guard exemption by location with its reason, and fail a stale one | review |
| [T16](tests.md#t16) | Read public names from the imported package, and source text through `ast` | review |
| [T17](tests.md#t17) | Fix a tool that misreads correct data; never trim the data to pass | review |
| [T18](tests.md#t18) | Mark a test of the figure, diagram or badge tooling `pinned_stack` | `tests/test_minimum_requirements.py`, `CI: Library tests at the dependency floors` |
| [T19](tests.md#t19) | Group the tests of an expensive module fixture with `xdist_group` | review |
| [T20](tests.md#t20) | Make every conformance row call the library; never recompute the expected value | `scripts/check_conformance_rows.py`, `make conformance-rows`, `CI: Every conformance row runs the library` |
| [T21](tests.md#t21) | Add a new conformance vocabulary value to the site schema and both label maps | `scripts/check_conformance_vocabulary.py`, `make conformance-vocabulary`, `CI: Conformance report up to date` |
| [T22](tests.md#t22) | Write every workflow so that zizmor finds nothing under `.github/` | `CI: Audit the workflows with zizmor` |
| [T23](tests.md#t23) | Pin every action to a release tag, never a branch or a commit SHA | `tests/test_repository_config.py::test_every_action_is_pinned_to_a_release_tag`, `CI: Audit the workflows with zizmor` |
| [T24](tests.md#t24) | Bound every wait a test makes on another process or thread | `tests/test_child_process.py::test_every_wait_in_the_suite_has_a_bound`, review |
| [T25](tests.md#t25) | Filter a warning in the pytest configuration by a builtin class, never an imported one | `tests/test_repository_config.py::test_the_pytest_configuration_filters_warnings_by_builtin_class` |

### Documentation and figures

| Rule | Statement | Enforced by |
|---|---|---|
| [F1](docs-and-figures.md#f1) | Change a guide's English page, Spanish twin and docs/ mirror together | `site/scripts/check-i18n-parity.mjs`, review |
| [F2](docs-and-figures.md#f2) | Write the docs mirror without frontmatter, and its figures as absolute `<picture>` links | review |
| [F3](docs-and-figures.md#f3) | Link every new guide from `docs/README.md` | `scripts/mirror_overviews.py`, `scripts/generate_llms.py` |
| [F4](docs-and-figures.md#f4) | Register a new guide in `topics.mjs` and the guides index, counted in figures and words | `site/scripts/check-guides-index.mjs`, `CI: Site builds and validates` |
| [F5](docs-and-figures.md#f5) | Never edit a generated file by hand; change its source and regenerate it | `scripts/mirror_overviews.py`, `scripts/check_conformance_artifact.py`, `make conformance`, `CI: Conformance report up to date`, `CI: llms artifacts up to date` |
| [F6](docs-and-figures.md#f6) | Never type a conformance count in prose; `make conformance` writes it | `scripts/check_conformance_claims.py`, `make conformance`, `CI: Conformance report up to date` |
| [F7](docs-and-figures.md#f7) | Put a site page's references in its frontmatter, never under a hand-written heading | `CI: Site builds and validates` |
| [F8](docs-and-figures.md#f8) | Give every `<ScopeClaim>` its `status` | `CI: Site builds and validates` |
| [F9](docs-and-figures.md#f9) | Pass `<ThemeImage>` the plain figure name; it adds the language and theme suffixes | `CI: Site builds and validates` |
| [F10](docs-and-figures.md#f10) | Link an API reference page by its hyphenated module slug | review |
| [F11](docs-and-figures.md#f11) | Write only absolute URLs in README.md: it is the PyPI page | review |
| [F12](docs-and-figures.md#f12) | Never let a hard-wrapped line start with `-`, `>`, `=` or `N.` in mid-sentence | `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads` |
| [F13](docs-and-figures.md#f13) | Link an accented heading through an ASCII `<span id>` placed above it | `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads`, `site/scripts/check-crawl.mjs`, `CI: Check what a search engine reads on every page` |
| [F14](docs-and-figures.md#f14) | Open and close a `$$` display block on lines of their own | `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads` |
| [F15](docs-and-figures.md#f15) | Escape a `<` in MDX prose unless a space or a tag name follows it | `scripts/check_markdown_hazards.py`, `make hazards`, `CI: Markdown renders the way it reads` |
| [F16](docs-and-figures.md#f16) | Write a page's Python blocks to run in reading order, on this branch's names | `scripts/check_doc_snippets.py`, `make snippets`, `CI: Documentation snippets run` |
| [F17](docs-and-figures.md#f17) | Use in a fence only names that an earlier fence of the same page defined | `scripts/check_fence_names.py`, `make fence-names`, `CI: Documentation fences read in order` |
| [F18](docs-and-figures.md#f18) | Define an annotated value in the fence that annotates it, or the one just before | review |
| [F19](docs-and-figures.md#f19) | Register a name the reader owns in `PLACEHOLDERS`, and introduce it as theirs | `scripts/check_fence_names.py`, `make fence-names`, `CI: Documentation fences read in order` |
| [F20](docs-and-figures.md#f20) | Never rebind a name imported from phonometry inside a documentation example | `scripts/check_doc_snippets.py`, `make snippets-static`, `CI: Documentation snippets run` |
| [F21](docs-and-figures.md#f21) | Import exactly the same phonometry names on a Spanish page as on its English twin | `scripts/check_doc_snippets.py`, `make snippets-static`, `CI: Documentation snippets run` |
| [F22](docs-and-figures.md#f22) | Fence an example that must not run as `py`; only a `python` fence runs | `scripts/check_doc_snippets.py`, `tests/test_contributing_guide.py` |
| [F23](docs-and-figures.md#f23) | Read a page's fences through `scripts/markdown_fences.py`, never by hand | `scripts/check_fence_readers.py`, `make fence-readers`, `CI: Markdown renders the way it reads` |
| [F24](docs-and-figures.md#f24) | Show in a guide figure a realistic result through its `.plot()`, one concept each | review |
| [F25](docs-and-figures.md#f25) | Give each figure its code in a `<details>`: the `.plot()` line and plain matplotlib | review |
| [F26](docs-and-figures.md#f26) | Give an example the real dimensions of a standard's or common equipment's setup | review |
| [F27](docs-and-figures.md#f27) | Pass the caller's language on to every helper that takes one | `scripts/check_language_forwarding.py`, `make language-forwarding`, `CI: Every call passes the language on` |
| [F28](docs-and-figures.md#f28) | Write every number of a Spanish figure with a decimal comma | `tests/test_plot_localized_panels.py`, `scripts/check_figure_decimal_point.py`, `make figure-decimal-point`, `CI: Documentation figures up to date` |
| [F29](docs-and-figures.md#f29) | Format a number in a label beside mathtext through `format_number(value, language)` | `scripts/check_decimal_comma.py`, `make decimal-comma`, `CI: Documentation figures up to date` |
| [F30](docs-and-figures.md#f30) | Sign a negative number in a figure or plate with U+2212, never a hyphen | `scripts/check_figure_minus_sign.py`, `make figure-minus-sign`, `CI: Documentation figures up to date` |
| [F31](docs-and-figures.md#f31) | Add every string a figure draws to the Spanish translation tables, in the same edit | `scripts/check_figure_language.py`, `make figure-language`, `CI: Documentation figures up to date` |
| [F32](docs-and-figures.md#f32) | Translate a label built from fixed numbers as an exact entry, not a pattern | `scripts/check_animation_freshness.py`, `make animation-freshness` |
| [F33](docs-and-figures.md#f33) | Default a matplotlib style through `style_default`, `style_get`, `style_pop` or `styled` | `scripts/check_plot_style_defaults.py`, `make plot-style-defaults`, `CI: Every call passes the language on`, `tests/test_check_plot_style_defaults.py::test_the_package_is_clean` |
| [F34](docs-and-figures.md#f34) | Copy the keyword arguments per curve before setting a label inside a loop | `tests/test_result_plots.py::test_no_renderer_defaults_a_label_on_the_shared_kwargs_inside_a_loop` |
| [F35](docs-and-figures.md#f35) | Label a frequency axis with `format_frequency_axis`, and clear hand-set log minor labels | `scripts/check_figure_ticks.py`, `make figure-ticks`, `CI: Documentation figures up to date`, review |
| [F36](docs-and-figures.md#f36) | Wrap only mathematics in `$...$`; words, units and numbers stay text | review |
| [F37](docs-and-figures.md#f37) | Write mathtext a figure label can parse; never chain two superscripts | `scripts/check_mathtext.py`, `make mathtext`, `CI: Documentation figures up to date` |
| [F38](docs-and-figures.md#f38) | Set figure titles in regular weight, never bold | review |
| [F39](docs-and-figures.md#f39) | Name a plate's descriptive letter outside `_ROMAN_SCRIPTS` with `upright=`, a sloped one with `sloped=` | `scripts/check_subscript_slope.py`, `make subscripts` |
| [F40](docs-and-figures.md#f40) | Generate every documentation image with `make graphs`, and commit exactly what it writes | `scripts/check_figures.py`, `make figures`, `CI: Documentation figures up to date` |
| [F41](docs-and-figures.md#f41) | Register a figure, diagram or fiche builder in its package's registry | review |
| [F42](docs-and-figures.md#f42) | Draw figure text as outlines and save every figure byte-stable | `scripts/check_figures.py`, `make figures`, `CI: Documentation figures up to date` |
| [F43](docs-and-figures.md#f43) | Move a figure only on purpose, then look at it in light, dark and Spanish | `scripts/check_figures.py`, `CI: Documentation figures up to date`, review |
| [F44](docs-and-figures.md#f44) | Move a label off a curve, or chip it opaquely above the curves | `scripts/check_figure_annotations.py`, `make figure-annotations`, `CI: Documentation figures up to date` |
| [F45](docs-and-figures.md#f45) | Draw nothing over a tick label: legends, curves, markers and insets stay clear | `scripts/check_figure_tick_clearance.py`, `make figure-tick-clearance`, `CI: Documentation figures up to date` |
| [F46](docs-and-figures.md#f46) | Place a hand-set label clear of tick labels, other text and strokes, in both languages | `scripts/check_figure_text_clearance.py`, `make figure-text-clearance`, `CI: Documentation figures up to date` |
| [F47](docs-and-figures.md#f47) | Place a legend or a label's chip where it covers no plotted point, in English and in Spanish | `scripts/check_figure_legends.py`, `make figure-legends`, `CI: Documentation figures up to date` |
| [F48](docs-and-figures.md#f48) | Shade a region so it clears CIEDE2000 10 against the page in both themes | `scripts/check_figure_contrast.py`, `make figure-contrast`, `CI: Documentation figures up to date` |
| [F49](docs-and-figures.md#f49) | Keep every line legible on the dark page: 3:1 for hairlines, 2:1 for thicker strokes | `scripts/check_stroke_contrast.py`, `CI: Documentation figures up to date` |
| [F50](docs-and-figures.md#f50) | Color a fiche's bars by category with a legend; never rotate long tick labels | review |
| [F51](docs-and-figures.md#f51) | Publish animation clips to phonometry-assets; never commit a clip to this repository | `scripts/check_figures.py`, `scripts/check_animation_freshness.py` |
| [F52](docs-and-figures.md#f52) | Re-render a clip whenever the code that draws it changes | `scripts/check_animation_freshness.py`, `make animation-freshness` |
| [F53](docs-and-figures.md#f53) | Embed an animation lazily, with its space reserved | review |
| [F54](docs-and-figures.md#f54) | Let every public record inherit `RichDisplay`, and give it no display method of its own | `scripts/check_record_display.py`, `make record-display`, `CI: Every public record shows itself as a table in a notebook`, `tests/test_check_record_display.py::test_the_package_shows_every_public_record_as_a_table`, `scripts/check_notebook.py`, `CI: phonometry runs in a notebook kernel` |
| [F55](docs-and-figures.md#f55) | Let a record field's unit read from its name, or declare it in `_display_units` | `tests/test_record_display.py::test_every_unit_a_record_names_is_needed_and_shown`, `tests/test_record_display.py::test_no_public_field_that_holds_no_number_is_shown_in_a_unit`, `tests/test_record_display.py::test_every_public_field_ending_in_a_unit_shows_it`, `tests/test_record_display.py::test_a_number_its_name_misreads_shows_its_own_unit` |
| [F56](docs-and-figures.md#f56) | Register every `PUBLISHED_` catalogue in the catalogues page generator | `scripts/check_published_catalogues_reach_the_page.py`, `make published-catalogues`, `CI: Every published value names its page`, `site/src/lib/catalogue-pages.ts` |
| [F57](docs-and-figures.md#f57) | Cite an errata entry's page by document, edition, PDF page and printed folio | `scripts/check_errata_evidence.py`, `CI: Errata entries cite their page` |
| [F58](docs-and-figures.md#f58) | Quote a printed value, its symbols and its separator exactly as the source prints them | review |
| [F59](docs-and-figures.md#f59) | Add or remove an errata entry in docs/ERRATA.md and docs/ERRATA.es.md together | `make site-reports`, `CI: Generated evidence pages up to date` |
| [F60](docs-and-figures.md#f60) | Hold every frame of a clip to the figure gates before it is encoded | `scripts/clip_frame_audit.py`, `make animation-audit`, `tests/test_clip_frame_audit.py` |
| [F61](docs-and-figures.md#f61) | Step a clip's field where the registry puts it, and keep it on that device between captures | `tests/test_clip_scenes_on_devices.py`, `tests/test_clip_placement.py` |
| [F62](docs-and-figures.md#f62) | Quote the extras of every install command | `scripts/check_quoted_extras.py`, `CI: Every install command quotes its extras`, `tests/test_check_quoted_extras.py` |
| [F63](docs-and-figures.md#f63) | Give every page a description of 160 characters or fewer that no other page of its language repeats | `site/scripts/check-descriptions.mjs`, `CI: Check every page has a short meta description of its own`, `site/scripts/check-descriptions.test.mjs`, `CI: Test the build checks on small builds made to fail them`, `tests/test_api_docs_generator.py::test_every_api_page_has_a_description_short_enough_to_show_whole` |
| [F64](docs-and-figures.md#f64) | Keep every built page under 1 800 000 bytes of HTML | `site/scripts/check-page-size.mjs`, `CI: Check every page fits in what a search engine reads` |

### Prose, commits and pull requests

| Rule | Statement | Enforced by |
|---|---|---|
| [P1](prose.md#p1) | Write code, docs/ and the English site in English, the Spanish site in Spanish | `site/scripts/check-i18n-parity.mjs`, review |
| [P2](prose.md#p2) | Write every Spanish string with its accents and eñes | `scripts/check_spanish_accents.py`, `make spanish-accents`, `CI: Markdown renders the way it reads`, `tests/test_check_spanish_accents.py::test_the_published_tables_carry_every_accent` |
| [P3](prose.md#p3) | Use the glossary's Spanish terms: sinusoide, diezmado, valor cuadrático medio, balance | `scripts/check_spanish_accents.py`, `make spanish-accents`, `CI: Markdown renders the way it reads`, `tests/test_check_spanish_accents.py` |
| [P4](prose.md#p4) | Settle a Spanish term on three independent sources, never on the corpus's majority | review |
| [P5](prose.md#p5) | Translate every catalogue string you add or change, in `catalogue-es.json` | `scripts/generate_catalogue_data.py`, `make catalogue-data`, `CI: Every published value names its page` |
| [P6](prose.md#p6) | Write no em dash anywhere | `scripts/check_em_dashes.py`, `CI: Markdown renders the way it reads`, review |
| [P7](prose.md#p7) | Use no control character but tab and newline in a tracked text file | `scripts/check_control_characters.py`, `make control-characters`, `CI: No stray control character` |
| [P8](prose.md#p8) | Group a long digit string in threes with U+202F, the narrow no-break space | `scripts/check_digit_grouping.py`, `make digit-grouping`, `CI: Every call passes the language on` |
| [P9](prose.md#p9) | Write the decimal point in an error message; a quotation keeps its source's separator | `tests/test_package_architecture.py::test_no_error_message_carries_a_comma_decimal` |
| [P10](prose.md#p10) | State what a page prints and where, never how the page was read | `scripts/check_errata_evidence.py`, `CI: Errata entries cite their page`, review |
| [P11](prose.md#p11) | Add a CHANGELOG entry under `[Unreleased]` for every new public name and user-visible break | review |
| [P12](prose.md#p12) | Open a CHANGELOG entry with a bold one-line title, then what changed for the user | review |
| [P13](prose.md#p13) | Rename an unreleased name in its CHANGELOG entries; never add a rename line | review |
| [P14](prose.md#p14) | Write a commit subject as what the user gets from the change | review |
| [P15](prose.md#p15) | Write commits and pull requests in your own voice, never about the maintainer in the third person | review |
| [P16](prose.md#p16) | Name no plan, phase, wave or task in a commit or pull request | review |
| [P17](prose.md#p17) | Write each paragraph of a pull request body on one line | review |
| [P18](prose.md#p18) | End a pull request that adds a guard with its red and green output | review |

## Rules no script checks yet

These rules are held by review alone, or a check covers only part of them, and a script could check the rest. Each line names the rule and the idea of the check. A contribution that adds one of these checks names it in the rule's `Enforced by` line, on the page and in the table above, and takes the rule off this list.

- [N1](naming.md#n1): refuse a public module whose path holds a standard designation (`iso`, `iec`, `en`, `din`, `ansi` or `astm` followed by digits); `_report` stays exempt by its path.
- [N4](naming.md#n4): list the public functions whose return annotation is a public class that does not end in `Result`, `Check`, `Verification` or `Assessment`, against an exemption table with reasons.
- [N7](naming.md#n7): refuse a public function or method named `get_`, `calculate_`, `compute_` or `calc_`.
- [N17](naming.md#n17): refuse a public name ending in `_min` whose annotation or `:param` text says minutes, beyond the quantities the guard already lists.
- [N33](naming.md#n33): refuse a public function, parameter, field or property name that holds an upper-case letter.
- [N34](naming.md#n34): refuse a module-level `Literal` or `TypeAlias` assignment whose name is not PascalCase.
- [A4](api.md#a4): scan `docs/`, the site guides, `scripts/figures`, `scripts/conformance` and `tests` for `from phonometry.<path> import <name>` where the name is not a module, and for imports through a private module path.
- [A11](api.md#a11): refuse an absolute `phonometry` import inside `src/phonometry`.
- [A14](api.md#a14): diff the public names of the last release tag against the branch and require a row in the three copies of the migration guide for every name gone.
- [A15](api.md#a15): search the docs, the site guides and `scripts/` for every name `tests/test_removed_names.py` pins as gone.
- [A16](api.md#a16): after 4.0, require every `DeprecationWarning` to carry `stacklevel` and a message naming the version it was deprecated in, the version it goes in and the replacement.
- [A25](api.md#a25): refuse a variadic public function outside an exemption table with reasons (`cascade`, `combine_fault_lines`, `catalogue_schema`).
- [A26](api.md#a26): refuse a public parameter named `axis` that is not keyword-only.
- [A29](api.md#a29): walk every public `report` method: the path first, every other parameter keyword-only, `metadata` and `language` present.
- [A30](api.md#a30): refuse a public dataclass field or public constructor parameter whose name starts with an underscore.
- [A37](api.md#a37): require the docstring of every public record with a field typed `Signal | NDArray` to say that the field holds a Signal when one came in.
- [A44](api.md#a44): an AST check that a public `__getitem__` or `requirement()` that misses raises `KeyError`, and that a plot selector raises `ValueError`.
- [A47](api.md#a47): read the messages of public functions defined in private modules too, and refuse a quoted name that is neither a parameter of the function nor a field of its record.
- [D1](docstrings.md#d1): require the first paragraph of every public module docstring to name a designation with its year, or a dated book, against an exemption table.
- [D2](docstrings.md#d2): refuse a draft designation (`E DIN`, `ISO/DIS`, `prEN`, `FprEN`) in a docstring without its date.
- [D4](docstrings.md#d4): refuse `:type`, `:rtype` and `:returns:` fields and numpydoc section headers in `src` docstrings.
- [D7](docstrings.md#d7): a heuristic over the numeric `:param`, `:ivar` and `:return` fields that name no unit, in the text or in the name, against an exemption table.
- [D8](docstrings.md#d8): refuse a public docstring that opens with Return, Get, Calculate or Compute.
- [D13](docstrings.md#d13): require a `PDF page N` citation in a docstring to be followed by its printed folio.
- [C3](docstrings.md#c3): refuse a comment line that parses as a Python statement, section banners excepted.
- [C4](docstrings.md#c4): require a comment line directly above every `noqa` in `src`, `scripts` and `tests`.
- [C5](docstrings.md#c5): search `src`, `scripts` and `tests` for `NOSONAR`.
- [X5](numerics.md#x5): an AST check that every `if <param> <= 0: raise` has a finiteness check or a shared guard on the same parameter in its function.
- [X8](numerics.md#x8): an AST check that refuses `.ravel()` or `.flatten()` on the samples of a public function's signal parameter.
- [T1](tests.md#t1): map each domain module to `tests/**/test_<module>.py`, with an exemption table for helpers tested through their public modules.
- [T5](tests.md#t5): refuse a committed document (a PDF, a scanned page) under `tests/data` and require a note file in each dataset folder.
- [T8](tests.md#t8): extend ruff's `raises-extend-require-match-for` to `TypeError`, `FrozenInstanceError` and `CatalogueError`, or require `match=` on every `pytest.raises`.
- [T10](tests.md#t10): refuse `pytest.warns(UserWarning)` and `pytest.warns(PhonometryWarning)` in the tests.
- [T11](tests.md#t11): require a pin in `tests/test_removed_names.py` for every row of the migration guide's table of names gone.
- [T12](tests.md#t12): fail a public result class with a `.plot()` and no row in `_KWARG_PLOT_CASES`.
- [T14](tests.md#t14): require every `scripts/check_*.py` to be imported by a test file.
- [T15](tests.md#t15): a test over every guard: each exemption table maps a location key to a non-empty reason and has a staleness check.
- [F1](docs-and-figures.md#f1): compare the imports and headings of each site guide with its `docs/` mirror, beside the i18n parity check.
- [F2](docs-and-figures.md#f2): refuse frontmatter and Astro components (`<ThemeImage>`, `<ScopeClaim>`) in `docs/**/*.md`, and a relative image path in a `<picture>`.
- [F10](docs-and-figures.md#f10): refuse an underscore in the module segment of a `reference/api` link in `docs/` and in the site content.
- [F11](docs-and-figures.md#f11): refuse a relative link or image path in `README.md`.
- [F25](docs-and-figures.md#f25): count the snippets inside each `<details>` block of `docs/` and the site that shows the code of a figure.
- [F35](docs-and-figures.md#f35): a run-time probe over the plot contract cases: a log x-axis labeled as a frequency carries the octave-center formatter.
- [F36](docs-and-figures.md#f36): an AST check over drawn strings that refuses a math span holding two plain words outside `\mathrm` or `\text`.
- [F38](docs-and-figures.md#f38): an AST check that refuses `fontweight='bold'` on `set_title` and `suptitle` in `scripts/figures`, `scripts/diagrams`, `_plot` and `_report`.
- [F41](docs-and-figures.md#f41): refuse a function definition in `scripts/generate_graphs.py` and `scripts/generate_diagrams.py`.
- [F50](docs-and-figures.md#f50): an AST check that refuses `rotation=` on tick labels in `src/phonometry/_report`.
- [F53](docs-and-figures.md#f53): refuse an animation embed without `loading="lazy"` or `preload="none"` and an explicit size.
- [F58](docs-and-figures.md#f58): refuse Unicode superscript powers of ten in `docs/ERRATA.md` and `docs/ERRATA.es.md`.
- [P6](prose.md#p6): extend the em-dash guard to commit messages and pull request bodies in CI.
- [P10](prose.md#p10): extend to the CHANGELOG, the curated API table and the guides the refusal `scripts/check_errata_evidence.py` makes of a citation that says how the page was read.
- [P11](prose.md#p11): diff `__all__` against the last release tag and require a CHANGELOG `[Unreleased]` mention for every new public name.
- [P12](prose.md#p12): require every top-level bullet under `[Unreleased]` to open with a bold title.
- [P14](prose.md#p14): refuse a conventional-commit prefix in pull request titles.
- [P15](prose.md#p15): scan pull request bodies and commit messages for the maintainer named in the third person.
- [P16](prose.md#p16): scan pull request titles, bodies and commit messages for references to a plan, a phase, a wave or a task.
- [P17](prose.md#p17): refuse a line break inside a paragraph of a pull request body (outside code, lists, tables and quotations).
