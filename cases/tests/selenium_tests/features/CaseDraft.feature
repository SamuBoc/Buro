Feature: Guardado de borradores (HU-32)

  Background:
    Given el usuario esta completando un formulario en el sistema

  Scenario: Guardar borrador
    Given el usuario ha ingresado datos parciales
    When selecciona la opcion guardar borrador
    Then el sistema almacena la informacion ingresada

  Scenario: Recuperar borrador
    Given existe un borrador guardado
    When el usuario vuelve a abrir el formulario
    Then el sistema muestra los datos previamente guardados
