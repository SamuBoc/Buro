Feature: Registro de causal de rechazo
  Background:
    Given existe un caso registrado en el sistema

  Scenario: Registro de rechazo
    Given la secretaria accede al caso
    When selecciona la opcion "Rechazar caso"
    And ingresa la causal de rechazo
    Then el sistema registra la causal
    And cambia el estado del caso a "Rechazado"

  Scenario: Intento de rechazo sin causal
    Given la secretaria intenta rechazar un caso
    When no ingresa una causal de rechazo
    Then el sistema bloquea el rechazo
    And solicita ingresar una causal valida
