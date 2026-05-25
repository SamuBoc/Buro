Feature: Registro de asistencia a citas

  Background:
    Given existe una cita programada
    And la secretaria inicia sesion en el sistema

  Scenario: Registrar asistencia
    Given el beneficiario asiste a la cita
    When la secretaria registra la asistencia
    Then el sistema actualiza el estado de la cita a "Asistió"

  Scenario: Registrar inasistencia
    Given el beneficiario no se presenta a la cita
    When la secretaria registra la inasistencia
    Then el sistema actualiza el estado de la cita a "No asistió"
