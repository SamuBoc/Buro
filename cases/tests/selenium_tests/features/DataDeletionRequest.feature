Feature: Solicitud de eliminacion de datos (HU-34)

  Background:
    Given el beneficiario tiene datos registrados en el sistema

  Scenario: Solicitar eliminacion de datos
    Given el usuario accede a su perfil
    When solicita la eliminacion de sus datos
    Then el sistema registra la solicitud

  Scenario: Registro de la solicitud
    Given se ha realizado una solicitud de eliminacion
    When el administrador revisa las solicitudes
    Then el sistema muestra la solicitud registrada
