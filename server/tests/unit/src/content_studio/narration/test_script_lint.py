"""Linter del guion (spec 006, AC-1): una prueba por regla de formato-guion.md que se comprueba sin modelo."""

from __future__ import annotations

from content_studio.narration.script_lint import lint


def rules(text: str) -> list[int]:
    return [issue.rule for issue in lint(text)]


def test_ac1_a_clean_script_has_no_issues():
    assert lint('Hola, somos del equipo. ¿Ya viste el guion? ¡Empecemos! [pausa 1]') == []


def test_ac1_rule_1_flags_tags_and_recording_notation_but_not_grammar_marks():
    issue = lint('Hola [curiosa] mundo.')[0]

    assert (issue.rule, issue.col, issue.length) == (1, 6, 9)
    assert rules('Hola (pausa) mundo.') == [1]
    assert rules('Ya → ahora.') == [1]
    assert rules('Hola [pausa 1] [estilo: dramatica] [risa] mundo.') == []


def test_ac1_rule_2_flags_uppercase_emphasis_but_not_acronyms():
    issue = lint('Esto es DEMO.')[0]

    assert (issue.rule, issue.col, issue.length) == (2, 9, 4)
    assert rules('Mira el PDF.') == []


def test_ac1_rule_3_flags_a_paragraph_without_final_punctuation():
    issue = lint('Hola mundo')[0]

    assert (issue.rule, issue.col, issue.length) == (3, 10, 1)


def test_ac1_rule_6_flags_semicolons_and_colons_that_do_not_open_a_list():
    issue = lint('Hola; mundo.')[0]

    assert (issue.rule, issue.col, issue.length) == (6, 5, 1)
    assert rules('Nota: esto es así.') == [6]
    assert rules('Tu historial: consultas, antecedentes.') == []


def test_ac1_rule_10_needs_both_signs_of_questions_and_exclamations():
    issue = lint('Así es el guion?')[0]

    assert (issue.rule, issue.col) == (10, 16)
    assert rules('¿Listo.') == [10]
    assert rules('Listo!') == [10]
    assert rules('¿Listo? ¡Vamos!') == []


def test_ac1_rule_11_flags_sentences_over_25_words():
    assert rules(' '.join(['casa'] * 26) + '.') == [11]
    assert rules(' '.join(['casa'] * 25) + '.') == []


def test_ac1_rule_13_flags_digits_but_not_pause_marks():
    issue = lint('Son 24 horas.')[0]

    assert (issue.rule, issue.col, issue.length) == (13, 5, 2)
    assert rules('Hola [pausa 0.8] mundo.') == []


def test_ac1_rule_19_flags_the_forbidden_verb():
    issue = lint('Ya registras tu cuenta.')[0]

    assert (issue.rule, issue.col, issue.length) == (19, 4, 9)


def test_ac1_the_spec_example_gives_rules_6_2_and_13_in_order():
    issues = lint('Hola; esto es DEMO con 24 horas.')

    assert [(i.rule, i.line, i.col, i.length) for i in issues] == [(6, 1, 5, 1), (2, 1, 15, 4), (13, 1, 24, 2)]
