Feature: Seleccion del tipo de atencion de cita
  Background:
    Given existe un beneficiario disponible para agendar cita
    And la secretaria accede al formulario de agendamiento de cita

  Scenario: Seleccion de modalidad de atencion
    When selecciona la modalidad telefonica
    And completa la fecha y la descripcion de la cita
    And registra la cita
    Then el sistema guarda la cita con la modalidad seleccionada

  Scenario: Modalidad no seleccionada
    When intenta agendar sin seleccionar modalidad
    And completa la fecha y la descripcion de la cita
    And registra la cita
    Then el sistema solicita seleccionar una modalidad valida
